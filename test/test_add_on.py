
bl_info = {
    "name": "Test Add-on",
    "blender": (3, 6, 0),
    "category": "Object",
    "author": "Your Name",
    "version": (0, 0, 1),
    "location": "View3D > Tools > Test Add-on",
    "description": "Description of your add-on",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "support": "COMMUNITY",
}


import bpy
from bpy_extras.io_utils import ImportHelper,ExportHelper
from bpy.props import BoolProperty, EnumProperty, FloatProperty, IntProperty, PointerProperty, StringProperty
from bpy.types import PropertyGroup


import sys
import os
sys.path.append(".")

# from libs.utils import print_add

class PG_TESTADDONProperties(bpy.types.PropertyGroup):

    test_enum_property: bpy.props.EnumProperty(
        name = "Model",
        description = "test addon",
        items = [ ("female", "Female", ""), ("male", "Male", ""), ("neutral", "Neutral", ""), ("helicopter", "Helicopter", "") ]
    )

class TESTAddGender(bpy.types.Operator):
    bl_idname = "scene.test_add_gender"
    bl_label = "Add"
    bl_description = ("Add test model of selected gender to scene")
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        try:
            # Enable button only if in Object Mode
            if (context.active_object is None) or (context.active_object.mode == 'OBJECT'):
                return True
            else: 
                return False
        except: return False

    def execute(self, context):
        gender = context.window_manager.test_tools.test_enum_property
        print("Adding gender: " + gender)

        path = os.path.dirname(os.path.realpath(__file__))

        # Use 300 shape model by default if available
        model_path = os.path.join(path, "data", SMPLX_MODELFILE_300)
        if os.path.exists(model_path):
            model_file = SMPLX_MODELFILE_300
        else:
            model_file = SMPLX_MODELFILE

        objects_path = os.path.join(path, "data", model_file, "Object")
        object_name = "SMPLX-mesh-" + gender

        bpy.ops.wm.append(filename=object_name, directory=str(objects_path))

        # Select imported mesh
        object_name = context.selected_objects[0].name
        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = bpy.data.objects[object_name]
        bpy.data.objects[object_name].select_set(True)

        # Set currently selected hand pose
        bpy.ops.object.smplx_set_handpose('EXEC_DEFAULT')

        return {'FINISHED'}

class TESTAddAnimation2(bpy.types.Operator, ImportHelper):
    bl_idname = "object.test2_add_animation"
    bl_label = "Add Animation"
    bl_description = ("Load AMASS/SMPL-X animation and create animated SMPL-X body")
    bl_options = {'REGISTER', 'UNDO'}

    filter_glob: StringProperty(
        default="*.npz",
        options={'HIDDEN'}
    )

    @classmethod
    def poll(cls, context):
        try:
            # Always enable button
            return True
        except: return False

    def execute(self, context):
        # Load .npz file
        print("Loading: " + self.filepath)

        return {'FINISHED'}
    
class TESTAddAnimation(bpy.types.Operator, ImportHelper):
    bl_idname = "object.test_add_animation"
    bl_label = "Add Animation"
    bl_description = ("Load AMASS/SMPL-X animation and create animated SMPL-X body")
    bl_options = {'REGISTER', 'UNDO'}

    filter_glob: bpy.props.StringProperty(
        default="*",
        options={'HIDDEN'}
    )
    
    @classmethod
    def poll(cls, context):
        try:
            # Enable button only if mesh or armature is active object
            return True
        except: 
            return False

    def execute(self, context):
        # Load .npz file
        print("Loading: " + self.filepath)
    
        return {'FINISHED'}
        
class TestOps(bpy.types.Operator):
    bl_idname = "object.test_operator"
    bl_label = "Test Operator."
    bl_description = ("Test bpy.types.Operator.")
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        try:
            # Enable button only if mesh is active object
            return (context.object.type == 'MESH')
        except: return False

    def execute(self, context):
        print("TestOps executed.")
        
        return {'FINISHED'}

class Test_PT_Panel(bpy.types.Panel):
    bl_label = "TEST_PANEL"
    bl_category = "TESTPanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_idname = "Test_PT_Panel"

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        
        col.operator("object.test_operator")
        col.separator()
        
        col.operator("object.test_add_animation")
        col.separator()
        
        # row = col.row(align=True)
        col.prop(context.window_manager.test_tools, "test_enum_property")
        col.operator("scene.test_add_gender", text="ADUA")
        
classes = [
    PG_TESTADDONProperties,
    TESTAddGender,
    TESTAddAnimation,
    TESTAddAnimation2,
    TestOps,
    Test_PT_Panel,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        
    # Store properties under WindowManager (not Scene) so that they are not saved in .blend files and always show default values after loading
    bpy.types.WindowManager.test_tools = bpy.props.PointerProperty(type=PG_TESTADDONProperties)
    
def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.WindowManager.test_tools

if __name__ == "__main__":
    print("Registering Addon...")
    register()
