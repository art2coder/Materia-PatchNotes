import bpy

def menu_grouping(self, context):
    layout = self.layout
    layout.separator()
    layout.operator("object.group_by_empty", icon='OUTLINER_OB_EMPTY')
    layout.operator("object.ungroup_empty",   icon='X')

def register():
    bpy.types.VIEW3D_MT_object.append(menu_grouping)

def unregister():
    bpy.types.VIEW3D_MT_object.remove(menu_grouping)
