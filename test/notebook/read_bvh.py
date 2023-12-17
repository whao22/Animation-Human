from bvh import Bvh
import matplotlib.pyplot as plt
import numpy as np


class BVH_paser():
    def __init__(self,bvh_file_path) -> None:
        self.bvh_file_path=bvh_file_path
        with open(bvh_file_path) as f:
            self.mocap = Bvh(f.read())

    def get_3D_motion(self):
        motion_lst=[]
        for pose in self.mocap.frames:
            pose_lst=[]
            for item in pose:
                pose_lst.append(float(item))
            motion_lst.append(pose_lst)
        return motion_lst

    def get_3D_joint(self):
        # 关节偏移
        ## 获取关节名称
        joints=self.mocap.get_joints_names()
        print(joints)
        ## 获取关节偏移
        joints_offsets=[]
        for joint in joints:
            offset=self.mocap.joint_offset(joint)
            joints_offsets.append(offset)
        print(joints_offsets)

        # 关节三维坐标
        def add_tuple(t1,t2):
            t=[]
            for i in range(len(t2)):
                t.append(t1[i]+t2[i])
            return t

        points=[joints_offsets[0]]
        for i in range(1,len(joints_offsets)):
            if i in [1,15,19]:
                p=add_tuple(points[0],joints_offsets[i])
            elif i in [5,7,11]:
                p=add_tuple(points[4],joints_offsets[i])
            else:
                p=add_tuple(points[i-1],joints_offsets[i])
            points.append(p)
        return points

def draw_joint(points:list):
    """
    points: N*3 list
    """
    # 分离坐标
    x = [point[0] for point in points]
    y = [point[1] for point in points]
    z = [point[2] for point in points]

    # 创建3D散点图
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    # 绘制散点
    ax.scatter(x, y, z, c='r', marker='o')
    for i,point in enumerate(points):
        ax.text(*point, f'{i}', fontsize=12, color='red')

    # 设置坐标轴标签
    ax.set_xlabel('X轴')
    ax.set_ylabel('Y轴')
    ax.set_zlabel('Z轴')
    # 设置坐标轴范围
    ax.set_xlim([-100, 100])
    ax.set_ylim([-100, 100])
    ax.set_zlim([-100, 100])

    # 显示图形
    plt.show()


if __name__=="__main__":
    # 读取bvh文件
    bvh_file_path = "/home/wanghao/桌面/南岭项目-角色模型/XSENS数据/9.8测试数据-wh-1.8/Xsens DATA/NPose/New Session-001.bvh"  # 替换为您的BVH文件路径

    bvh=BVH_paser(bvh_file_path)
    points=bvh.get_3D_joint()
    print(points)
    draw_joint(points)

    # motion=bvh.get_3D_motion()
    # motion=np.array(motion)
    # translations=motion[:,:3]
    # rotations=motion[:,3:].reshape(motion.shape[0],-1,3) # YXZ
    # print(translations.shape)
    # print(rotations.shape)
    
    