import bpy

class MODIFIER_PIE_PT_camera_quick_settings(bpy.types.Panel):
    bl_label = "카메라 설정"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "정리"

    def draw(self, context):
        layout = self.layout
        view = context.space_data
        scene = context.scene

        col = layout.column()

        # 카메라 선택
        col.label(text="Camera", icon='CAMERA_DATA')
        col.template_ID(scene, "camera", new="object.camera_add")
        view.camera = scene.camera

        # 뷰 잠금
        col.prop(view, "lock_camera", text="Camera to View", toggle=True)

        camera = view.camera
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
            col.prop(cam_data, "clip_start", text="Start")
            col.prop(cam_data, "clip_end", text="End")

            col.separator()
            col.label(text="Composition Guides")

            row = col.row(align=True)
            row.prop(cam_data, "show_composition_thirds", text="Thirds", toggle=True)
            row.prop(cam_data, "show_composition_center", text="Center", toggle=True)

            col.separator()
            col.prop(view, "use_camera_passepartout", text="Passepartout", toggle=True)

# 등록/해제
classes = [
    MODIFIER_PIE_PT_camera_quick_settings
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
