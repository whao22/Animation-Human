import json
from mathutils import Vector

from scipy.spatial.transform import Rotation

def rotation_mat(axis: str='x', angle: int=0):
    """Rotation matrix for smplicity, e.g. Rotate 90 degrees clockwise around the x-axis. = rotation_mat('x', 90)

    Args:
        axis (str, optional): _description_. Defaults to 'x'.
        angle (int, optional): _description_. Defaults to 0.

    Returns:
        matrix (ndarray): _description_. shape (3, 3).
    """
    matrix = Rotation.from_euler(axis, angle, degrees=True).as_matrix()
    return matrix
    
def parse_recv_data(recv_data):
    parsed_data = None
    if len(recv_data.strip()) == 0:
        print("The received data is empty!")
    else:
        content = recv_data.decode().strip()
        parsed_data = json.loads(content)
    return parsed_data

def motion_pose_to_smplx_pose(pose):
    """_summary_

    Args:
        pose (ndarray): motion pose from xsens, shape (23, 3)
    """
    corresponding_bone_idx = [0, 19, 15, 1, 20, 16, 3, 21, 17, 4, 22, 18, 5, 11, 7, 6, 12, 8, 13, 9, 14, 10, -1, -1]
    ret_pose = pose[corresponding_bone_idx]
    
    return ret_pose

def deform_mesh_obj_manual(selected_obj, cur_vertices):
    # 检查选择的对象是否是网格对象
    mesh = selected_obj.data

    # 获取网格中的顶点数量
    num_vertices = len(mesh.vertices)
    
    # 对每个顶点进行随机移动
    for i in range(num_vertices):
        new_location = Vector(cur_vertices[i])
        selected_obj.data.vertices[i].co = selected_obj.matrix_world.inverted() @ new_location
        
    # 更新网格
    mesh.update()