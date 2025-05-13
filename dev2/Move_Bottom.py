bl_info = {
    "name": "Move Bottom to Z=0",
    "blender": (4, 2, 0),
    "category": "Object",
    "author": "ChatGPT + User",
    "description": "선택한 오브젝트의 바닥면을 Z=0 위치로 이동시킵니다.",
}

import bpy
from mathutils import Vector

class OBJECT_OT_move_bottom_to_z0(bpy.types.Operator):
    bl_idname = "object.move_bottom_to_z0"
    bl_label = "Move Bottom"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue

            # 월드 공간에서 바닥면 계산
            bbox = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
            min_z = min(v.z for v in bbox)
            delta_z = -min_z

            # 이동 적용
            obj.location.z += delta_z

        return {'FINISHED'}

class VIEW3D_PT_move_bottom_to_z0_panel(bpy.types.Panel):
    bl_label = "Move Bottom"
    bl_idname = "VIEW3D_PT_move_bottom_to_z0_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Extras"

    def draw(self, context):
        layout = self.layout
        layout.operator("object.move_bottom_to_z0", icon='TRIA_DOWN')

classes = [
    OBJECT_OT_move_bottom_to_z0,
    VIEW3D_PT_move_bottom_to_z0_panel
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
