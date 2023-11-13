import pathlib
import bpy


def import_batch_obj():
    obj_root = pathlib.Path('/home/wanghao/WORKSPACE/OpenSim_geometry/Geometry')


    for a in obj_root.glob('*.obj'):
    #    print(str(a))
        if 'foot' in str(a):
            bpy.ops.import_scene.obj(filepath=str(a))
    ##    print(a)
    
def paint_weight():
    pass
    

if __name__=="__main__":
    paint_weight()