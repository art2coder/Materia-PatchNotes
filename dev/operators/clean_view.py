import bpy

# --- 클린 뷰 설정 저장용 ---
_clean_view_previous = {}

# --- 유틸리티 함수 ---
def get_view3d_space(context):
    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    return space
    return None

def store_clean_view_settings(space):
    return {
        'studio_light': getattr(space.shading, 'studio_light', None),
        'light': space.shading.light,
        'color_type': space.shading.color_type,
        'background_color': space.shading.background_color[:],
        'background_type': space.shading.background_type,
        'show_overlays': space.overlay.show_overlays,
        'type': space.shading.type,
    }

def apply_clean_view_settings(space):
    space.shading.type = 'SOLID'
    space.shading.background_type = 'VIEWPORT'
    try:
        space.shading.studio_light = 'basic.sl'
    except TypeError:
        pass
    space.shading.background_color = (1.0, 1.0, 1.0)
    space.shading.light = 'FLAT'
    space.shading.color_type = 'OBJECT'
    space.overlay.show_overlays = False

def restore_clean_view_settings(space, settings):
    space.shading.type = settings.get('type', 'SOLID')
    space.shading.background_type = settings['background_type']
    studio_light = settings.get('studio_light')
    if studio_light:
        try:
            space.shading.studio_light = studio_light
        except TypeError:
            pass
    space.shading.light = settings['light']
    space.shading.color_type = settings['color_type']
    space.shading.background_color = settings['background_color']
    space.overlay.show_overlays = settings['show_overlays']

# --- 오퍼레이터 ---
class MODIFIER_PIE_OT_toggle_clean_view(bpy.types.Operator):
    bl_idname = "modifier_pie.toggle_clean_view"
    bl_label = "클린 뷰 토글"
    bl_description = "뷰포트를 클린 모드로 전환하거나 복원합니다."
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        space = get_view3d_space(context)
        if not space:
            self.report({'WARNING'}, "3D 뷰포트를 찾을 수 없습니다.")
            return {'CANCELLED'}

        key = 'global'
        if key not in _clean_view_previous:
            _clean_view_previous[key] = store_clean_view_settings(space)
            apply_clean_view_settings(space)
        else:
            restore_clean_view_settings(space, _clean_view_previous[key])
            del _clean_view_previous[key]

        return {'FINISHED'}

# --- 패널 ---
class MODIFIER_PIE_PT_clean_view_panel(bpy.types.Panel):
    bl_label = "클린 뷰 모드"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "정리"

    def draw(self, context):
        layout = self.layout
        layout.operator("modifier_pie.toggle_clean_view", text="클린 뷰 토글", icon="HIDE_OFF")

# --- 등록 / 해제 ---
classes = [
    MODIFIER_PIE_OT_toggle_clean_view,
    MODIFIER_PIE_PT_clean_view_panel,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
