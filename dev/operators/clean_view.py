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

        row = layout.row(align=True)
        row.prop(context.scene, "show_cleanview_wire_toggle", toggle=True, text="와이어", icon="SHADING_WIRE")
        row.prop(context.scene, "show_cleanview_lineart_toggle", toggle=True, text="라인아트", icon="MOD_LINEART")
        if "LineArt" not in bpy.data.collections:
            row.enabled = False

# --- 추가 기능: 와이어/라인아트 토글 ---
def update_cleanview_wire_toggle(self, context):
    space = get_view3d_space(context)
    if space:
        if context.scene.show_cleanview_wire_toggle:
            space.shading.type = 'WIREFRAME'
            space.shading.show_xray = False
        else:
            space.shading.type = 'SOLID'

def update_cleanview_lineart_toggle(self, context):
    col = bpy.data.collections.get("LineArt")
    if col:
        # 'Exclude from View Layer' 는 해당 콜렉션이 현재 View Layer에 포함되는지에 따라 결정됨
        layer_collection = None
        view_layer = context.view_layer

        def recursive_search(layer_coll):
            nonlocal layer_collection
            if layer_coll.collection == col:
                layer_collection = layer_coll
                return True
            for child in layer_coll.children:
                if recursive_search(child):
                    return True
            return False

        recursive_search(view_layer.layer_collection)

        if layer_collection:
            layer_collection.exclude = not context.scene.show_cleanview_lineart_toggle


# --- 등록 / 해제 ---
classes = [
    MODIFIER_PIE_OT_toggle_clean_view,
    MODIFIER_PIE_PT_clean_view_panel,
]

def register():
    bpy.types.Scene.show_cleanview_wire_toggle = bpy.props.BoolProperty(
        name="와이어 보기 토글",
        description="X-Ray 없이 와이어프레임 보기",
        default=False,
        update=update_cleanview_wire_toggle
    )

    bpy.types.Scene.show_cleanview_lineart_toggle = bpy.props.BoolProperty(
        name="라인아트 표시 토글",
        description="'LineArt' 콜렉션의 보기 설정을 토글합니다.",
        default=False,
        update=update_cleanview_lineart_toggle
    )
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    del bpy.types.Scene.show_cleanview_wire_toggle
    del bpy.types.Scene.show_cleanview_lineart_toggle
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
