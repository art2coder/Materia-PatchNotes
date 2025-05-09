
bl_info = {
    "name": "Restore Grease Pencil Color",
    "author": "EJ",
    "version": (1, 0),
    "blender": (4, 2, 0),
    "location": "View3D > View",
    "description": "Restore object.color for all Grease Pencil objects",
    "category": "Object",
}


import bpy

class GPENCIL_OT_restore_object_color(bpy.types.Operator):
    bl_idname = "object.restore_gpencil_color"
    bl_label = "Restore Grease Pencil Color"
    bl_description = "Restores object.color for all Grease Pencil objects to prevent color override"
    bl_options = {'REGISTER', 'UNDO'}

    color: bpy.props.FloatVectorProperty(
        name="Restore Color",
        subtype='COLOR',
        size=4,
        min=0.0, max=1.0,
        default=(0.0, 0.0, 0.0, 1.0)  # 검정색
    )

    def execute(self, context):
        count = 0
        for obj in bpy.data.objects:
            if obj.type == 'GPENCIL':
                obj.color = self.color
                count += 1
        self.report({'INFO'}, f"{count} Grease Pencil object(s) color restored")
        return {'FINISHED'}

# 🔽 View 메뉴에 오퍼레이터 추가
def draw_in_view_menu(self, context):
    self.layout.separator()
    self.layout.operator(GPENCIL_OT_restore_object_color.bl_idname)

# 등록/해제 함수
def register():
    bpy.utils.register_class(GPENCIL_OT_restore_object_color)
    bpy.types.VIEW3D_MT_view.append(draw_in_view_menu)

def unregister():
    bpy.types.VIEW3D_MT_view.remove(draw_in_view_menu)
    bpy.utils.unregister_class(GPENCIL_OT_restore_object_color)

if __name__ == "__main__":
    register()


