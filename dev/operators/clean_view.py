import bpy

_viewport_states = {}

_draw_handle = None

# --- 유틸리티 함수 ---

def get_view3d_space(context):
    area = context.area
    if area and area.type == 'VIEW_3D':
        return area.spaces.active
    return None

def get_space_id(space):
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.spaces.active == space:
                return f"{window.as_pointer()}_{area.as_pointer()}"
    return str(space.as_pointer())

def ensure_viewport_state(sid, space=None):
    if sid not in _viewport_states:
        if space:
            space.shading.type = 'SOLID'
            space.shading.background_type = 'THEME'
            space.shading.light = 'STUDIO'
            space.shading.color_type = 'MATERIAL'
            space.overlay.show_overlays = True
        _viewport_states[sid] = {
            "show_cleanview_wire_toggle": False,
            "show_cleanview_lineart_toggle": False,
        }
    return _viewport_states[sid]

# 배경색 업데이트 콜백
def update_clean_bg(self, context):
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                space = area.spaces.active
                space.shading.background_type = 'VIEWPORT'
                space.shading.background_color = context.scene.clean_view_bg_color

# Scene에 배경색 프로퍼티 추가
bpy.types.Scene.clean_view_bg_color = bpy.props.FloatVectorProperty(
    name="배경색",
    subtype='COLOR',
    size=3,
    default=(1.0, 1.0, 1.0),
    min=0.0,
    max=1.0,
    update=update_clean_bg
)

# --- Operators ---

class MODIFIER_PIE_OT_viewport_render_image(bpy.types.Operator):
    bl_idname = "modifier_pie.viewport_render_image"
    bl_label = "뷰포트 렌더"
    bl_description = "뷰포트를 렌더링하고 렌더 결과 창을 엽니다"

    def execute(self, context):
        try:
            bpy.ops.render.opengl('INVOKE_DEFAULT', view_context=True)
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"렌더링 실패: {str(e)}")
            return {'CANCELLED'}

# =================================================================
# ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼ 새로운 기능 추가 ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
# =================================================================

class MODIFIER_PIE_OT_reset_bg_to_theme(bpy.types.Operator):
    """뷰포트 배경을 기본 테마색으로 되돌립니다"""
    bl_idname = "modifier_pie.reset_bg_to_theme"
    bl_label = "배경색"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        space = get_view3d_space(context)
        if space:
            space.shading.background_type = 'THEME'
            return {'FINISHED'}
        self.report({'WARNING'}, "3D 뷰포트를 찾을 수 없습니다.")
        return {'CANCELLED'}

# =================================================================
# ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲ 새로운 기능 추가 ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲
# =================================================================

class MODIFIER_PIE_OT_toggle_wire(bpy.types.Operator):
    bl_idname = "modifier_pie.toggle_wire"
    bl_label = "와이어 보기 전환"
    bl_description = "메시를 선만 보이는 와이어프레임 모드로 전환합니다"

    def execute(self, context):
        space = get_view3d_space(context)
        if not space:
            return {'CANCELLED'}
        sid = get_space_id(space)
        state = ensure_viewport_state(sid)
        state["show_cleanview_wire_toggle"] = not state.get("show_cleanview_wire_toggle", False)
        state["show_cleanview_lineart_toggle"] = False
        if state["show_cleanview_wire_toggle"]:
            space.shading.type = 'WIREFRAME'
            if hasattr(space.shading, 'show_xray'):
                space.shading.show_xray = False
        else:
            space.shading.type = 'SOLID'
        return {'FINISHED'}

class MODIFIER_PIE_OT_toggle_lineart(bpy.types.Operator):
    bl_idname = "modifier_pie.toggle_lineart"
    bl_label = "라인아트 전환"
    bl_description = "'LineArt'라는 이름의 콜렉션을 보이게 하거나 숨깁니다"

    def execute(self, context):
        space = get_view3d_space(context)
        if not space:
            return {'CANCELLED'}
        sid = get_space_id(space)
        state = ensure_viewport_state(sid)
        state["show_cleanview_lineart_toggle"] = not state.get("show_cleanview_lineart_toggle", False)
        state["show_cleanview_wire_toggle"] = False
        col = bpy.data.collections.get("LineArt")
        if col:
            def toggle_collection_in_all_layers():
                for layer in context.scene.view_layers:
                    def recursive(layer_coll):
                        if layer_coll.collection == col:
                            layer_coll.exclude = not state["show_cleanview_lineart_toggle"]
                            return True
                        for child in layer_coll.children:
                            if recursive(child):
                                return True
                        return False
                    recursive(layer.layer_collection)
            toggle_collection_in_all_layers()

        is_lineart_visible = state["show_cleanview_lineart_toggle"]
        space.show_object_viewport_mesh = not is_lineart_visible
        space.shading.type = 'SOLID'

        for obj in context.scene.objects:
            if obj.type == 'GPENCIL' and "LineArt" in obj.name:
                if bpy.app.version >= (4, 4, 0):
                    if hasattr(obj.data, "viewport_display"):
                        obj.data.viewport_display.stroke_depth_order = 'FRONT'
                elif bpy.app.version >= (4, 3, 0):
                    if hasattr(obj.data, "viewport_display"):
                        obj.data.viewport_display.stroke_depth_order = 'FRONT'
                elif hasattr(obj.data, "stroke_depth_order"):
                    obj.data.stroke_depth_order = '3D'

                if len(obj.data.materials) == 0:
                    mat = bpy.data.materials.new(name="LineArt_Black")
                    if hasattr(mat, "grease_pencil"):
                        mat.grease_pencil.stroke_color = (0, 0, 0, 1)
                    obj.data.materials.append(mat)
                else:
                    for mat in obj.data.materials:
                        if hasattr(mat, "grease_pencil"):
                            if bpy.app.version >= (4, 3, 0):
                                mat.grease_pencil.stroke_style = 'SOLID'
                                mat.grease_pencil.stroke_color = (0, 0, 0, 1)
                                mat.grease_pencil.fill_style = 'SOLID'
                                mat.grease_pencil.fill_color = (1, 1, 1, 0)

        if bpy.app.version >= (4, 3, 0):
            space.shading.color_type = 'MATERIAL'

        return {'FINISHED'}

class MODIFIER_PIE_PT_clean_view_panel(bpy.types.Panel):
    bl_label = "라인 렌더"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Extras"

    def draw(self, context):
        layout = self.layout
        space = get_view3d_space(context)
        if not space:
            layout.label(text="3D 뷰포트가 필요합니다")
            return

        sid = get_space_id(space)
        state = ensure_viewport_state(sid, space)

        layout.operator("modifier_pie.viewport_render_image", text="뷰포트 렌더", icon="RENDER_RESULT")

        # =================================================================
        # ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼ 수정된 부분 ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
        # =================================================================
        row = layout.row(align=True)
        # "배경색" 버튼 추가 (클릭 시 테마색으로 변경)
        row.operator(MODIFIER_PIE_OT_reset_bg_to_theme.bl_idname, text="배경색")
        # 라벨 없는 색상 선택기 추가
        row.prop(context.scene, "clean_view_bg_color", text="")
        # =================================================================
        # ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲ 수정된 부분 ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲
        # =================================================================

        row2 = layout.row(align=True)
        row2.operator("modifier_pie.toggle_wire", text="와이어", icon="SHADING_WIRE", depress=state["show_cleanview_wire_toggle"])
        row2.operator("modifier_pie.toggle_lineart", text="라인아트", icon="MOD_LINEART", depress=state["show_cleanview_lineart_toggle"])

        layout.separator()

        layout.prop(context.scene.render, "film_transparent", text="배경 투명화")

def draw_handler():
    pass

# =================================================================
# ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼ 수정된 부분 ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
# =================================================================
classes = [
    MODIFIER_PIE_OT_viewport_render_image,
    MODIFIER_PIE_OT_reset_bg_to_theme, # 새로 추가한 클래스 등록
    MODIFIER_PIE_OT_toggle_wire,
    MODIFIER_PIE_OT_toggle_lineart,
    MODIFIER_PIE_PT_clean_view_panel,
]
# =================================================================
# ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲ 수정된 부분 ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲
# =================================================================


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    try:
        if bpy.context and bpy.context.scene and hasattr(bpy.context.scene, 'view_settings'):
            bpy.context.scene.view_settings.view_transform = 'Standard'
    except Exception as e:
        print(f"뷰 변환 기본값 설정 실패: {e}")

    global _draw_handle
    if _draw_handle:
        bpy.types.SpaceView3D.draw_handler_remove(_draw_handle, 'WINDOW')
    _draw_handle = bpy.types.SpaceView3D.draw_handler_add(draw_handler, (), 'WINDOW', 'POST_PIXEL')

    try:
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'VIEW_3D':
                    space = area.spaces.active
                    sid = get_space_id(space)
                    ensure_viewport_state(sid, space)
    except:
        pass

def unregister():
    global _draw_handle
    if _draw_handle:
        bpy.types.SpaceView3D.draw_handler_remove(_draw_handle, 'WINDOW')
    _draw_handle = None
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
