import bpy

_clean_view_previous = {}
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
            "use_clean_view": False,
            "show_cleanview_wire_toggle": False,
            "show_cleanview_lineart_toggle": False,
        }
    return _viewport_states[sid]

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

    if bpy.app.version >= (4, 3, 0):
        space.shading.light = 'STUDIO'
        space.shading.color_type = 'MATERIAL'
        space.shading.background_type = 'THEME'

# --- Operators ---
class MODIFIER_PIE_OT_viewport_render_image(bpy.types.Operator):
    bl_idname = "modifier_pie.viewport_render_image"
    bl_label = "뷰포트 렌더"
    bl_description = "OpenGL 뷰포트를 렌더링하고 렌더 결과 창을 엽니다"

    def execute(self, context):
        # 현재 3D 뷰 컨텍스트에서 OpenGL 렌더 호출
        bpy.ops.render.opengl('INVOKE_DEFAULT', view_context=True)
        return {'FINISHED'}
        return {'CANCELLED'}

class MODIFIER_PIE_OT_toggle_clean_view(bpy.types.Operator):
    bl_idname = "modifier_pie.toggle_clean_view"
    bl_label = "배경색 전환"
    bl_description = "배경을 화이트로 전환"

    def execute(self, context):
        space = get_view3d_space(context)
        context.area.tag_redraw()
        sid = get_space_id(space)

        state = ensure_viewport_state(sid, space)
        use_clean_view = state.get("use_clean_view", False)

        if use_clean_view:
            if sid in _clean_view_previous:
                restore_clean_view_settings(space, _clean_view_previous[sid])
                del _clean_view_previous[sid]
            state["use_clean_view"] = False
        else:
            _clean_view_previous[sid] = store_clean_view_settings(space)
            apply_clean_view_settings(space)
            state["use_clean_view"] = True

        return {'FINISHED'}

class MODIFIER_PIE_OT_toggle_wire(bpy.types.Operator):
    bl_idname = "modifier_pie.toggle_wire"
    bl_label = "와이어 보기 전환"
    bl_description = "매쉬를 와이어프레임으로 보기"

    def execute(self, context):
        space = get_view3d_space(context)
        sid = get_space_id(space)
        state = ensure_viewport_state(sid)

        state["show_cleanview_wire_toggle"] = not state.get("show_cleanview_wire_toggle", False)
        state["show_cleanview_lineart_toggle"] = False

        if state["show_cleanview_wire_toggle"]:
            space.shading.type = 'WIREFRAME'
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

        space.shading.type = 'SOLID'

        for obj in context.scene.objects:
            if obj.type == 'GPENCIL' and "LineArt" in obj.name:
                if bpy.app.version >= (4, 3, 0):
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
        sid = get_space_id(space)
        state = ensure_viewport_state(sid, space)

        layout.operator("modifier_pie.viewport_render_image", text="뷰포트 렌더", icon="RENDER_RESULT")
        layout.operator("modifier_pie.toggle_clean_view", text="배경색 전환", icon="WORKSPACE", depress=state["use_clean_view"])

        row = layout.row(align=True)
        row.operator("modifier_pie.toggle_wire", text="와이어", icon="SHADING_WIRE", depress=state["show_cleanview_wire_toggle"])
        row.operator("modifier_pie.toggle_lineart", text="라인아트", icon="MOD_LINEART", depress=state["show_cleanview_lineart_toggle"])

def draw_handler():
    pass

classes = [
    MODIFIER_PIE_OT_viewport_render_image,
    MODIFIER_PIE_OT_toggle_clean_view,
    MODIFIER_PIE_OT_toggle_wire,
    MODIFIER_PIE_OT_toggle_lineart,
    MODIFIER_PIE_PT_clean_view_panel,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    global _draw_handle
    if _draw_handle:
        bpy.types.SpaceView3D.draw_handler_remove(_draw_handle, 'WINDOW')
    _draw_handle = bpy.types.SpaceView3D.draw_handler_add(draw_handler, (), 'WINDOW', 'POST_PIXEL')
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                space = area.spaces.active
                sid = get_space_id(space)
                ensure_viewport_state(sid, space)


def unregister():
    global _draw_handle
    if _draw_handle:
        bpy.types.SpaceView3D.draw_handler_remove(_draw_handle, 'WINDOW')
        _draw_handle = None
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
