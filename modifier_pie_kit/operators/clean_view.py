import bpy

_viewport_states = {}
_draw_handle = None
_modal_operator = None
_fullscreen_toggle_pending = False

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
                return f"space_{space.as_pointer()}"
    return f"space_{space.as_pointer()}"

def get_fallback_state_id():
    return "global_viewport_state"

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
            "background_type": 'THEME',
            "background_color": (0.051, 0.051, 0.051),
        }
    
    return _viewport_states[sid]

def restore_background_state(space, state):
    if space and state:
        try:
            target_type = state.get("background_type", 'THEME')
            current_type = space.shading.background_type
            
            if current_type != target_type:
                space.shading.background_type = target_type
                if target_type == 'VIEWPORT':
                    space.shading.background_color = state.get("background_color", (1.0, 1.0, 1.0))
                return True
        except:
            pass
    return False

def save_background_state(sid, bg_type, bg_color=None):
    if sid not in _viewport_states:
        _viewport_states[sid] = {
            "show_cleanview_wire_toggle": False,
            "show_cleanview_lineart_toggle": False,
            "background_type": 'THEME',
            "background_color": (0.051, 0.051, 0.051),
        }
    
    _viewport_states[sid]["background_type"] = bg_type
    if bg_color:
        _viewport_states[sid]["background_color"] = bg_color
    
    # 전역 상태에도 저장
    fallback_id = get_fallback_state_id()
    _viewport_states[fallback_id] = _viewport_states[sid].copy()

def restore_all_viewport_backgrounds():
    """전체화면 전환 후 모든 뷰포트의 배경 복원"""
    try:
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'VIEW_3D':
                    space = area.spaces.active
                    sid = get_space_id(space)
                    
                    if sid in _viewport_states:
                        state = _viewport_states[sid]
                    else:
                        fallback_id = get_fallback_state_id()
                        if fallback_id in _viewport_states:
                            state = _viewport_states[fallback_id]
                            _viewport_states[sid] = state.copy()
                        else:
                            continue
                    
                    restore_background_state(space, state)
    except:
        pass

# --- Modal Operator for Key Detection ---

class MODIFIER_PIE_OT_fullscreen_key_listener(bpy.types.Operator):
    """Ctrl+Space 및 화면 전환 이벤트를 감지하는 Modal Operator"""
    bl_idname = "modifier_pie.fullscreen_key_listener"
    bl_label = "Fullscreen Key Listener"
    bl_options = {'REGISTER'}

    def __init__(self):
        self.last_area_count = 0
        self.pending_restore = False

    def modal(self, context, event):
        global _fullscreen_toggle_pending
        
        # Ctrl+Space 감지 (Toggle Maximize Area)
        if (event.type == 'SPACE' and event.ctrl and event.value == 'PRESS'):
            print("Ctrl+Space 감지: 화면 전환 예정")
            _fullscreen_toggle_pending = True
            self.pending_restore = True
            
            # 0.1초 후 배경 복원 시도
            def delayed_restore():
                restore_all_viewport_backgrounds()
                return None
            bpy.app.timers.register(delayed_restore, first_interval=0.1)
        
        # 화면 영역 변경 감지 (화면 전환 완료 감지)
        current_areas = []
        try:
            for window in bpy.context.window_manager.windows:
                current_areas.extend([area.type for area in window.screen.areas])
            
            current_area_count = len(current_areas)
            
            # 화면 영역 수가 변경되었거나 전환이 예정되어 있으면 복원
            if (current_area_count != self.last_area_count or _fullscreen_toggle_pending) and self.pending_restore:
                print("화면 전환 감지: 배경 복원 중")
                restore_all_viewport_backgrounds()
                _fullscreen_toggle_pending = False
                self.pending_restore = False
                
            self.last_area_count = current_area_count
        except:
            pass
        
        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

# 배경색 업데이트 콜백
def update_clean_bg(self, context):
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                space = area.spaces.active
                sid = get_space_id(space)
                
                space.shading.background_type = 'VIEWPORT'
                space.shading.background_color = context.scene.clean_view_bg_color
                
                save_background_state(sid, 'VIEWPORT', context.scene.clean_view_bg_color)

# --- Operators ---

class MODIFIER_PIE_OT_viewport_render_image(bpy.types.Operator):
    bl_idname = "modifier_pie.viewport_render_image"
    bl_label = "뷰포트 렌더"
    bl_description = "뷰포트를 렌더링하고 렌더 결과 창을 엽니다"

    def execute(self, context):
        if not context.scene.clean_render_hide_overlays:
            try:
                bpy.ops.render.opengl('INVOKE_DEFAULT', view_context=True)
                return {'FINISHED'}
            except Exception as e:
                self.report({'ERROR'}, f"렌더링 실패: {str(e)}")
                return {'CANCELLED'}

        space = get_view3d_space(context)
        if not space:
            self.report({'WARNING'}, "3D 뷰포트를 찾을 수 없습니다.")
            return {'CANCELLED'}

        original_overlay_state = space.overlay.show_overlays

        try:
            space.overlay.show_overlays = False
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
            bpy.ops.render.opengl('INVOKE_DEFAULT', view_context=True)
        except Exception as e:
            self.report({'ERROR'}, f"렌더링 실패: {str(e)}")
            return {'CANCELLED'}
        finally:
            def restore_overlay():
                if space:
                    space.overlay.show_overlays = original_overlay_state
                return None

            bpy.app.timers.register(restore_overlay, first_interval=0.1)

        return {'FINISHED'}

class MODIFIER_PIE_OT_reset_bg_to_theme(bpy.types.Operator):
    """뷰포트 배경을 기본 테마색으로 되돌립니다"""
    bl_idname = "modifier_pie.reset_bg_to_theme"
    bl_label = "배경색"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        space = get_view3d_space(context)
        if space:
            sid = get_space_id(space)
            
            space.shading.background_type = 'THEME'
            save_background_state(sid, 'THEME')
            
            return {'FINISHED'}
        
        self.report({'WARNING'}, "3D 뷰포트를 찾을 수 없습니다.")
        return {'CANCELLED'}

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

        row = layout.row(align=True)
        row.operator(MODIFIER_PIE_OT_reset_bg_to_theme.bl_idname, text="테마색")
        row.prop(context.scene, "clean_view_bg_color", text="")

        row2 = layout.row(align=True)
        row2.operator("modifier_pie.toggle_wire", text="와이어", icon="SHADING_WIRE", depress=state["show_cleanview_wire_toggle"])
        row2.operator("modifier_pie.toggle_lineart", text="라인아트", icon="MOD_LINEART", depress=state["show_cleanview_lineart_toggle"])

        layout.separator()

        row3 = layout.row(align=True)
        row3.prop(context.scene.render, "film_transparent", text="배경 투명화")
        row3.prop(context.scene, "clean_render_hide_overlays", text="클린 렌더")

# 빈 draw handler (이벤트 기반이므로 불필요)
def draw_handler():
    pass

classes = [
    MODIFIER_PIE_OT_viewport_render_image,
    MODIFIER_PIE_OT_reset_bg_to_theme,
    MODIFIER_PIE_OT_toggle_wire,
    MODIFIER_PIE_OT_toggle_lineart,
    MODIFIER_PIE_PT_clean_view_panel,
    MODIFIER_PIE_OT_fullscreen_key_listener,
]

def register():
    bpy.types.Scene.clean_view_bg_color = bpy.props.FloatVectorProperty(
        name="배경색",
        subtype='COLOR',
        size=3,
        default=(1.0, 1.0, 1.0),
        min=0.0,
        max=1.0,
        update=update_clean_bg
    )

    bpy.types.Scene.clean_render_hide_overlays = bpy.props.BoolProperty(
        name="렌더 시 오버레이 숨김",
        description="뷰포트 렌더 시에만 일시적으로 오버레이를 끕니다",
        default=False
    )

    for cls in classes:
        bpy.utils.register_class(cls)

    try:
        if bpy.context and bpy.context.scene and hasattr(bpy.context.scene, 'view_settings'):
            bpy.context.scene.view_settings.view_transform = 'Standard'
    except Exception as e:
        print(f"뷰 변환 기본값 설정 실패: {e}")

    global _draw_handle, _modal_operator
    if _draw_handle:
        bpy.types.SpaceView3D.draw_handler_remove(_draw_handle, 'WINDOW')
    
    _draw_handle = bpy.types.SpaceView3D.draw_handler_add(draw_handler, (), 'WINDOW', 'POST_PIXEL')
    
    # Modal operator 시작 (키 감지용)
    try:
        bpy.ops.modifier_pie.fullscreen_key_listener('INVOKE_DEFAULT')
        print("이벤트 기반 화면 전환 감지 시작됨")
    except:
        pass

def unregister():
    global _draw_handle, _modal_operator
    if _draw_handle:
        bpy.types.SpaceView3D.draw_handler_remove(_draw_handle, 'WINDOW')
        _draw_handle = None

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    if hasattr(bpy.types.Scene, "clean_render_hide_overlays"):
        del bpy.types.Scene.clean_render_hide_overlays
    if hasattr(bpy.types.Scene, "clean_view_bg_color"):
        del bpy.types.Scene.clean_view_bg_color

    _viewport_states.clear()

if __name__ == "__main__":
    register()
