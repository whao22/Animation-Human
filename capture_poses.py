import os
import shutil
import pandas as pd
import argparse
import threading
import socket
# from pynput import keyboard
import time
import numpy as np
import torch
import json
from tqdm import tqdm
import pdb

from scipy.spatial.transform import Rotation
from bvh import Bvh

# pt 15 原地挥动双手

# dict1={"bone_names": ['00',
#                       '01',
#                       '02',
#                       '03',
#                       '04',
#                       '05',
#                       '06',
#                       '07',
#                       '08',
#                       '09',
#                       '10',
#                       '11',
#                       '12',
#                       '13',
#                       '14',
#                       '15',
#                       '16',
#                       '17',
#                       '18',
#                       '19',
#                       '20',
#                       '21',
#                       '22',
#                       '23']}

# dict1={"bone_names": ['Pelvis',
#                       'L_Hip',
#                       'R_Hip',
#                       'Spine1',
#                       'L_Knee',
#                       'R_Knee',
#                       'Spine2',
#                       'L_Ankle',
#                       'R_Ankle',
#                       'Spine3',
#                       'L_Foot',
#                       'R_Foot',
#                       'Neck',
#                       'L_Collar',
#                       'R_Collar',
#                       'Head',
#                       'L_Shoulder',
#                       'R_Shoulder',
#                       'L_Elbow',
#                       'R_Elbow',
#                       'L_Wrist',
#                       'R_Wrist',
#                       'L_Hand',
#                       'R_Hand']}

dict1 = {"bone_names": ['pelvis',
                        'left_hip',
                        'right_hip',
                        'spine1',
                        'left_knee',
                        'right_knee',
                        'spine2',
                        'left_ankle',
                        'right_ankle',
                        'spine3',
                        'left_foot',
                        'right_foot',
                        'neck',
                        'left_collar',
                        'right_collar',
                        'head',
                        'left_shoulder',
                        'right_shoulder',
                        'left_elbow',
                        'right_elbow',
                        'left_wrist',
                        'right_wrist',
                        'left_middle1',
                        'right_middle2']}


def data2str(bone_euler, location, scale, bone_names):
    data = {}
    data['bone_euler'] = bone_euler.detach().numpy().tolist()
    data['location'] = location.detach().numpy().tolist()
    data['scale'] = scale
    data['bone_names'] = bone_names
    return json.dumps(data)


def rotation_matrix_to_euler_angle(r: torch.Tensor, seq='XYZ'):
    r"""
    Turn rotation matrices into euler angles. (torch, batch)

    :param r: Rotation matrix tensor that can reshape to [batch_size, 3, 3].
    :param seq: 3 characters belonging to the set {'X', 'Y', 'Z'} for intrinsic
                rotations, or {'x', 'y', 'z'} for extrinsic rotations (radians).
                See scipy for details.
    :return: Euler angle tensor of shape [batch_size, 3].
    """
    rot = Rotation.from_matrix(r.clone().detach().cpu().view(-1, 3, 3).numpy())
    ret = torch.from_numpy(rot.as_euler(seq)).float().to(r.device)
    return ret


def rotation_matrix_to_axis_angle(r: torch.Tensor):
    r"""
    Turn rotation matrices into axis-angles. (torch, batch)

    :param r: Rotation matrix tensor that can reshape to [batch_size, 3, 3].
    :return: Axis-angle tensor of shape [batch_size, 3].
    """
    import cv2
    result = [cv2.Rodrigues(_)[0]
              for _ in r.clone().detach().cpu().view(-1, 3, 3).numpy()]
    result = torch.from_numpy(
        np.stack(result)).float().squeeze(-1).to(r.device)
    return result


def transaction(args):
    # create a socket
    # TODO 判断端口是否被占用
    p, t = torch.load("/home/wanghao/WORKSPACE/PIP/0.pt")
    # data=torch.load("data/test.pt")
    # i=1
    # p,t=data['pose'][i],data['tran'][i]

    client = socket.socket()
    client.connect(('127.0.0.1', args.port))

    while True:
        for bone_matrix, location in zip(p, t):
            bone_euler = rotation_matrix_to_euler_angle(
                bone_matrix)  # /np.pi*180
            print(bone_euler.shape)
            # bone_euler[:,-1]=-bone_euler[:,-1]
            send_data = data2str(bone_euler, location, 1, dict1['bone_names'])
            # bone_matrix=bone_matrix.reshape(24,3)
            # angle=torch.sqrt(torch.sum(bone_matrix**2,dim=1)).reshape([24,1])
            # axis=bone_matrix/angle
            # send_data=data2str(torch.cat((angle/np.pi*180,axis),dim=1), location, 1, dict1['bone_names'])
            print(send_data.encode())
            send_data = send_data+' '*(1024*5-len(send_data))
            client.send(send_data.encode())
            time.sleep(0.033)


class BVH_paser():
    def __init__(self, bvh_file_path) -> None:
        self.bvh_file_path = bvh_file_path
        with open(bvh_file_path) as f:
            self.mocap = Bvh(f.read())

    def get_3D_motion(self):
        motion_lst = []
        for pose in self.mocap.frames:
            pose_lst = []
            for item in pose:
                pose_lst.append(float(item))
            motion_lst.append(pose_lst)
        return motion_lst

    def get_3D_joint(self):
        # 关节偏移
        # 获取关节名称
        joints = self.mocap.get_joints_names()
        print(joints)
        # 获取关节偏移
        joints_offsets = []
        for joint in joints:
            offset = self.mocap.joint_offset(joint)
            joints_offsets.append(offset)
        print(joints_offsets)

        # 关节三维坐标
        def add_tuple(t1, t2):
            t = []
            for i in range(len(t2)):
                t.append(t1[i]+t2[i])
            return t

        points = [joints_offsets[0]]
        for i in range(1, len(joints_offsets)):
            if i in [1, 15, 19]:
                p = add_tuple(points[0], joints_offsets[i])
            elif i in [5, 7, 11]:
                p = add_tuple(points[4], joints_offsets[i])
            else:
                p = add_tuple(points[i-1], joints_offsets[i])
            points.append(p)
        return points


def deformation(rotations):
    """_summary_

    Args:
        rotations (ndarray): shape (N_frames, N_joints, 3), where the N_joints is 23.

    Returns:
        _type_: _description_
    """
    N_frames, N_joints, _ = rotations.shape

    # poses matrix
    bone_matrix = Rotation.from_euler(seq="YXZ", angles=rotations.reshape(-1, 3), degrees=True).as_matrix().reshape(N_frames, N_joints, 3, 3) # (N_frames, N_joints, 3, 3)
    
    bone_quat = Rotation.from_matrix(bone_matrix.reshape(-1, 3, 3)).as_quat(True).reshape(N_frames, N_joints, 4) # (x, y, z, w)
    bone_quat = bone_quat[..., [-1, 0, 1, 2]] # (w, x, y, z)

    return bone_quat


def transaction2(args):
    # bone order of XSENS for SMPLX
    dict = {"bone_names": ['pelvis',
                           'spine1',
                           'spine2',
                           'spine2',
                           'spine3',
                           'neck',
                           'head',
                           'right_collar',
                           'right_shoulder',
                           'right_elbow',
                           'right_wrist',
                           'left_collar',
                           'left_shoulder',
                           'left_elbow',
                           'left_wrist',
                           'right_hip',
                           'right_knee',
                           'right_ankle',
                           'right_foot',
                           'left_hip',
                           'left_knee',
                           'left_ankle',
                           'left_foot']}
    # 读取bvh文件
    # bvh_file_path = "/home/wanghao/桌面/南岭项目-角色模型/XSENS数据/9.8测试数据-wh-1.8/Xsens DATA/NPose/New Session-001.bvh"  # 替换为您的BVH文件路径
    bvh_file_path = "data/motion_data/TPose.bvh"  # 替换为您的BVH文件路径

    bvh = BVH_paser(bvh_file_path)
    motion = bvh.get_3D_motion()
    motion = np.array(motion)
    translations = motion[:, :3]  # N*3
    rotations = motion[:, 3:].reshape(motion.shape[0], -1, 3)  # YXZ, N*23*3, radias angle
    quaternions = deformation(rotations) # (N_frames, N_joints, 4)

    def data2str2(bone_euler, location, scale, bone_names):
        data = {}
        data['poses'] = bone_euler.tolist()
        data['locations'] = location.tolist()
        data['scale'] = scale
        data['bone_names'] = bone_names
        return json.dumps(data)

    client = socket.socket()
    client.connect(('127.0.0.1', args.port))

    while True:
        for quat, location in zip(quaternions, translations):
            send_data = data2str2(quat, location, 1, dict['bone_names'])

            print(send_data.encode())
            send_data = send_data+' '*(1024*5-len(send_data))
            client.send(send_data.encode())
            # time.sleep(0.033)


def transaction3(args):
    # 读取xls文件
    def parse_xls(filepath, sheet1, sheet2):
        corresponding = [1, 19, 15, 2, 20, 16, 3, 21, 17, 4,
                         22, 18, 5, 11, 7, 6, 12, 8, 13, 9, 14, 10, -1, -1]

        # corresponding=[1,19,15,2,20,16,3,21,17,4,22,18,5,11,7,6,12,8,13,9,14,10,-1,-1]
        # corresponding=[1,20,16,3,21,17,4,22,18,5,23,19,6,-1,-1,7,12,8,13,9,14,10,15,11]
        sheet = pd.read_excel(filepath, sheet_name=None)
        bone_angles = sheet[sheet1].values[:, 1:]
        translation = sheet[sheet2].values[:, 1:]

        # 关节运动树，模型关节角度
        nframe, ncol = bone_angles.shape
        bone_angles_smpl = np.zeros(shape=(nframe, 24*3))
        for i in range(24):
            j = corresponding[i]-1
            if j >= 0:
                bone_angles_smpl[:, i*3:i*3+3] = bone_angles[:, j*3:j*3+3]

        # 模型平移
        translation_smpl = translation[:, :3]

        # reshape
        bone_angles_smpl = bone_angles_smpl.reshape(nframe, -1, 3)
        tmp = np.zeros_like(bone_angles_smpl)
        tmp[..., 0] = -bone_angles_smpl[..., 2]
        tmp[..., 1] = bone_angles_smpl[..., 1]
        tmp[..., 2] = bone_angles_smpl[..., 0]
        bone_angles_smpl = tmp

        return bone_angles_smpl/180*3.141592654, translation_smpl

    def data2str2(bone_euler, location, scale, bone_names):
        data = {}
        data['bone_euler'] = bone_euler.tolist()
        data['location'] = location.tolist()
        data['scale'] = scale
        data['bone_names'] = bone_names
        return json.dumps(data)

    # create a socket
    # TODO 判断端口是否被占用
    filepath = "/home/wanghao/桌面/南岭项目-角色模型/XSENS数据/9.8测试数据-wh-1.8/Xsens DATA/TPose/New Session-002.xlsx"
    sheet1 = 'Joint Angles XZY'
    sheet2 = 'Center of Mass'
    p, t = parse_xls(filepath, sheet1, sheet2)

    client = socket.socket()
    client.connect(('127.0.0.1', args.port))

    while True:
        for bone_euler, location in zip(p, t):
            send_data = data2str2(bone_euler, location, 1, dict1['bone_names'])

            print(send_data.encode())
            send_data = send_data+' '*(1024*5-len(send_data))
            client.send(send_data.encode())
            time.sleep(0.033)


def configparser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=6666, help='')
    args = parser.parse_args()
    return args


def main():
    args = configparser()

    # 事务进程
    t_trans = threading.Thread(target=transaction2, args=(args,))
    t_trans.start()


if __name__ == '__main__':
    main()
