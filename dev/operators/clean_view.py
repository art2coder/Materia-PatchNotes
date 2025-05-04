import bpy

_clean_view_previous = {}
_viewport_states = {}


def get_view3d_space(context):
    area = context.area
    if area and area.type == 'VIEW_3D':
        return area.spaces.active
    return None


def get_space_id(space):
    return str(space.as_pointer())


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


# ------------------------- 오퍼레이터 -------------------------

class MODIFIER_PIE_OT_toggle_clean_view(bpy.types.Operator):
    bl_idname = "modifier_pie.toggle_clean_view"
    bl_label = "배경색 전환"
    bl_description = "이 뷰포트만 클린 뷰 모드로 전환하거나 복원"

    def execute(self, context):
        space = get_view3d_space(context)
        sid = get_space_id(space)
        state = _viewport_states.get(sid, {})
        use_clean_view = state.get("use_clean_view", False)

        if not use_clean_view:
            _clean_view_previous[sid] = store_clean_view_settings(space)
            apply_clean_view_settings(space)
            state["use_clean_view"] = True
        else:
            if sid in _clean_view_previous:
                restore_clean_view_settings(space, _clean_view_previous[sid])
                del _clean_view_previous[sid]
            state["use_clean_view"] = False

        _viewport_states[sid] = state
        return {'FINISHED'}


class MODIFIER_PIE_OT_toggle_wire(bpy.types.Operator):
    bl_idname = "modifier_pie.toggle_wire"
    bl_label = "와이어 보기 전환"
    bl_description = "이 뷰포트만 와이어프레임 보기 토글"

    def execute(self, context):
        space = get_view3d_space(context)
        sid = get_space_id(space)
        state = _viewport_states.setdefault(sid, {})

        current = state.get("show_cleanview_wire_toggle", False)
        state["show_cleanview_wire_toggle"] = not current
        state["show_cleanview_lineart_toggle"] = False

        _viewport_states[sid] = state
        return {'FINISHED'}


class MODIFIER_PIE_OT_toggle_lineart(bpy.types.Operator):
    bl_idname = "modifier_pie.toggle_lineart"
    bl_label = "라인아트 전환"
    bl_description = "이 뷰포트만 라인아트 표시 토글"

    def execute(self, context):
        space = get_view3d_space(context)
        sid = get_space_id(space)
        state = _viewport_states.setdefault(sid, {})

        current = state.get("show_cleanview_lineart_toggle", False)
        state["show_cleanview_lineart_toggle"] = not current
        state["show_cleanview_wire_toggle"] = False

        _viewport_states[sid] = state
        return {'FINISHED'}


# ------------------------- 패널 -------------------------

class MODIFIER_PIE_PT_clean_view_panel(bpy.types.Panel):
    bl_label = "2D 모드"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Extras"

    def draw(self, context):
        layout = self.layout
        space = get_view3d_space(context)
        sid = get_space_id(space)
        state = _viewport_states.setdefault(sid, {
            "use_clean_view": False,
            "show_cleanview_wire_toggle": False,
            "show_cleanview_lineart_toggle": False,
        })

        layout.operator(
            "modifier_pie.toggle_clean_view",
            text="배경색 전환",
            icon="WORKSPACE",
            depress=state["use_clean_view"]
        )

        row = layout.row(align=True)
        row.operator(
            "modifier_pie.toggle_wire",
            text="와이어",
            icon="SHADING_WIRE",
            depress=state["show_cleanview_wire_toggle"]
        )
        row.operator(
            "modifier_pie.toggle_lineart",
            text="라인아트",
            icon="MOD_LINEART",
            depress=state["show_cleanview_lineart_toggle"]
        )
        if "LineArt" not in bpy.data.collections:
            row.enabled = False


# ------------------------- 핸들러 -------------------------

def draw_handler(scene):
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type != 'VIEW_3D':
                continue
            space = area.spaces.active
            sid = get_space_id(space)
            state = _viewport_states.get(sid, {})

            if state.get("show_cleanview_wire_toggle", False):
                space.shading.type = 'WIREFRAME'
                space.shading.show_xray = False
            elif state.get("show_cleanview_lineart_toggle", False):
                col = bpy.data.collections.get("LineArt")
                if col:
                    layer_collection = None
                    def recursive_search(layer_coll):
                        nonlocal layer_collection
                        if layer_coll.collection == col:
                            layer_collection = layer_coll
                            return True
                        for child in layer_coll.children:
                            if recursive_search(child):
                                return True
                        return False
                    recursive_search(bpy.context.view_layer.layer_collection)
                    if layer_collection:
                        layer_collection.exclude = False
                space.shading.type = 'SOLID'
            else:
                space.shading.type = 'SOLID'


# ------------------------- 등록/해제 -------------------------

classes = [
    MODIFIER_PIE_OT_toggle_clean_view,
    MODIFIER_PIE_OT_toggle_wire,
    MODIFIER_PIE_OT_toggle_lineart,
    MODIFIER_PIE_PT_clean_view_panel,
]

_draw_handle = None

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    global _draw_handle
    _draw_handle = bpy.types.SpaceView3D.draw_handler_add(
        draw_handler, (bpy.context.scene,), 'WINDOW', 'POST_PIXEL'
    )

def unregister():
    global _draw_handle
    if _draw_handle:
        bpy.types.SpaceView3D.draw_handler_remove(_draw_handle, 'WINDOW')
        _draw_handle = None

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
