# The script used for painting weight for rigged character, where 
# armature and character has been added in .blend. See the picture
# in [.assets/paint-weight.png].

import pathlib
import bpy
import math

def import_batch_obj():
    """ import objs 
    """
    obj_root = pathlib.Path('/home/wanghao/WORKSPACE/OpenSim_geometry/Geometry')


    for a in obj_root.glob('*.obj'):
    #    print(str(a))
        if 'foot' in str(a):
            bpy.ops.import_scene.obj(filepath=str(a))
    ##    print(a)
    
def paint_weight():
    """ assign weight for each points of each bone objects. 
    """
    remove_existing = True
    
    bones={}
    group_of_bones={
        # head and neck, 10
        'head': 'head',
        'jaw': 'head',
        'cerv1': 'neck',
        'cerv2': 'neck',
        'cerv3': 'neck',
        'cerv4': 'neck',
        'cerv5': 'neck',
        'cerv6': 'neck',
        'cerv7': 'neck',
        # main body, 24
        'clavicle_lvsm':'left_collar',
        'scapula_lvsm':'left_collar',
        'clavicle_rvsm':'right_collar',
        'scapula_rvsm':'right_collar',
        'thoracic1': 'spine3',
        'thoracic2': 'spine3',
        'thoracic3': 'spine3',
        'thoracic4': 'spine3',
        'thoracic5': 'spine3',
        'thoracic6': 'spine3',
        'thoracic7': 'spine2',
        'thoracic8': 'spine2',
        'thoracic9': 'spine2',
        'thoracic10': 'spine2',
        'thoracic11': 'spine2',
        'thoracic12': 'spine2',
        'ribcage_s': 'spine2',
        'lumbar1': 'spine1',
        'lumbar2': 'spine1',
        'lumbar3': 'spine1',
        'lumbar4': 'spine1',
        'lumbar5': 'spine1',
        'sacrum': 'pelvis',
        'left_pelvis': 'pelvis',
        'right_pelvis': 'pelvis',
        # left arm, 29
        'left_uparm': 'left_shoulder',
        'left_forearm': 'left_elbow',
        'capitate_lvs': 'left_wrist',
        'hamate_lvs': 'left_wrist',
        'lunate_lvs': 'left_wrist',
        'pisiform_lvs': 'left_wrist',
        'scaphoid_lvs': 'left_wrist',
        'trapezium_lvs': 'left_wrist',
        'trapezoid_lvs': 'left_wrist',
        'triquetrum_lvs': 'left_wrist',
        'metacarpal2_lvs': 'left_wrist',
        'metacarpal3_lvs': 'left_wrist',
        'metacarpal4_lvs': 'left_wrist',
        'metacarpal5_lvs': 'left_wrist',
        'metacarpal1_lvs': 'left_thumb1',
        'thumb_proximal_lvs': 'left_thumb2',
        'thumb_distal_lvs': 'left_thumb3',
        'index_proximal_lvs': 'left_index1',
        'index_medial_lvs': 'left_index2',
        'index_distal_lvs': 'left_index3',
        'middle_proximal_lvs': 'left_middle1',
        'middle_medial_lvs': 'left_middle2',
        'middle_distal_lvs': 'left_middle3',
        'ring_proximal_lvs': 'left_ring1',
        'ring_medial_lvs': 'left_ring2',
        'ring_distal_lvs': 'left_ring3',
        'little_proximal_lvs': 'left_pinky1',
        'little_medial_lvs': 'left_pinky2',
        'little_distal_lvs': 'left_pinky3',
        # right arm, 29
        'right_uparm': 'right_shoulder',
        'right_forearm': 'right_elbow',
        'capitate_rvs': 'right_wrist',
        'hamate_rvs': 'right_wrist',
        'lunate_rvs': 'right_wrist',
        'pisiform_rvs': 'right_wrist',
        'scaphoid_rvs': 'right_wrist',
        'trapezium_rvs': 'right_wrist',
        'trapezoid_rvs': 'right_wrist',
        'triquetrum_rvs': 'right_wrist',
        'metacarpal2_rvs': 'right_wrist',
        'metacarpal3_rvs': 'right_wrist',
        'metacarpal4_rvs': 'right_wrist',
        'metacarpal5_rvs': 'right_wrist',
        'metacarpal1_rvs': 'right_thumb1',
        'thumb_proximal_rvs': 'right_thumb2',
        'thumb_distal_rvs': 'right_thumb3',
        'index_proximal_rvs': 'right_index1',
        'index_medial_rvs': 'right_index2',
        'index_distal_rvs': 'right_index3',
        'middle_proximal_rvs': 'right_middle1',
        'middle_medial_rvs': 'right_middle2',
        'middle_distal_rvs': 'right_middle3',
        'ring_proximal_rvs': 'right_ring1',
        'ring_medial_rvs': 'right_ring2',
        'ring_distal_rvs': 'right_ring3',
        'little_proximal_rvs': 'right_pinky1',
        'little_medial_rvs': 'right_pinky2',
        'little_distal_rvs': 'right_pinky3',
        # legs, 10
        'left_thigh': 'left_hip',
        'left_patella': 'left_hip',
        'left_leg': 'left_knee',
        'l_foot': 'left_ankle',
        'l_bofoot': 'left_foot',
        'right_thigh': 'right_hip',
        'right_patella': 'right_hip',
        'right_leg': 'right_knee',
        'r_foot': 'right_ankle',
        'r_bofoot': 'right_foot',
    }
    
    for bone_name in group_of_bones.keys():
        # get current obj and observed vertex groups    
        obj = bpy.data.objects[bone_name]
        vgs = obj.vertex_groups
        vertices = obj.data.vertices
        if len(bones) == 0:
            for i, vg in enumerate(vgs):
                bones[vg.name] = i
        
        # remove existing
        if remove_existing:
            # record vertices ids in groups
            vertices_ids_in_groups={}
            for v in vertices:
                for g in v.groups:
                    if g.group not in vertices_ids_in_groups:
                        vertices_ids_in_groups[g.group]=[]
                    vertices_ids_in_groups[g.group].append(v.index)

            # remove existing vertices in groups 
            for gg in vertices_ids_in_groups.keys():
                vgs[gg].remove(vertices_ids_in_groups[gg])
        
        # add new vertices to specified groups
        vertices_indexs = [i for i in range(len(vertices))]
        gg = bones[group_of_bones[bone_name]]
        vgs[gg].add(vertices_indexs, 1.0, 'REPLACE')
       
    
        # for show
        # record vertices ids in groups
        vertices_ids_in_groups={}
        for v in vertices:
            for g in v.groups:
                if g.group not in vertices_ids_in_groups:
                    vertices_ids_in_groups[g.group]=[]
                vertices_ids_in_groups[g.group].append(v.index)
        print(vertices_ids_in_groups)
    
    
def cylinder_between(x1, y1, z1, x2, y2, z2, r):
    """ add cylinder between the points (x1, y1, z1) and (x1, y1, z1).
    """
    dx = x2 - x1
    dy = y2 - y1
    dz = z2 - z1    
    dist = math.sqrt(dx**2 + dy**2 + dz**2)

    bpy.ops.mesh.primitive_cylinder_add(
        calc_uvs=True,
        radius = r, 
        depth = dist,
        location = (dx/2 + x1, dy/2 + y1, dz/2 + z1)   
    )

    phi = math.atan2(dy, dx) 
    theta = math.acos(dz/dist) 

    bpy.context.object.rotation_euler[1] = theta 
    bpy.context.object.rotation_euler[2] = phi 

def remove_all_cylinders():
    bpy.ops.object.select_all(action='DESELECT')
    
    objs = bpy.data.objects
    for obj in objs:
        if "柱体" in obj.name:
            obj.select_set(True)
            bpy.ops.object.delete()

def add_color(keys=['柱体'], colors=[[1,0,0,0.8]]):
    """add color for existing objects.

    Args:
        keys (list, optional): determines the categories of objects need to color. Defaults to ['柱体'].
        colors (list, optional): _description_. Defaults to [[1,0,0,0.8]].
    """
    bpy.ops.object.select_all(action='DESELECT')

    assert len(keys) == len(colors), 'please make sure the number of keys and colors and identity.'
    
    for key, color in zip(keys,colors):
        matc = bpy.data.materials.new(f"{key}_color")
        matc.diffuse_color = color
        
        objs = bpy.data.objects
        for obj in objs:
            if key in obj.name:
                obj.select_set(True)
                obj.active_material = matc
#                bpy.context.collection.objects.link(obj)


if __name__=="__main__":
#    paint_weight()

    remove_all_cylinders()
    cylinder_between(-0.068366, -0.11954, -0.93096, -0.057228, -0.10993, -1.2581, 0.002)
    cylinder_between(-0.080927, -0.085624, -0.93326, -0.072242, -0.080151, -1.259, 0.002)
    cylinder_between(-0.068366, -0.11954, -0.93096, -0.072242, -0.080151, -1.259, 0.002)

    add_color()
#    remove_all_cylinders()