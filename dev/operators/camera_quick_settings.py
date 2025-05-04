import bpy

class VIEW3D_OT_reset_clip_values(bpy.types.Operator):
    """클리핑 값을 기본값으로 초기화"""
    bl_idname = "view3d.reset_clip_values"
    bl_label = "Reset Clipping"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        cam = context.space_data.camera
        if cam and cam.type == 'CAMERA':
            cam.data.clip_start = 0.01
            cam.data.clip_end = 1000.0
            self.report({'INFO'}, "Clipping values reset.")
        return {'FINISHED'}


class MODIFIER_PIE_PT_camera_quick_settings(bpy.types.Panel):
    bl_label = "카메라 설정"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Extras"

    def draw(self, context):
        layout = self.layout
        view = context.space_data
        scene = context.scene

        col = layout.column()
        col.label(text="Camera", icon='CAMERA_DATA')
        col.template_ID(scene, "camera", new="object.camera_add")

        icon = 'HIDE_OFF' if view.lock_camera else 'HIDE_ON'
        col.prop(view, "lock_camera", text="카메라 시점 모드", icon=icon, toggle=True)

        camera = view.camera or scene.camera
        if camera and camera.type == 'CAMERA':
            cam_data = camera.data

            col.separator()
            col.label(text="Lens Settings")
            if cam_data.lens_unit == 'MILLIMETERS':
                col.prop(cam_data, "lens", text="Focal Length")
            else:
                col.prop(cam_data, "angle", text="Field of View")
            col.prop(cam_data, "lens_unit", text="Unit")

            col.separator()
            col.label(text="Clipping")
            row = col.row(align=True)
            row.prop(cam_data, "clip_start", text="Start")
            row.prop(cam_data, "clip_end", text="End")

            col.operator("view3d.reset_clip_values", text="초기화")

            col.separator()
            col.label(text="Composition Guides")
            row = col.row(align=True)
            row.prop(cam_data, "show_composition_thirds", text="Thirds", toggle=True)
            row.prop(cam_data, "show_composition_center", text="Center", toggle=True)

            col.separator()
            col.prop(view, "use_camera_passepartout", text="Passepartout", toggle=True)


classes = [
    MODIFIER_PIE_PT_camera_quick_settings,
    VIEW3D_OT_reset_clip_values
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
