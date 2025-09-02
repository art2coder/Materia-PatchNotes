bl_info = {
    "name": "카메라 퀵 설정 (UI 개선판)",
    "description": "UI 레이아웃 및 기능이 개선된 버전입니다.",
    "author": "User, Assistant",
    "version": (9, 0, 0), # 버전업
    "blender": (4, 2, 0),
    "location": "3D뷰 > 사이드바 > Extras > 카메라 셋업",
    "category": "Camera"
}

import bpy

# ▼▼▼ 1단계: Getter/Setter 함수 정의 ▼▼▼
# 이 함수들은 프록시 속성과 실제 속성 사이의 값을 주고받는 역할을 합니다.
def get_passepartout_proxy(self):
    """실제 passepartout_alpha 값을 가져와 UI에 보여줍니다."""
    return self.passepartout_alpha

def set_passepartout_proxy(self, value):
    """UI에서 변경된 값을 실제 passepartout_alpha 값에 저장합니다."""
    self.passepartout_alpha = value

# --- 헬퍼 함수 및 핵심 로직 (이전과 동일) ---
def get_addon_prefs():
    try:
        return bpy.context.preferences.addons["modifier_pie_kit"].preferences
    except (AttributeError, KeyError):
        class DummyPrefs:
            use_custom_camera_resolution = True
            min_resolution = 16
            max_resolution = 20000
            default_width = 1920
            default_height = 1080
        return DummyPrefs()

def apply_camera_resolution(scene):
    prefs = get_addon_prefs()
    if not prefs.use_custom_camera_resolution: return
    if not scene: return
    cam_obj = scene.camera
    if cam_obj and cam_obj.type == 'CAMERA':
        res_x = cam_obj.get("resolution_x", prefs.default_width)
        res_y = cam_obj.get("resolution_y", prefs.default_height)
        if scene.render.resolution_x != res_x: scene.render.resolution_x = res_x
        if scene.render.resolution_y != res_y: scene.render.resolution_y = res_y

# --- 오퍼레이터 (이전과 동일) ---
class CAMERA_OT_add_resolution_properties(bpy.types.Operator):
    bl_idname = "camera.add_resolution_properties"
    bl_label = "해상도 속성 추가"
    def execute(self, context):
        cam_obj = context.scene.camera
        if not (cam_obj and cam_obj.type == 'CAMERA'):
            self.report({'WARNING'}, "활성화된 카메라가 없습니다.")
            return {'CANCELLED'}
        prefs = get_addon_prefs()
        if not prefs.use_custom_camera_resolution:
            self.report({'INFO'}, "커스텀 해상도 기능이 비활성화되어 있습니다.")
            return {'CANCELLED'}
        cam_obj["resolution_x"] = prefs.default_width
        cam_obj["resolution_y"] = prefs.default_height
        apply_camera_resolution(context.scene)
        return {'FINISHED'}

class VIEW3D_OT_align_camera_to_view(bpy.types.Operator):
    bl_idname = "view3d.align_camera_to_view"
    bl_label = "새 카메라"
    
    def execute(self, context):        
        bpy.ops.object.camera_add(location=context.scene.cursor.location)
        new_cam_obj = context.active_object    
        context.scene.camera = new_cam_obj
        context.space_data.region_3d.view_perspective = 'PERSP'
        bpy.ops.view3d.camera_to_view()
        context.space_data.lock_camera = False
        
        # 뷰포트 디스플레이 옵션에서 네임을 켜는 코드 추가
        new_cam_obj.data.show_name = True
        
        prefs = get_addon_prefs()
        if prefs.use_custom_camera_resolution:
            new_cam_obj["resolution_x"] = prefs.default_width
            new_cam_obj["resolution_y"] = prefs.default_height
            apply_camera_resolution(context.scene)
            
        return {'FINISHED'}

class VIEW3D_OT_camera_select_prev(bpy.types.Operator):
    bl_idname = "view3d.camera_select_prev"
    bl_label = "이전 카메라"
    def execute(self, context):
        scene, cameras = context.scene, sorted([o for o in context.scene.objects if o.type == 'CAMERA'], key=lambda c: c.name)
        if not cameras: return {'CANCELLED'}
        try:
            idx = (cameras.index(scene.camera) - 1) % len(cameras)
        except (ValueError, IndexError):
            idx = 0
        scene.camera = cameras[idx]
        return {'FINISHED'}

class VIEW3D_OT_camera_select_next(bpy.types.Operator):
    bl_idname = "view3d.camera_select_next"
    bl_label = "다음 카메라"
    def execute(self, context):
        scene, cameras = context.scene, sorted([o for o in context.scene.objects if o.type == 'CAMERA'], key=lambda c: c.name)
        if not cameras: return {'CANCELLED'}
        try:
            idx = (cameras.index(scene.camera) + 1) % len(cameras)
        except (ValueError, IndexError):
            idx = 0
        scene.camera = cameras[idx]
        return {'FINISHED'}

class VIEW3D_OT_camera_view_toggle(bpy.types.Operator):
    bl_idname = "view3d.camera_view_toggle"
    bl_label = "카메라 뷰"
    def execute(self, context):
        is_cam_view = context.space_data.region_3d.view_perspective == 'CAMERA'
        context.space_data.region_3d.view_perspective = 'PERSP' if is_cam_view else 'CAMERA'
        return {'FINISHED'}

class VIEW3D_OT_lock_camera_toggle(bpy.types.Operator):
    bl_idname = "view3d.lock_camera_toggle"
    bl_label = "에임 캠"
    def execute(self, context):
        context.space_data.lock_camera = not context.space_data.lock_camera
        return {'FINISHED'}

# --- UI 패널 (수정된 부분) ---
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
        prefs = get_addon_prefs()

        col = layout.column()
        col.operator("view3d.align_camera_to_view", icon='FILE_NEW')

        row = col.row(align=True)
        row.prop_search(scene, "camera", scene, "objects", text="", icon='CAMERA_DATA')
        row.operator("view3d.camera_select_prev", text="", icon='TRIA_UP')
        row.operator("view3d.camera_select_next", text="", icon='TRIA_DOWN')

        row = col.row(align=True)
        is_camera_view = view.region_3d.view_perspective == 'CAMERA'
        op_text = "뷰 전환" if is_camera_view else "뷰 전환"
        row.operator("view3d.camera_view_toggle", text=op_text)

        sub_row = row.row(align=True)
        sub_row.enabled = is_camera_view
        is_locked = view.lock_camera if is_camera_view else False
        sub_row.alert = is_locked

        button_text = "뷰 고정" if is_locked else "뷰"
        sub_row.operator("view3d.lock_camera_toggle", text=button_text, depress=is_locked)
        

        col.separator()
        col.separator()

        if cam_obj and cam_obj.type == 'CAMERA':
            cam_data = cam_obj.data

            row = col.row(align=True)
            row.prop(cam_data, "angle_unit_custom", text="")
            if cam_data.angle_unit_custom == 'LENS':
                row.prop(cam_data, "lens", text=" ")
            else:
                row.prop(cam_data, "angle", text=" ")

            row = col.row(align=True)
            row.prop(cam_data, "clip_start", text=" ")
            row.prop(cam_data, "clip_end", text=" ")

            col.separator()
            col.separator()

            
            row = col.row(align=True)
            split = row.split(factor=0.7)

            passepartout_row = split.row(align=True)
            passepartout_row.prop(cam_data, "show_passepartout", text="")
            
            slider_part = passepartout_row.row(align=True)
            slider_part.enabled = cam_data.show_passepartout
            # 실제 속성 대신 프록시 속성을 UI에 표시합니다.
            slider_part.prop(cam_data, "passepartout_proxy", text="외부", slider=True)

            split.prop(context.preferences.inputs, "use_mouse_depth_navigate", text="깊이")

            col.separator()

        if prefs.use_custom_camera_resolution:
            col.separator()
            col.label(text="카메라 해상도")

            if cam_obj and cam_obj.type == 'CAMERA':
                if "resolution_x" in cam_obj:
                    row_x = col.row()
                    split_x = row_x.split(factor=0.5)      
                    left_col_x = split_x.column()
                    left_col_x.alignment = 'RIGHT'
                    left_col_x.label(text="가로")
                    sub_row_x = split_x.column().row(align=True)
                    sub_row_x.prop(cam_obj, '["resolution_x"]', text="")
                    
                  
                    row_y = col.row()
                    split_y = row_y.split(factor=0.5)
                    left_col_y = split_y.column()
                    left_col_y.alignment = 'RIGHT'
                    left_col_y.label(text="세로")
                    sub_row_y = split_y.column().row(align=True)
                    sub_row_y.prop(cam_obj, '["resolution_y"]', text="")
                    
                else:
                    col.operator(CAMERA_OT_add_resolution_properties.bl_idname, icon='ADD')
            else:
                col.label(text="카메라를 선택하세요.", icon='CAMERA_DATA')

# --- 핸들러 및 등록/해제 (이전과 동일) ---
temp_res_on_save = None
def initialize_default_camera():
    prefs = get_addon_prefs()
    if not prefs.use_custom_camera_resolution: return
    scene = bpy.context.scene
    if not (scene and scene.camera) or "resolution_x" in scene.camera: return
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
    prefs = get_addon_prefs()
    if not prefs.use_custom_camera_resolution: return
    global temp_res_on_save
    if not hasattr(bpy.context, "scene") or not bpy.context.scene:
        temp_res_on_save = None
        return
    scene = bpy.context.scene
    temp_res_on_save = (scene.render.resolution_x, scene.render.resolution_y)
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
    CAMERA_OT_add_resolution_properties,
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

    bpy.types.Camera.angle_unit_custom = bpy.props.EnumProperty(
        name="단위",
        description="초점거리(Focal Length)와 화각(Field of View) 간 전환",
        items=[('LENS', "초점거리", "밀리미터(mm) 단위의 초점거리 사용"),
               ('FOV', "FOV", "도(°) 단위의 화각 사용")],
        default='LENS'
    )

    # ▼▼▼ 2단계: register 함수에 프록시 속성 등록 ▼▼▼
    bpy.types.Camera.passepartout_proxy = bpy.props.FloatProperty(
        name="외부 영역 프록시",
        description="소수점 정밀도가 제어된 외부 영역 값",
        min=0.0, max=1.0,
        precision=1, # 소수점 한 자리로 정밀도 설정
        get=get_passepartout_proxy,
        set=set_passepartout_proxy
    )

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

    if hasattr(bpy.types.Camera, 'angle_unit_custom'):
        del bpy.types.Camera.angle_unit_custom
    
    # ▼▼▼ 3단계: unregister 함수에 속성 삭제 코드 추가 ▼▼▼
    if hasattr(bpy.types.Camera, 'passepartout_proxy'):
        del bpy.types.Camera.passepartout_proxy

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)