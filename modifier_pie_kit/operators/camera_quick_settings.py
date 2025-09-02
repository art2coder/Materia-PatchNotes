bl_info = {
    "name": "카메라 퀵 설정 (완전체 최종판)",
    "description": "모든 UI와 기능, 안정성이 포함된 최종 버전입니다.",
    "author": "User, Assistant",
    "version": (7, 5, 0),
    "blender": (2, 80, 0),
    "location": "3D뷰 > 사이드바 > Extras > 카메라 셋업",
    "category": "Camera"
}

import bpy

# --- 헬퍼 함수 및 핵심 로직 ---
def get_addon_prefs():
    try:
        return bpy.context.preferences.addons["modifier_pie_kit"].preferences
    except (AttributeError, KeyError):
        class DummyPrefs:
            min_resolution = 16; max_resolution = 20000
            default_width = 1920; default_height = 1080
        return DummyPrefs()

def apply_camera_resolution(scene):
    if not scene: return
    cam_obj = scene.camera
    if cam_obj and cam_obj.type == 'CAMERA':
        prefs = get_addon_prefs()
        res_x = cam_obj.get("resolution_x", prefs.default_width)
        res_y = cam_obj.get("resolution_y", prefs.default_height)
        
        if scene.render.resolution_x != res_x:
            scene.render.resolution_x = res_x
        if scene.render.resolution_y != res_y:
            scene.render.resolution_y = res_y

# --- 오퍼레이터 ---
class VIEW3D_OT_align_camera_to_view(bpy.types.Operator):
    bl_idname = "view3d.align_camera_to_view"
    bl_label = "새 카메라"
    def execute(self, context):
        bpy.ops.object.camera_add(location=context.scene.cursor.location)
        new_cam_obj = context.active_object
        context.scene.camera = new_cam_obj
        bpy.ops.view3d.camera_to_view()
        
        context.space_data.lock_camera = False
        
        prefs = get_addon_prefs()
        new_cam_obj["resolution_x"] = prefs.default_width
        new_cam_obj["resolution_y"] = prefs.default_height

        apply_camera_resolution(context.scene)
        return {'FINISHED'}

class VIEW3D_OT_camera_select_prev(bpy.types.Operator):
    bl_idname = "view3d.camera_select_prev"
    bl_label = "이전 카메라"
    def execute(self, context):
        scene = context.scene
        cameras = sorted([obj for obj in scene.objects if obj.type == 'CAMERA'], key=lambda c: c.name)
        if not cameras: return {'CANCELLED'}
        try:
            current_index = cameras.index(scene.camera)
            prev_index = (current_index - 1) % len(cameras)
        except (ValueError, IndexError):
            prev_index = 0
        scene.camera = cameras[prev_index]
        return {'FINISHED'}

class VIEW3D_OT_camera_select_next(bpy.types.Operator):
    bl_idname = "view3d.camera_select_next"
    bl_label = "다음 카메라"
    def execute(self, context):
        scene = context.scene
        cameras = sorted([obj for obj in scene.objects if obj.type == 'CAMERA'], key=lambda c: c.name)
        if not cameras: return {'CANCELLED'}
        try:
            current_index = cameras.index(scene.camera)
            next_index = (current_index + 1) % len(cameras)
        except (ValueError, IndexError):
            next_index = 0
        scene.camera = cameras[next_index]
        return {'FINISHED'}

class VIEW3D_OT_camera_view_toggle(bpy.types.Operator):
    bl_idname = "view3d.camera_view_toggle"
    bl_label = "카메라 뷰"
    def execute(self, context):
        if context.space_data.region_3d.view_perspective == 'CAMERA':
            context.space_data.region_3d.view_perspective = 'PERSP'
        else:
            bpy.ops.view3d.camera_to_view()
        return {'FINISHED'}

class VIEW3D_OT_lock_camera_toggle(bpy.types.Operator):
    bl_idname = "view3d.lock_camera_toggle"
    bl_label = "에임 캠"
    def execute(self, context):
        context.space_data.lock_camera = not context.space_data.lock_camera
        return {'FINISHED'}

# --- UI 패널 ---
class MODIFIER_PIE_PT_camera_quick_settings(bpy.types.Panel):
    bl_label = "카메라 셋업"
    bl_idname = "MODIFIER_PIE_PT_camera_quick_settings"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Extras"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        cam_obj = scene.camera
        view = context.space_data

        col = layout.column()
        col.operator("view3d.align_camera_to_view", icon='FILE_NEW')
        
        row = col.row(align=True)
        row.prop_search(scene, "camera", scene, "objects", text="")
        row.operator("view3d.camera_select_prev", text="", icon='TRIA_UP')
        row.operator("view3d.camera_select_next", text="", icon='TRIA_DOWN')

        is_camera_view = view.region_3d.view_perspective == 'CAMERA'
        op_text = "카메라 뷰 종료" if is_camera_view else "카메라 뷰"
        col.operator("view3d.camera_view_toggle", text=op_text)
        
        row = col.row()
        row.enabled = is_camera_view
        is_locked = view.lock_camera if is_camera_view else False
        row.alert = is_locked
        row.operator("view3d.lock_camera_toggle", text="에임 캠", depress=is_locked)

        col.separator()
        
        # [복구] 카메라 세부 속성 UI
        if cam_obj and cam_obj.type == 'CAMERA':
            cam_data = cam_obj.data
            col.prop(cam_data, "lens", text="초점거리")
            col.prop(cam_data, "clip_start", text="클립 시작")
            col.prop(cam_data, "clip_end", text="클립 종료")
            col.separator()
            row = col.row(align=True)
            row.prop(cam_data, "show_passepartout", text="")
            row.prop(cam_data, "passepartout_alpha", text="외부 영역", slider=True)
            col.separator()

        col.prop(context.preferences.inputs, "use_mouse_depth_navigate", text="깊이")
        col.separator()

        layout.label(text="카메라 해상도:")
        
        if cam_obj and cam_obj.type == 'CAMERA':
            layout.prop(cam_obj, '["resolution_x"]', text="가로")
            layout.prop(cam_obj, '["resolution_y"]', text="세로")
        else:
            layout.label(text="카메라를 선택하세요.")

        layout.separator()
        layout.label(text=f"현재 씬 해상도: {scene.render.resolution_x} x {scene.render.resolution_y}")


# --- 핸들러 및 등록/해제 ---
temp_res_on_save = None

def initialize_default_camera():
    scene = bpy.context.scene
    if not (scene and scene.camera): return
    if "resolution_x" not in scene.camera:
        prefs = get_addon_prefs()
        scene.camera["resolution_x"] = prefs.default_width
        scene.camera["resolution_y"] = prefs.default_height
        apply_camera_resolution(scene)
    return None

@bpy.app.handlers.persistent
def on_depsgraph_update_post(scene, depsgraph):
    if depsgraph.id_type_updated('CAMERA') or depsgraph.id_type_updated('OBJECT'):
        apply_camera_resolution(scene)
        if hasattr(bpy.context, "screen"):
            for window in bpy.context.window_manager.windows:
                for area in window.screen.areas:
                    if area.type == 'VIEW_3D':
                        area.tag_redraw()

@bpy.app.handlers.persistent
def on_save_pre(dummy):
    global temp_res_on_save
    if not hasattr(bpy.context, "scene") or not bpy.context.scene:
        temp_res_on_save = None; return
    scene = bpy.context.scene
    temp_res_on_save = (scene.render.resolution_x, scene.render.resolution_y)
    prefs = get_addon_prefs()
    scene.render.resolution_x = prefs.default_width
    scene.render.resolution_y = prefs.default_height
    if hasattr(bpy.context, "view_layer") and bpy.context.view_layer:
        bpy.context.view_layer.update()

@bpy.app.handlers.persistent
def on_save_post(dummy):
    global temp_res_on_save
    if not hasattr(bpy.context, "scene") or not bpy.context.scene or not temp_res_on_save:
        return
    scene = bpy.context.scene
    scene.render.resolution_x = temp_res_on_save[0]
    scene.render.resolution_y = temp_res_on_save[1]
    temp_res_on_save = None

@bpy.app.handlers.persistent
def on_load_post(dummy):
    bpy.app.timers.register(initialize_default_camera, first_interval=0.1)

classes = (
    VIEW3D_OT_align_camera_to_view,
    VIEW3D_OT_camera_select_prev,
    VIEW3D_OT_camera_select_next,
    VIEW3D_OT_camera_view_toggle,
    VIEW3D_OT_lock_camera_toggle,
    MODIFIER_PIE_PT_camera_quick_settings,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    handlers = [
        (bpy.app.handlers.depsgraph_update_post, on_depsgraph_update_post),
        (bpy.app.handlers.save_pre, on_save_pre),
        (bpy.app.handlers.save_post, on_save_post),
        (bpy.app.handlers.load_post, on_load_post)
    ]
    for handler_list, handler_func in handlers:
        if handler_func not in handler_list:
            handler_list.append(handler_func)
    
    bpy.app.timers.register(initialize_default_camera, first_interval=0)

def unregister():
    handlers = [
        (bpy.app.handlers.depsgraph_update_post, on_depsgraph_update_post),
        (bpy.app.handlers.save_pre, on_save_pre),
        (bpy.app.handlers.save_post, on_save_post),
        (bpy.app.handlers.load_post, on_load_post)
    ]
    for handler_list, handler_func in handlers:
        if handler_func in handler_list:
            handler_list.remove(handler_func)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
