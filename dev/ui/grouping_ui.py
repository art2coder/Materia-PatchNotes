import bpy
from ..operators.grouping import OBJECT_OT_group_by_empty, OBJECT_OT_ungroup_empty

def menu_grouping(self, context):
    layout = self.layout
    layout.separator()
    layout.operator(OBJECT_OT_group_by_empty.bl_idname, icon='OUTLINER_OB_EMPTY')
    layout.operator(OBJECT_OT_ungroup_empty.bl_idname,   icon='X')

def register():
    bpy.types.VIEW3D_MT_object.append(menu_grouping)

def unregister():
    bpy.types.VIEW3D_MT_object.remove(menu_grouping)
