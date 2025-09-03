import bpy
from bpy.props import StringProperty, BoolProperty, FloatProperty, IntProperty, EnumProperty
from bpy.types import AddonPreferences, Operator
import urllib.request
import zipfile
import os
import shutil
import threading
import sys
import time
import blf
import gpu
from bpy.app.handlers import persistent

# --- GitHub 정보 ---
GITHUB_USER = "art2coder"
GITHUB_REPO = "modifier_pie_kit"

# --- 전역 상태 변수 ---
update_status = {
    "message": "",
    "progress": 0.0,
    "running": False,
    "finished": False,
    "error": None,
}

# --- 헬퍼 함수 ---
def get_addon_version(addon_name):
    if addon_name not in sys.modules: return (0, 0, 0)
    module = sys.modules[addon_name]
    return getattr(module, "bl_info", {}).get("version", (0, 0, 0))

def compare_versions(v1, v2):
    return v1 > v2

def fetch_latest_version_info():
    url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/version.txt"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            latest_version_str = response.read().decode('utf-8').strip()
            return tuple(map(int, latest_version_str.split('.')))
    except Exception as e:
        print(f"Error checking for update: {e}")
        return None

def get_download_url(version_str):
    file_name = f"{GITHUB_REPO}_v{version_str}.zip"
    return f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}/releases/latest/download/{file_name}"

def show_update_error_popup(error_message):
    def draw(self, context):
        self.layout.label(text=f"Update failed. See console for details: {error_message}")
    bpy.context.window_manager.popup_menu(draw, title="Update Error", icon='ERROR')
    return None

def format_progress_bar(progress):
    bar_length = 20
    filled_length = int(bar_length * progress)
    bar = '■' * filled_length + '-' * (bar_length - filled_length)
    return f"[{bar}] {int(progress * 100)}%"



# --- 프로퍼티 및 오퍼레이터 ---
class UpdaterProperties(bpy.types.PropertyGroup):
    update_available: BoolProperty(default=False)
    latest_version: StringProperty(default="")

class MODIFIERPIEKIT_OT_check_for_updates(Operator):
    bl_idname = "modifierpiekit.check_for_updates"
    bl_label = "업데이트 확인"
    def execute(self, context):
        updater_props = context.scene.modifier_pie_kit_updater
        latest_version = fetch_latest_version_info()
        if latest_version:
            current_version = get_addon_version(GITHUB_REPO)
            if compare_versions(latest_version, current_version):
                updater_props.update_available = True
                updater_props.latest_version = ".".join(map(str, latest_version))
                self.report({'INFO'}, f"새로운 버전이 있습니다: {updater_props.latest_version}")
            else:
                updater_props.update_available = False
                self.report({'INFO'}, "현재 사용 중인 버전이 최신 버전입니다.")
        else:
            self.report({'ERROR'}, "업데이트를 확인할 수 없습니다. 인터넷 연결을 확인하세요.")
        return {'FINISHED'}
    
class MODIFIERPIEKIT_OT_show_update_complete_messages(Operator):
    bl_idname = "modifierpiekit.show_update_complete_messages"
    bl_label = "Show Update Complete Messages"
    
    def execute(self, context):
        # 즉시 설치 완료 메시지 표시
        context.workspace.status_text_set_internal("업데이트 완료!")
        print("설치 완료 메시지 표시")
        
        # 2초 후에 재시작 메시지로 변경하는 타이머 등록
        def switch_to_restart_message():
            try:
                bpy.context.workspace.status_text_set_internal("업데이트 완료! 적용을 위해 블렌더를 재시작하세요.")
                print("재시작 메시지로 전환 완료")
            except:
                pass
            return None  # 타이머 종료
            
        bpy.app.timers.register(switch_to_restart_message, first_interval=2.0)
        
        return {'FINISHED'}

class MODIFIERPIEKIT_OT_install_update(Operator):
    bl_idname = "modifierpiekit.install_update"
    bl_label = "지금 설치"
    
    _thread = None
    _timer = None

    def install_thread_task(self, latest_version_str):  # 클래스 내부로 이동
        global update_status
        
        try:
            update_status["message"] = "다운로드 중..."
            update_status["progress"] = 0.0
            
            download_url = get_download_url(latest_version_str)
            addons_path = bpy.utils.script_path_user() + "/addons/"
            zip_file_name = f"{GITHUB_REPO}_v{latest_version_str}.zip"
            zip_path = os.path.join(addons_path, zip_file_name)

            # 다운로드 진행률 표시
            with urllib.request.urlopen(download_url) as response, open(zip_path, 'wb') as out_file:
                total_size = int(response.info().get('Content-Length', 0))
                downloaded_size = 0
                chunk_size = 8192

                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    
                    out_file.write(chunk)
                    downloaded_size += len(chunk)
                    
                    if total_size > 0:
                        update_status["progress"] = downloaded_size / total_size

            update_status["message"] = "설치 중..."
            update_status["progress"] = 1.0

            # 기존 addon 디렉토리 제거
            addon_path = os.path.join(addons_path, GITHUB_REPO)
            if os.path.exists(addon_path):
                shutil.rmtree(addon_path)

            # 압축 해제
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(addons_path)

            # 임시 파일 삭제
            os.remove(zip_path)

            update_status["message"] = "설치 성공"

        except Exception as e:
            print(f"Update failed: {e}")
            update_status["error"] = str(e)
        finally:
            update_status["finished"] = True
            update_status["running"] = False

    def modal(self, context, event):
        global update_status

        if event.type == 'TIMER':
            if update_status["finished"]:
                # 타이머 제거
                if self._timer:
                    context.window_manager.event_timer_remove(self._timer)

                if update_status["error"]:
                    context.workspace.status_text_set_internal(None)
                    show_update_error_popup(update_status["error"])
                else:
                    # 성공 시 하단 상태 표시줄에 "설치 완료!" 메시지 표시
                    bpy.ops.modifierpiekit.show_update_complete_messages()

                return {'FINISHED'}
            
            else:
                # 하단 상태 표시줄에 진행률 표시
                progress_bar = format_progress_bar(update_status['progress'])
                status_text = f"{update_status['message']} {progress_bar}"
                context.workspace.status_text_set_internal(status_text)

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        global update_status

        if update_status["running"]:
            self.report({'WARNING'}, "Update is already in progress.")
            return {'CANCELLED'}

        # 상태 초기화
        update_status.update({
            "running": True,
            "finished": False,
            "error": None,
            "message": "",
            "progress": 0.0
        })

        self.report({'INFO'}, "업데이트를 시작합니다...")

        updater_props = context.scene.modifier_pie_kit_updater
        
        # 백그라운드 스레드에서 다운로드 시작 (이제 정상 동작함)
        self._thread = threading.Thread(
            target=self.install_thread_task, 
            args=(updater_props.latest_version,)
        )
        self._thread.start()

        # 타이머 등록
        self._timer = context.window_manager.event_timer_add(0.1, window=context.window)
        context.window_manager.modal_handler_add(self)
        
        return {'RUNNING_MODAL'}


# --- 기존 환경설정 UI 및 로직 ---
def update_outliner_focus_handler(self, context):
    if hasattr(bpy.types.Scene, "outliner_enhancer_reinit_handler"):
        bpy.types.Scene.outliner_enhancer_reinit_handler(self.use_outliner_auto_focus)

def update_resolution_on_toggle(self, context):
    if not context.scene: return
    try:
        module = getattr(__import__("__main__"), "camera_quick_settings")
        apply_resolution = getattr(module, "apply_camera_resolution")
    except (ImportError, AttributeError): apply_resolution = None
    if self.use_custom_camera_resolution:
        if apply_resolution: apply_resolution(context.scene)
    else:
        context.scene.render.resolution_x = 1920
        context.scene.render.resolution_y = 1080

def get_icon_size_preset(self):
    val = self.icon_size
    if val < 1.15: return 0
    elif val < 1.25: return 1
    else: return 2

def set_icon_size_preset(self, value):
    if value == 0: self.icon_size = 1.1
    elif value == 1: self.icon_size = 1.2
    else: self.icon_size = 1.3

class WM_OT_capture_key(Operator):
    bl_idname = "wm.capture_key"; bl_label = "Press a key..."
    key_type: StringProperty()
    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        self.report({'INFO'}, "원하는 키 조합을 누르세요 (ESC 취소)")
        return {'RUNNING_MODAL'}
    def modal(self, context, event):
        if event.type == 'ESC': return {'CANCELLED'}
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

class ModifierPiePreferences(AddonPreferences):
    bl_idname = "modifier_pie_kit"
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
    icon_size: FloatProperty(name="아이콘 크기", default=1.2, min=0.5, max=2.0)    
    icon_size_preset: EnumProperty(name="아이콘 크기", items=[('SMALL', "작게", ""), ('MEDIUM', "중간", ""), ('LARGE', "크게", "")], get=get_icon_size_preset, set=set_icon_size_preset)
    show_text: BoolProperty(name="아이콘 이름 표시", default=False)
    use_custom_camera_resolution: BoolProperty(name="커스텀 카메라 해상도 사용", default=True, update=update_resolution_on_toggle)
    min_resolution: IntProperty(name="최소 해상도", default=1000, min=1, max=1000)
    max_resolution: IntProperty(name="최대 해상도", default=15000, min=1920, max=50000)
    default_width: IntProperty(name="기본 가로 해상도", default=3272, min=1080, max=20000)
    default_height: IntProperty(name="기본 세로 해상도", default=1600, min=16, max=20000)
    use_collection_sorting: BoolProperty(name="컬렉션 정리 사용", default=True)
    use_outliner_auto_focus: BoolProperty(name="아웃라이너 포커스 사용", default=True, update=update_outliner_focus_handler)
    ui_keymap_expanded: BoolProperty(name="키 설정", default=True)
    ui_display_expanded: BoolProperty(name="파이 메뉴", default=True)
    ui_camera_expanded: BoolProperty(name="카메라 해상도", default=True)
    ui_outliner_expanded: BoolProperty(name="아웃라이너", default=True)
    ui_updater_expanded: BoolProperty(name="업데이트", default=True)
    def draw(self, context):
        layout = self.layout
        main_row = layout.row(); main_row.column()
        center_col = main_row.column(align=True); center_col.scale_x = 1.2
        main_row.column()
        row = center_col.row(align=True)
        icon = 'TRIA_DOWN' if self.ui_updater_expanded else 'TRIA_RIGHT'
        row.prop(self, "ui_updater_expanded", text="", icon=icon, emboss=False)
        row.label(text="업데이트")
        if self.ui_updater_expanded:
            updater_props = context.scene.modifier_pie_kit_updater
            col = center_col.column(align=True)
            button_row = col.row(align=True)
            button_row.split(factor=0.85)
            button_row.operator("modifierpiekit.check_for_updates", text="업데이트 확인", icon='URL')
            if updater_props.update_available:
                row = col.row(align=True)
                row.label(text=f"새 버전이 있습니다: {updater_props.latest_version}", icon='INFO')
                row.operator("modifierpiekit.install_update", text="지금 설치", icon='URL')
        center_col.separator(factor=3)
        row = center_col.row(align=True)
        icon = 'TRIA_DOWN' if self.ui_keymap_expanded else 'TRIA_RIGHT'
        row.prop(self, "ui_keymap_expanded", text="", icon=icon, emboss=False)
        row.label(text="키 설정")
        if self.ui_keymap_expanded:
            col = center_col.column(align=True)
            def get_key_text(prefs, key_type):
                key = getattr(prefs, f"{key_type}_key", ""); ctrl = getattr(prefs, f"{key_type}_ctrl", False)
                shift = getattr(prefs, f"{key_type}_shift", False); alt = getattr(prefs, f"{key_type}_alt", False)
                text = [];
                if ctrl: text.append("Ctrl")
                if shift: text.append("Shift")
                if alt: text.append("Alt")
                text.append(key)
                return " + ".join(text)
            row = col.row(align=True); split = row.split(factor=0.5); split.alignment = 'RIGHT'; split.label(text="그룹"); op = split.operator("wm.capture_key", text=get_key_text(self, "grouping")); op.key_type = "grouping"
            row = col.row(align=True); split = row.split(factor=0.5); split.alignment = 'RIGHT'; split.label(text="그룹 해제"); op = split.operator("wm.capture_key", text=get_key_text(self, "ungrouping")); op.key_type = "ungrouping"
            row = col.row(align=True); split = row.split(factor=0.5); split.alignment = 'RIGHT'; split.label(text="파이 메뉴"); op = split.operator("wm.capture_key", text=get_key_text(self, "pie_menu")); op.key_type = "pie_menu"
            row = col.row(align=True); split = row.split(factor=0.5); split.alignment = 'RIGHT'; split.label(text="스마트 셀렉트"); op = split.operator("wm.capture_key", text=get_key_text(self, "smart_select")); op.key_type = "smart_select"
        center_col.separator(factor=3)
        row = center_col.row(align=True)
        icon = 'TRIA_DOWN' if self.ui_display_expanded else 'TRIA_RIGHT'
        row.prop(self, "ui_display_expanded", text="", icon=icon, emboss=False)
        row.label(text="파이 메뉴")
        if self.ui_display_expanded:
            row = center_col.row(align=True); split = row.split(factor=0.5); split.alignment = 'RIGHT'; split.label(text="아이콘 크기"); split.prop(self, "icon_size_preset", text="")
            row = center_col.row(align=True); split = row.split(factor=0.5); split.label(text=""); split.prop(self, "show_text")
        center_col.separator(factor=3)
        row = center_col.row(align=True)
        icon = 'TRIA_DOWN' if self.ui_camera_expanded else 'TRIA_RIGHT'
        row.prop(self, "ui_camera_expanded", text="", icon=icon, emboss=False)
        row.label(text="카메라 해상도")
        if self.ui_camera_expanded:
            row = center_col.row(align=True); split = row.split(factor=0.5); split.label(text=""); split.prop(self, "use_custom_camera_resolution")
            col = center_col.column(align=True); col.enabled = self.use_custom_camera_resolution
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
        center_col.separator(factor=3)

addon_keymaps = []
def update_keymaps():
    unregister_keymaps()
    register_keymaps()
def register_keymaps():
    wm = bpy.context.window_manager; kc = wm.keyconfigs.addon
    if not kc: return
    try: prefs = bpy.context.preferences.addons["modifier_pie_kit"].preferences
    except: return
    keymaps_to_register = [
        {'idname': 'object.group_by_empty', 'type_prop': 'grouping_key', 'ctrl_prop': 'grouping_ctrl', 'shift_prop': 'grouping_shift', 'alt_prop': 'grouping_alt'},
        {'idname': 'object.ungroup_empty', 'type_prop': 'ungrouping_key', 'ctrl_prop': 'ungrouping_ctrl', 'shift_prop': 'ungrouping_shift', 'alt_prop': 'ungrouping_alt'},
        {'idname': 'wm.call_menu_pie', 'type_prop': 'pie_menu_key', 'ctrl_prop': 'pie_menu_ctrl', 'shift_prop': 'pie_menu_shift', 'alt_prop': 'pie_menu_alt', 'properties': [('name', 'PIE_MT_pivot_pie')]},
        {'idname': 'object.smartselect', 'type_prop': 'smart_select_key', 'ctrl_prop': 'smart_select_ctrl', 'shift_prop': 'smart_select_shift', 'alt_prop': 'smart_select_alt'},
    ]
    for km_info in keymaps_to_register:
        key_type = getattr(prefs, km_info['type_prop']); ctrl = getattr(prefs, km_info['ctrl_prop'])
        shift = getattr(prefs, km_info['shift_prop']); alt = getattr(prefs, km_info['alt_prop'])
        for mode_name in ["Object Mode", "Mesh"]:
            if 'smartselect' not in km_info['idname'] and mode_name == 'Mesh' and 'pie' not in km_info['idname'] : continue
            km = kc.keymaps.new(name=mode_name, space_type='EMPTY')
            kmi = km.keymap_items.new(km_info['idname'], type=key_type, value='PRESS', ctrl=ctrl, shift=shift, alt=alt)
            if 'properties' in km_info:
                for prop_name, prop_value in km_info['properties']: setattr(kmi.properties, prop_name, prop_value)
            addon_keymaps.append((km, kmi))
            if 'smartselect' not in km_info['idname'] and 'pie' not in km_info['idname']: break
def unregister_keymaps():
    for km, kmi in addon_keymaps:
        try: km.keymap_items.remove(kmi)
        except: pass
    addon_keymaps.clear()

loaded_handlers = []

@persistent
def on_file_loaded(dummy):    
    print("파일 로드 완료, 키맵을 다시 설정합니다.") # 디버깅용
    update_keymaps()

def register_load_handler():
    """ 핸들러를 등록하고 전역 변수에 저장합니다. """
    if on_file_loaded not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(on_file_loaded)
        loaded_handlers.append(on_file_loaded)    

def unregister_load_handler():
    """ 전역 변수에 저장된 핸들러를 제거합니다. """
    for handler in loaded_handlers:
        if handler in bpy.app.handlers.load_post:
            bpy.app.handlers.load_post.remove(handler)
    loaded_handlers.clear()

classes = (
    WM_OT_capture_key, 
    ModifierPiePreferences,
    UpdaterProperties,
    MODIFIERPIEKIT_OT_check_for_updates,
    MODIFIERPIEKIT_OT_install_update,
    MODIFIERPIEKIT_OT_show_update_complete_messages,    
)

def register():
    for cls in classes: 
        bpy.utils.register_class(cls)
    bpy.types.Scene.modifier_pie_kit_updater = bpy.props.PointerProperty(type=UpdaterProperties)
    
    update_keymaps()
    register_load_handler()    

def unregister():
    
    unregister_load_handler()
    unregister_keymaps()
    for cls in reversed(classes): 
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.modifier_pie_kit_updater
