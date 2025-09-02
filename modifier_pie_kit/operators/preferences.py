# 파일 이름: preferences.py

import bpy
from bpy.props import StringProperty, BoolProperty, FloatProperty, IntProperty, EnumProperty
from bpy.types import AddonPreferences, Operator

# --- 콜백 함수 (기능 로직) ---
def update_outliner_focus_handler(self, context):
    if hasattr(bpy.types.Scene, "outliner_enhancer_reinit_handler"):
        reinit_func = bpy.types.Scene.outliner_enhancer_reinit_handler
        reinit_func(self.use_outliner_auto_focus)
    else:
        print("[Modifier Pie Kit] Outliner_Enhancer의 핸들러 함수를 찾을 수 없습니다.")

def update_resolution_on_toggle(self, context):
    if not context.scene: return
    try:
        module = getattr(__import__("__main__"), "camera_quick_settings")
        apply_resolution = getattr(module, "apply_camera_resolution")
    except (ImportError, AttributeError):
        apply_resolution = None
    
    if self.use_custom_camera_resolution:
        if apply_resolution: apply_resolution(context.scene)
    else:
        context.scene.render.resolution_x = 1920
        context.scene.render.resolution_y = 1080

# ▼▼▼ 수정된 부분: 부동소수점 오차를 해결하도록 숫자 비교 로직 변경 ▼▼▼
def get_icon_size_preset(self):
    """현재 float 크기를 읽어 드롭다운 메뉴에 표시될 인덱스를 반환합니다."""
    val = self.icon_size
    # 각 값의 중간값을 경계로 설정하여 오차 방지
    if val < 1.15:
        return 0 # '작게'
    elif val < 1.25:
        return 1 # '중간'
    else:
        return 2 # '크게'

def set_icon_size_preset(self, value):
    """드롭다운에서 선택된 인덱스(value)에 따라 실제 float 크기를 설정합니다."""
    if value == 0:
        self.icon_size = 1.1
    elif value == 1:
        self.icon_size = 1.2
    else:
        self.icon_size = 1.3
# ▲▲▲ 수정 완료 ▲▲▲


# --- 키 입력을 위한 Operator ---
class WM_OT_capture_key(Operator):
    bl_idname = "wm.capture_key"; bl_label = "Press a key..."
    key_type: StringProperty()

    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        self.report({'INFO'}, "원하는 키 조합을 누르세요 (ESC 취소)")
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type == 'ESC':
            return {'CANCELLED'}
        
        is_valid_key = event.type.isalnum() or event.type in {'SPACE', 'LEFT_MOUSE', 'RIGHT_MOUSE', 'MIDDLE_MOUSE'}

        if event.value == 'PRESS' and is_valid_key:
            prefs = context.preferences.addons["modifier_pie_kit"].preferences
            
            setattr(prefs, f"{self.key_type}_key", event.type)
            setattr(prefs, f"{self.key_type}_ctrl", event.ctrl)
            setattr(prefs, f"{self.key_type}_shift", event.shift)
            setattr(prefs, f"{self.key_type}_alt", event.alt)

            self.report({'INFO'}, f"단축키가 설정되었습니다.")
            return {'FINISHED'}

        return {'PASS_THROUGH'}


# --- 메인 환경설정 클래스 ---
class ModifierPiePreferences(AddonPreferences):
    bl_idname = "modifier_pie_kit"
    
    # --- 기능 속성 ---
    grouping_key: StringProperty(name="그룹핑 키", default="G", update=lambda self, context: update_keymaps())
    grouping_ctrl: BoolProperty(name="그룹핑 Ctrl", default=True, update=lambda self, context: update_keymaps())
    grouping_shift: BoolProperty(name="그룹핑 Shift", default=False, update=lambda self, context: update_keymaps())
    grouping_alt: BoolProperty(name="그룹핑 Alt", default=False, update=lambda self, context: update_keymaps())

    ungrouping_key: StringProperty(name="언그룹핑 키", default="G", update=lambda self, context: update_keymaps())
    ungrouping_ctrl: BoolProperty(name="언그룹핑 Ctrl", default=False, update=lambda self, context: update_keymaps())
    ungrouping_shift: BoolProperty(name="언그룹핑 Shift", default=False, update=lambda self, context: update_keymaps())
    ungrouping_alt: BoolProperty(name="언그룹핑 Alt", default=True, update=lambda self, context: update_keymaps())

    pie_menu_key: StringProperty(name="파이메뉴 키", default="SPACE", update=lambda self, context: update_keymaps())
    pie_menu_ctrl: BoolProperty(name="파이메뉴 Ctrl", default=False, update=lambda self, context: update_keymaps())
    pie_menu_shift: BoolProperty(name="파이메뉴 Shift", default=False, update=lambda self, context: update_keymaps())
    pie_menu_alt: BoolProperty(name="파이메뉴 Alt", default=False, update=lambda self, context: update_keymaps())

    smart_select_key: StringProperty(name="스마트 셀렉트 키", default="V", update=lambda self, context: update_keymaps())
    smart_select_ctrl: BoolProperty(name="스마트 셀렉트 Ctrl", default=False, update=lambda self, context: update_keymaps())
    smart_select_shift: BoolProperty(name="스마트 셀렉트 Shift", default=False, update=lambda self, context: update_keymaps())
    smart_select_alt: BoolProperty(name="스마트 셀렉트 Alt", default=False, update=lambda self, context: update_keymaps())

    
    
    # --- 아이콘 크기 ---
    # ▼▼▼ 수정된 부분: 기본값을 1.1로 명확하게 설정 ▼▼▼
    icon_size: FloatProperty(name="아이콘 크기", default=1.2, min=0.5, max=2.0)
    
    icon_size_preset: EnumProperty(
        name="아이콘 크기",
        items=[
            ('SMALL', "작게", "아이콘 크기를 1.1로 설정"),
            ('MEDIUM', "중간", "아이콘 크기를 1.2로 설정"),
            ('LARGE', "크게", "아이콘 크기를 1.3으로 설정"),
        ],
        get=get_icon_size_preset,
        set=set_icon_size_preset
    )

    show_text: BoolProperty(name="아이콘 이름 표시", default=False)
    use_custom_camera_resolution: BoolProperty(name="커스텀 카메라 해상도 사용", default=True, update=update_resolution_on_toggle)
    min_resolution: IntProperty(name="최소 해상도", default=1000, min=1, max=1000)
    max_resolution: IntProperty(name="최대 해상도", default=15000, min=1920, max=50000)
    default_width: IntProperty(name="기본 가로 해상도", default=3272, min=1080, max=20000)
    default_height: IntProperty(name="기본 세로 해상도", default=1600, min=16, max=20000)
    use_collection_sorting: BoolProperty(name="컬렉션 정리 사용", default=True)
    use_outliner_auto_focus: BoolProperty(name="아웃라이너 포커스 사용", default=True, update=update_outliner_focus_handler)

    # --- UI 패널 상태 저장을 위한 속성 ---
    ui_keymap_expanded: BoolProperty(name="키 설정", default=True)
    ui_display_expanded: BoolProperty(name="파이 메뉴", default=True)
    ui_camera_expanded: BoolProperty(name="카메라 해상도", default=True)
    ui_outliner_expanded: BoolProperty(name="아웃라이너", default=True)

    # --- UI를 그리는 메인 함수 ---
    def draw(self, context):
        layout = self.layout
        
        main_row = layout.row()
        main_row.column()
        center_col = main_row.column(align=True)
        center_col.scale_x = 1.2
        main_row.column()
        
        # --- 1. 키맵 설정 패널 ---
        row = center_col.row(align=True)
        icon = 'TRIA_DOWN' if self.ui_keymap_expanded else 'TRIA_RIGHT'
        row.prop(self, "ui_keymap_expanded", text="", icon=icon, emboss=False)
        row.label(text="키 설정")
        
        if self.ui_keymap_expanded:
            col = center_col.column(align=True)
            
            def get_key_text(prefs, key_type):
                key = getattr(prefs, f"{key_type}_key", "")
                ctrl = getattr(prefs, f"{key_type}_ctrl", False)
                shift = getattr(prefs, f"{key_type}_shift", False)
                alt = getattr(prefs, f"{key_type}_alt", False)
                text = []
                if ctrl: text.append("Ctrl")
                if shift: text.append("Shift")
                if alt: text.append("Alt")
                text.append(key)
                return " + ".join(text)

            row = col.row(align=True); split = row.split(factor=0.5); split.alignment = 'RIGHT'; split.label(text="그룹"); op = split.operator("wm.capture_key", text=get_key_text(self, "grouping")); op.key_type = "grouping"
            row = col.row(align=True); split = row.split(factor=0.5); split.alignment = 'RIGHT'; split.label(text="그룹 해제"); op = split.operator("wm.capture_key", text=get_key_text(self, "ungrouping")); op.key_type = "ungrouping"
            row = col.row(align=True); split = row.split(factor=0.5); split.alignment = 'RIGHT'; split.label(text="파이 메뉴"); op = split.operator("wm.capture_key", text=get_key_text(self, "pie_menu")); op.key_type = "pie_menu"
            row = col.row(align=True); split = row.split(factor=0.5); split.alignment = 'RIGHT'; split.label(text="스마트 셀렉트"); op = split.operator("wm.capture_key", text=get_key_text(self, "smart_select")); op.key_type = "smart_select"
            row = center_col.row(align=True); split = row.split(factor=0.5); split.label(text=""); split.prop(self, "override_default")

        center_col.separator(factor=3)

        # --- 2. 파이 메뉴 패널 ---
        row = center_col.row(align=True)
        icon = 'TRIA_DOWN' if self.ui_display_expanded else 'TRIA_RIGHT'
        row.prop(self, "ui_display_expanded", text="", icon=icon, emboss=False)
        row.label(text="파이 메뉴")
        
        if self.ui_display_expanded:
            row = center_col.row(align=True); split = row.split(factor=0.5); split.alignment = 'RIGHT'; split.label(text="아이콘 크기"); split.prop(self, "icon_size_preset", text="")
            row = center_col.row(align=True); split = row.split(factor=0.5); split.label(text=""); split.prop(self, "show_text")

        center_col.separator(factor=3)

        # (이하 다른 패널들은 변경 없음)
        row = center_col.row(align=True)
        icon = 'TRIA_DOWN' if self.ui_camera_expanded else 'TRIA_RIGHT'
        row.prop(self, "ui_camera_expanded", text="", icon=icon, emboss=False)
        row.label(text="카메라 해상도")
        
        if self.ui_camera_expanded:
            row = center_col.row(align=True); split = row.split(factor=0.5); split.label(text=""); split.prop(self, "use_custom_camera_resolution")
            
            col = center_col.column(align=True)
            col.enabled = self.use_custom_camera_resolution
            row = col.row(align=True); split = row.split(factor=0.5); split.alignment = 'RIGHT'; split.label(text="최소 해상도"); split.prop(self, "min_resolution", text="")
            row = col.row(align=True); split = row.split(factor=0.5); split.alignment = 'RIGHT'; split.label(text="최대 해상도"); split.prop(self, "max_resolution", text="")
            row = col.row(align=True); split = row.split(factor=0.5); split.alignment = 'RIGHT'; split.label(text="기본 가로"); split.prop(self, "default_width", text="")
            row = col.row(align=True); split = row.split(factor=0.5); split.alignment = 'RIGHT'; split.label(text="기본 세로"); split.prop(self, "default_height", text="")
            
        center_col.separator(factor=3)

        row = center_col.row(align=True)
        icon = 'TRIA_DOWN' if self.ui_outliner_expanded else 'TRIA_RIGHT'
        row.prop(self, "ui_outliner_expanded", text="", icon=icon, emboss=False)
        row.label(text="아웃라이너")
        
        if self.ui_outliner_expanded:
            row = center_col.row(align=True); split = row.split(factor=0.5); split.label(text=""); split.prop(self, "use_collection_sorting")
            row = center_col.row(align=True); split = row.split(factor=0.5); split.label(text=""); split.prop(self, "use_outliner_auto_focus")

# --- 키맵 등록/해제 로직 ---
addon_keymaps = []
def update_keymaps():
    unregister_keymaps()
    register_keymaps()

def register_keymaps():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if not kc: return
    try:
        prefs = bpy.context.preferences.addons["modifier_pie_kit"].preferences
    except: return

    keymaps_to_register = [
        {'idname': 'object.group_by_empty', 'type_prop': 'grouping_key', 'ctrl_prop': 'grouping_ctrl', 'shift_prop': 'grouping_shift', 'alt_prop': 'grouping_alt'},
        {'idname': 'object.ungroup_empty', 'type_prop': 'ungrouping_key', 'ctrl_prop': 'ungrouping_ctrl', 'shift_prop': 'ungrouping_shift', 'alt_prop': 'ungrouping_alt'},
        {'idname': 'wm.call_menu_pie', 'type_prop': 'pie_menu_key', 'ctrl_prop': 'pie_menu_ctrl', 'shift_prop': 'pie_menu_shift', 'alt_prop': 'pie_menu_alt', 'properties': [('name', 'PIE_MT_pivot_pie')]},
        {'idname': 'object.smartselect', 'type_prop': 'smart_select_key', 'ctrl_prop': 'smart_select_ctrl', 'shift_prop': 'smart_select_shift', 'alt_prop': 'smart_select_alt'},
    ]

    for km_info in keymaps_to_register:
        key_type = getattr(prefs, km_info['type_prop'])
        ctrl = getattr(prefs, km_info['ctrl_prop'])
        shift = getattr(prefs, km_info['shift_prop'])
        alt = getattr(prefs, km_info['alt_prop'])

        for mode_name in ["Object Mode", "Mesh"]:
            if 'smartselect' not in km_info['idname'] and mode_name == 'Mesh' and 'pie' not in km_info['idname'] :
                 continue
            
            km = kc.keymaps.new(name=mode_name, space_type='EMPTY')
            kmi = km.keymap_items.new(km_info['idname'], type=key_type, value='PRESS', ctrl=ctrl, shift=shift, alt=alt)
            
            if 'properties' in km_info:
                for prop_name, prop_value in km_info['properties']:
                    setattr(kmi.properties, prop_name, prop_value)
            
            addon_keymaps.append((km, kmi))
            
            if 'smartselect' not in km_info['idname'] and 'pie' not in km_info['idname']:
                break

def unregister_keymaps():
    for km, kmi in addon_keymaps:
        try:
            km.keymap_items.remove(kmi)
        except:
            pass
    addon_keymaps.clear()

# --- 모듈 등록/해제 ---
classes = (WM_OT_capture_key, ModifierPiePreferences)
def register():
    for cls in classes: bpy.utils.register_class(cls)
    bpy.app.timers.register(lambda: update_keymaps() or None, first_interval=0.1)

def unregister():
    unregister_keymaps()
    for cls in reversed(classes): bpy.utils.unregister_class(cls)