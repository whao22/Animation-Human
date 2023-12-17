import bpy
import socket
import json
import time
import pickle
from mathutils import Vector

import sys
sys.path.append(".")
import numpy as np
from scipy.spatial.transform import Rotation
import torch
import pdb

from libs.smplx.body_models import SMPLXLayer
from libs.utils import parse_recv_data, motion_pose_to_smplx_pose, rotation_mat, deform_mesh_obj_manual

port = 6666

def stop_playback(scene):
    print(f"{scene.frame_current} / {scene.frame_end}")
    if scene.frame_current == scene.frame_end:
        bpy.ops.screen.animation_cancel(restore_frame=False)

    
class MocapBlenderOperator(bpy.types.Operator):
    bl_idname = "wm.mocap_blender"
    bl_label = "Mocap Blender"

    _timer = None
    stop: bpy.props.BoolProperty()

    def execute(self, context):
        # load smplx params
        B=1
        fxy_wang= '/home/wanghao/桌面/南岭项目-角色模型/FXY/wang-smplx-betas.pkl'
        with open('data/mesh_data/wanghao.pkl', 'rb') as f:
            data = pickle.load(f)
        self.betas = torch.from_numpy(data['betas']).float().reshape(B, -1)
        self.expression = torch.from_numpy(data['expression']).float().reshape(B, -1)
        ## pose
        self.left_hand_pose = torch.from_numpy(Rotation.from_rotvec(data['left_hand_pose'].reshape(-1, 3)).as_matrix()).float().reshape(B, -1, 3, 3)
        self.right_hand_pose = torch.from_numpy(Rotation.from_rotvec(data['right_hand_pose'].reshape(-1, 3)).as_matrix()).float().reshape(B, -1, 3, 3)
        self.jaw_pose = torch.from_numpy(Rotation.from_rotvec(data['jaw_pose'].reshape(-1, 3)).as_matrix()).float().reshape(B, 3, 3)
        self.leye_pose = torch.from_numpy(Rotation.from_rotvec(data['leye_pose'].reshape(-1, 3)).as_matrix()).float().reshape(B, 3, 3)
        self.reye_pose = torch.from_numpy(Rotation.from_rotvec(data['reye_pose'].reshape(-1, 3)).as_matrix()).float().reshape(B, 3, 3)
        print("bone_euler", self.left_hand_pose.shape)
        
        # load smplx model
        self.smplxlayer = SMPLXLayer(model_path='data/smplx', num_betas=300, num_expression_coeffs=100)
        
        # blender addon
        # bpy.app.handlers.frame_change_pre.append(stop_playback)
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.02, window=context.window)
        wm.modal_handler_add(self)
        # 初始化骨骼场景
        self.init_armatures()
        # 初始化socket
        self.init_socket()
        self.nframe = 0
        return {'RUNNING_MODAL'}

    def init_socket(self):
        # 创建socket
        self.server = socket.socket()
        self.server.bind(('127.0.0.1', port))
        self.server.listen(5)
        # 等待客户端连接
        print("正在连接动作捕捉进程...")
        self.con, self.addr = self.server.accept()
        print(f"已连接动作捕捉进程，套接字{self.con}{self.addr}.")

    def init_armatures(self):
        objs = bpy.data.objects
        armatures = [obj for obj in objs if obj.type=='ARMATURE']
        meshes = [obj for obj in objs if obj.type=='MESH']
        self.skeleton_armature = None
        self.skin_armature = None
        self.skin_model = None
        for armature in armatures:
            if 'bone' in armature.name:
                self.skeleton_armature = armature
            if 'skin' in armature.name:
                self.skin_armature = armature
        for mesh in meshes:
            if '000' in mesh.name:
                self.skin_model = mesh
        
        self.skeleton_armature.location = (0, 0, 0)
        self.skin_armature.location = (0, 0,0 )
        self.skin_model.location = (0, 0, 0)
        print("skeleton_armature", self.skeleton_armature)
        print("skin_model", self.skin_model)
        
    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
        self.con.close()
        self.server.close()

    def modal(self, context, event):
        if (event.type in {'ESC', 'SPACE'}) or self.stop == True:
            self.cancel(context)
            return {'CANCELLED'}

        if event.type == "TIMER":
            recv_data = self.con.recv(1024*5, socket.MSG_WAITALL)
            parsed_data = parse_recv_data(recv_data)
            bone_quats = parsed_data['poses']
            locations = parsed_data['locations']
            scale = parsed_data['scale']
            bone_names = parsed_data['bone_names']
            
            
            # skeletal model deformation
            for i, b in enumerate(bone_names):
                bone0 = self.skeleton_armature.pose.bones[b]
                bone1 = self.skin_armature.pose.bones[b]
        
                bone0.rotation_mode = "QUATERNION"
                bone1.rotation_mode = "QUATERNION"
                
                bone0.rotation_quaternion = bone_quats[i]
                bone1.rotation_quaternion = bone_quats[i]
                
            # skin model deformation
            bone_quats = motion_pose_to_smplx_pose(np.array(bone_quats))
            bone_quats = bone_quats[..., [1, 2, 3, 0]] # (x, y, z, w)
            body_poses = Rotation.from_quat(bone_quats).as_matrix()
            
            pose_smplx = torch.from_numpy(body_poses[1:22]).float().reshape(1, -1, 3, 3)
            transl = torch.zeros(1, 3, dtype=torch.float32)
            global_orient = torch.from_numpy(body_poses[0]).float().reshape(1, 3, 3)
            
            output = self.smplxlayer(self.betas, 
                    global_orient, 
                    pose_smplx,
                    self.left_hand_pose, 
                    self.right_hand_pose, 
                    transl,
                    self.expression,
                    self.jaw_pose, 
                    self.leye_pose, 
                    self.reye_pose,
                    return_verts=True,
                    return_full_pose=True)
            
            cur_vertices = output.vertices.reshape(-1, 3).detach().cpu().numpy() # (N_points, 3)
            # rotation 90
            R_x_p90 = rotation_mat('xyz', (90, 0, 0)) # (3, 3)
            cur_vertices = (R_x_p90 @ cur_vertices[..., None]).squeeze()
            # translation 
            cur_vertices = cur_vertices + np.array([[locations[0],-locations[2],locations[1]]]) / 100
            
            deform_mesh_obj_manual(self.skin_model, cur_vertices)
            
            
            x, y, z = locations
            self.skeleton_armature.location = x/100, -z/100, y/100
            self.skin_armature.location = x/100, -z/100, y/100
            self.skeleton_armature.keyframe_insert(data_path="location", index=-1)
            self.skin_armature.keyframe_insert(data_path="location", index=-1)
            self.skin_model.keyframe_insert(data_path="location", index=-1)
            self.nframe += 1
            print(self.nframe)

        return {'PASS_THROUGH'}


class MocapPanel(bpy.types.WorkSpaceTool):
    """Creates a Panel in the Object properties window"""
    bl_label = "MocapPanel"
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'
    bl_idname = "ui_plus.mocap"
    bl_icon = "ops.generic.select_circle"

    def draw_settings(context, layout, tool):
        row = layout.row()
        op = row.operator("wm.mocap_blender", text="Mocap",
                          icon="OUTLINER_OB_CAMERA")
        # props = tool.operator_properties("wm.opencv_operator")
        # layout.prop(props, "stop", text="Stop Capture")
        # layout.prop(tool.op, "stop", text="Stop Capture")


def register():
    bpy.utils.register_class(MocapBlenderOperator)
    bpy.utils.register_tool(MocapPanel, separator=True, group=True)


def unregister():
    bpy.utils.unregister_class(MocapBlenderOperator)
    bpy.utils.unregister_tool(MocapPanel)


if __name__ == "__main__":
    register()
