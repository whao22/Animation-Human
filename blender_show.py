import bpy
import socket
import json
import time
import numpy as np

port=6666

def str2data(content):
    data=json.loads(content)
    return data['bone_euler'],data['location'],float(data['scale']),data['bone_names']

def stop_playback(scene):
    print(f"{scene.frame_current} / {scene.frame_end}")
    if scene.frame_current == scene.frame_end:
        bpy.ops.screen.animation_cancel(restore_frame=False)

class MocapBlenderOperator(bpy.types.Operator):
    bl_idname="wm.mocap_blender"
    bl_label="Mocap Blender"

    _timer=None
    stop:bpy.props.BoolProperty()
     
    def execute(self,context):
        bpy.app.handlers.frame_change_pre.append(stop_playback)
        wm=context.window_manager
        self._timer=wm.event_timer_add(0.02, window=context.window)
        wm.modal_handler_add(self)
        # 初始化骨骼场景
        self.init_skeleton()
        # 初始化socket
        self.init_socket()
        return {'RUNNING_MODAL'}

    def init_socket(self):
        # 创建socket
        self.server=socket.socket()
        self.server.bind(('127.0.0.1',port))
        self.server.listen(5)
        # 等待客户端连接
        print("正在连接动作捕捉进程...")
        self.con, self.addr=self.server.accept()
        print(f"已连接动作捕捉进程，套接字{self.con}{self.addr}.")
        
    def init_skeleton_bak(self):
        # skeleton_objs = list(filter(lambda o: o.type == 'ARMATURE', bpy.data.objects))
        # assert len(skeleton_objs) == 1, "There should be only one skeleton object"
        skeleton_objs = list(filter(lambda o: o.type == 'ARMATURE', bpy.data.objects))
        self.skeleton0 = skeleton_objs[0]
        self.skeleton1 = skeleton_objs[1]
        self.skeleton0.location = (0, 0, 0)
        self.skeleton1.location = (0, 0, 0)
        time.sleep(0.005)

    def init_skeleton(self):
        # skeleton_objs = list(filter(lambda o: o.type == 'ARMATURE', bpy.data.objects))
        # assert len(skeleton_objs) == 1, "There should be only one skeleton object"
        skeleton_objs = list(filter(lambda o: o.type == 'ARMATURE', bpy.data.objects))
        self.skeleton0 = skeleton_objs[0]
        self.skeleton0.location = (0, 0, 0)
        self.nframe=0
        time.sleep(0.005)

    def cancel(self, context):
        wm=context.window_manager
        wm.event_timer_remove(self._timer)
        self.con.close()
        self.server.close()

    def modal_bak(self, context, event):
        if (event.type in {'ESC','SPACE'}) or self.stop==True:
            self.cancel(context)
            return {'CANCELLED'}
        
        if event.type =="TIMER":
            recv_data=self.con.recv(1024*5,socket.MSG_WAITALL)
            if len(recv_data.strip())==0:
                print("接收到的动捕进程的数据为空")
            elif recv_data.decode()=='exit':
                    self.stop=True
            else:
                # 接收数据
                content=recv_data.decode().strip()
                print(f"接收到的数据为{content}")
                bone_euler,location,scale,bone_names=str2data(content)
                print("aaaaa ",len(bone_euler))
                # 选中骨架并变形
                for i,b in enumerate(bone_names):
                    bone0=self.skeleton0.pose.bones[b]
                    bone1=self.skeleton1.pose.bones[b]
                    bone0.rotation_mode="ZYX" ## ZYX is the best
                    bone1.rotation_mode="ZYX"
                    # bone0.rotation_mode="AXIS_ANGLE"
                    # bone1.rotation_mode="AXIS_ANGLE"
                    bone0.rotation_euler=bone_euler[i]  
                    bone1.rotation_euler=bone_euler[i]
                    # bone0.rotation_axis_angle=bone_euler[int(b)]
                    # bone1.rotation_axis_angle=bone_euler[int(b)]
                    bone0.keyframe_insert(data_path="rotation_euler", index=-1)
                    bone1.keyframe_insert(data_path="rotation_euler", index=-1)
                    
                x,y,z=location
                self.skeleton0.location=y, -z, x
                self.skeleton1.location=y, -z, x
                print(f"x: {x} ,y: {y} ,z: {z} ")
                self.skeleton0.keyframe_insert(data_path="location", index=-1)
                self.skeleton1.keyframe_insert(data_path="location", index=-1)

        return {'PASS_THROUGH'}
    
    def modal(self, context, event):
        if (event.type in {'ESC','SPACE'}) or self.stop==True:
            self.cancel(context)
            return {'CANCELLED'}
        
        if event.type =="TIMER":
            recv_data=self.con.recv(1024*5,socket.MSG_WAITALL)
            if len(recv_data.strip())==0:
                print("接收到的动捕进程的数据为空")
            elif recv_data.decode()=='exit':
                    self.stop=True
            else:
                # 接收数据
                content=recv_data.decode().strip()
                # print(f"接收到的数据为{content}")
                bone_euler,location,scale,bone_names=str2data(content)
                # print(bone_euler)
                # print("aaaaa ",len(bone_euler))

                # 选中骨架并变形
                for i,b in enumerate(bone_names):
                    bone0=self.skeleton0.pose.bones[b]

                    if b in ['R_Collar', 'R_Shoulder','R_Elbow','R_Wrist','L_Collar', 'L_Shoulder','L_Elbow','L_Wrist']:
                        bone0.rotation_mode="XYZ"
                    # elif b in ['L_Ankle','L_Foot','R_Ankle','R_Foot']:
                    #     bone0.rotation_mode="ZXY"
                    else:
                        bone0.rotation_mode="YXZ"
                    # bone0.rotation_mode="YXZ" ## ZYX is the best

                    bone0.rotation_euler=bone_euler[i]  
                    # bone0.keyframe_insert(data_path="rotation_euler", index=-1)
                    # if b=="L_Shoulder":
                    #     bone0.rotation_euler=(bone_euler[i][0],bone_euler[i][1],bone_euler[i][2]-1.270796327)
                    # elif b=="R_Shoulder":
                    #     bone0.rotation_euler=(bone_euler[i][0],bone_euler[i][1],bone_euler[i][2]+1.270796327)
                    # elif b=="L_Elbow":
                    #     bone0.rotation_euler=(bone_euler[i][0],bone_euler[i][1]-1.270796327,bone_euler[i][2])
                    # elif b=="R_Elbow":
                    #     bone0.rotation_euler=(bone_euler[i][0],bone_euler[i][1]-1.270796327,bone_euler[i][2])
                    # else:
                    #     bone0.rotation_euler=bone_euler[i]


                x,y,z=location
                self.skeleton0.location=x/100,-z/100,y/100
                print(f"x: {x} ,y: {y} ,z: {z} ")
                self.skeleton0.keyframe_insert(data_path="location", index=-1)
                self.nframe+=1
                print(self.nframe)
                

        return {'PASS_THROUGH'}

class MocapPanel(bpy.types.WorkSpaceTool):
    """Creates a Panel in the Object properties window"""
    bl_label = "MocapPanel"
    bl_space_type = 'VIEW_3D'
    bl_context_mode='OBJECT'
    bl_idname = "ui_plus.mocap"
    bl_icon = "ops.generic.select_circle"


    def draw_settings(context, layout, tool):
        row = layout.row()
        op = row.operator("wm.mocap_blender", text="Mocap", icon="OUTLINER_OB_CAMERA")
        #props = tool.operator_properties("wm.opencv_operator")
        #layout.prop(props, "stop", text="Stop Capture")
        #layout.prop(tool.op, "stop", text="Stop Capture")

def register():
    bpy.utils.register_class(MocapBlenderOperator)
    bpy.utils.register_tool(MocapPanel, separator=True, group=True)

def unregister():
    bpy.utils.unregister_class(MocapBlenderOperator)
    bpy.utils.unregister_tool(MocapPanel)


if __name__ == "__main__":
    register()


