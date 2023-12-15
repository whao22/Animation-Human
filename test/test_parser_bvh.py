from scipy.spatial.transform import Rotation
from bvh import Bvh
import numpy as np

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
    # rest pose bone matrix, got from blender
    bone_rest_matrix = np.zeros([len(rotations[0]), 3, 3])
    bone_rest_matrix[0] = pelvis_rest = np.array(
        [[1, 0, 0], [0, 0.9939, 0.1104], [0, -0.1104, 0.9939]])
    bone_rest_matrix[1] = chest_rest = np.array(
        [[1, 0, 0], [0, 1, 0], [0, 0, 1]])
    bone_rest_matrix[2] = chest2_rest = np.array(
        [[1, 0, 0], [0, 1, 0], [0, 0, 1]])
    bone_rest_matrix[3] = chest3_rest = np.array(
        [[1, 0, 0], [0, 1, 0], [0, 0, 1]])
    bone_rest_matrix[4] = chest4_rest = np.array(
        [[1, 0, 0], [0, 1, 0], [0, 0, 1]])
    bone_rest_matrix[5] = neck_rest = np.array(
        [[1, 0, 0], [0, 1, 0], [0, 0, 1]])
    bone_rest_matrix[6] = head_rest = np.array(
        [[1, 0, 0], [0, 1, 0], [0, 0, 1]])

    bone_rest_matrix[7] = rcollar_rest = np.array(
        [[0, -1, 0], [1, 0, 0], [0, 0, 1]])
    bone_rest_matrix[8] = rshoulder_rest = np.array(
        [[0, -1, 0], [1, 0, 0], [0, 0, 1]])
    bone_rest_matrix[9] = relbow_rest = np.array(
        [[0, -1, 0], [1, 0, 0], [0, 0, 1]])
    bone_rest_matrix[10] = rwrist_rest = np.array(
        [[0, -1, 0], [1, 0, 0], [0, 0, 1]])

    bone_rest_matrix[11] = lcollar_rest = np.array(
        [[0, 1, 0], [-1, 0, 0], [0, 0, 1]])
    bone_rest_matrix[12] = lshouder_rest = np.array(
        [[0, 1, 0], [-1, 0, 0], [0, 0, 1]])
    bone_rest_matrix[13] = lelbow_rest = np.array(
        [[0, 1, 0], [-1, 0, 0], [0, 0, 1]])
    bone_rest_matrix[14] = lwrist_rest = np.array(
        [[0, 1, 0], [-1, 0, 0], [0, 0, 1]])

    bone_rest_matrix[15] = rhip_rest = np.array(
        [[-1, 0, 0], [0, -1, 0], [0, 0, 1]])
    bone_rest_matrix[16] = rknee_rest = np.array(
        [[-1, 0, 0], [0, -1, 0], [0, 0, 1]])
    bone_rest_matrix[17] = rankle_rest = np.array(
        [[-1, 0, 0], [0, -1, 0], [0, 0, 1]])
    bone_rest_matrix[18] = rtoe_rest = np.array(
        [[-1, 0, 0], [0, -1, 0], [0, 0, 1]])
    bone_rest_matrix[19] = lhip_rest = np.array(
        [[-1, 0, 0], [0, -1, 0], [0, 0, 1]])
    bone_rest_matrix[20] = lknee_rest = np.array(
        [[-1, 0, 0], [0, -1, 0], [0, 0, 1]])
    bone_rest_matrix[21] = lankle_rest = np.array(
        [[-1, 0, 0], [0, -1, 0], [0, 0, 1]])
    bone_rest_matrix[22] = ltoe_rest = np.array(
        [[-1, 0, 0], [0, -1, 0], [0, 0, 1]])

    # poses matrix, borrowed from blender bvh import addon
    for j, rotation in enumerate(rotations):
        for i in range(len(rotation)):
            bone_matrix = Rotation.from_euler(
                seq="YXZ", angles=rotation[i], degrees=True).as_matrix()
            bone_matrix = np.linalg.inv(
                bone_rest_matrix[i]) @ bone_matrix @ bone_rest_matrix[i]
            tmp = Rotation.from_matrix(
                bone_matrix).as_euler("ZXY", degrees=False)
            
            if i >= 0 and i <= 6:  # spine
                rotations[j, i, 0] = tmp[1]
                rotations[j, i, 1] = tmp[2]
                rotations[j, i, 2] = tmp[0]
            if i >= 7 and i <= 10:  # r arms
                rotations[j, i, 0] = -tmp[2]
                rotations[j, i, 1] = tmp[1]
                rotations[j, i, 2] = tmp[0]
            if i >= 11 and i <= 14:  # l arms
                rotations[j, i, 0] = tmp[2]
                rotations[j, i, 1] = -tmp[1]
                rotations[j, i, 2] = tmp[0]
            if i >= 15 and i <= 22:  # r&l legs
                rotations[j, i, 0] = -tmp[1]
                rotations[j, i, 1] = -tmp[2]
                rotations[j, i, 2] = tmp[0]
    return rotations

# bvh_file_path = "/home/wanghao/桌面/南岭项目-角色模型/XSENS数据/9.8测试数据-wh-1.8/Xsens DATA/TPose/New Session-002.bvh"  # 替换为您的BVH文件路径

# bvh = BVH_paser(bvh_file_path)
# motion = bvh.get_3D_motion()
# motion = np.array(motion)
# translations = motion[:, :3]  # N*3
# rotations = motion[:, 3:].reshape(motion.shape[0], -1, 3)  # YXZ, N*23*3, radias angle
# # rotations = deformation(rotations)
# print()

bone_rest_matrix = np.zeros([23, 3, 3])
bone_rest_matrix[0] = np.array([[1, 0, 0], [0, 0.9939, 0.1104], [0, -0.1104, 0.9939]])
bone_rest_matrix[1:7] = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
bone_rest_matrix[7:11] = np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1]])
bone_rest_matrix[11:15] = np.array([[0, 1, 0], [-1, 0, 0], [0, 0, 1]])
bone_rest_matrix[15:23] = np.array([[-1, 0, 0], [0, -1, 0], [0, 0, 1]])

bone_rest_matrix = np.tile(bone_rest_matrix[None, ...], (10000, 1, 1, 1))
print(bone_rest_matrix)