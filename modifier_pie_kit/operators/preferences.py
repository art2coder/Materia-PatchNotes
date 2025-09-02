import bpy
from bpy.props import StringProperty, BoolProperty, FloatProperty, EnumProperty, IntProperty
from bpy.types import AddonPreferences, Operator

# 키 캡처용 Modal Operator
class WM_OT_capture_key(Operator):
    bl_idname = "wm.capture_key"
    bl_label = "Press a key..."
    key_type: StringProperty()

    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        self.report({'INFO'}, "아무 키나 누르세요 (ESC 취소)")
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type == 'ESC':
            return {'CANCELLED'}

        if event.value == 'PRESS' and event.type.isalpha():
            prefs = context.preferences.addons["modifier_pie_kit"].preferences
            # 키 타입에 따라 해당 속성 업데이트
            if self.key_type == "grouping":
                prefs.grouping_key = event.type
            elif self.key_type == "ungrouping":
                prefs.ungrouping_key = event.type
            elif self.key_type == "pie_menu":
                prefs.pie_menu_key = event.type
            elif self.key_type == "smart_select":
                prefs.smart_select_key = event.type

            self.report({'INFO'}, f"키가 {event.type}로 설정되었습니다")
            return {'FINISHED'}

        return {'RUNNING_MODAL'}

class ModifierPiePreferences(AddonPreferences):
    bl_idname = "modifier_pie_kit"

    # 키맵 설정
    grouping_key: StringProperty(
        name="그룹핑 키",
        description="Ctrl + 이 키로 그룹핑 실행",
        default="G",
        update=lambda self, context: update_keymaps()
    )
    
    ungrouping_key: StringProperty(
        name="언그룹핑 키",
        description="Alt + 이 키로 언그룹핑 실행",
        default="G",
        update=lambda self, context: update_keymaps()
    )
    
    pie_menu_key: StringProperty(
        name="파이메뉴 키",
        description="파이메뉴 호출 키",
        default="SPACE",
        update=lambda self, context: update_keymaps()
    )
    
    smart_select_key: StringProperty(
        name="스마트 셀렉트 키",
        description="스마트 셀렉트 호출 키",
        default="V",
        update=lambda self, context: update_keymaps()
    )

    # 기존 키 덮어쓰기 옵션
    override_default: BoolProperty(
        name="기본 키 덮어쓰기",
        description="선택한 키의 기본 블렌더 기능을 덮어씁니다",
        default=True,
        update=lambda self, context: update_keymaps()
    )

    # 파이메뉴 설정
    icon_size: FloatProperty(
        name="아이콘 크기",
        description="파이메뉴 아이콘의 스케일 (1.0 = 기본)",
        default=1.1,
        min=0.5,
        max=2.0,
    )
    
    show_text: BoolProperty(
        name="텍스트 표시",
        description="버튼에 텍스트를 표시할지 여부",
        default=True,
    )

    # ★ 새로 추가: 카메라 해상도 설정 ★
    min_resolution: IntProperty(
        name="최소 해상도",
        description="해상도의 최소값",
        default=1000,
        min=1,
        max=1000
    )
    
    max_resolution: IntProperty(
        name="최대 해상도",
        description="해상도의 최대값",
        default=15000,
        min=1920,
        max=50000
    )
    
    default_width: IntProperty(
        name="기본 가로 해상도",
        description="새 카메라 생성 시 기본 가로 해상도",
        default=3272,
        min=1080,
        max=20000
    )
    
    default_height: IntProperty(
        name="기본 세로 해상도",
        description="새 카메라 생성 시 기본 세로 해상도",
        default=1600,
        min=16,
        max=20000
    )

    def draw(self, context):
        layout = self.layout
        
        # 키맵 설정 섹션
        box = layout.box()
        box.label(text="키맵 설정", icon='KEYINGSET')
        
        # 그룹핑 키 설정
        row = box.row()
        op = row.operator("wm.capture_key", text=f"그룹핑 키 설정 (Ctrl+{self.grouping_key})")
        op.key_type = "grouping"
        
        # 언그룹핑 키 설정
        row = box.row()
        op = row.operator("wm.capture_key", text=f"언그룹핑 키 설정 (Alt+{self.ungrouping_key})")
        op.key_type = "ungrouping"
        
        # 파이메뉴 키 설정
        row = box.row()
        op = row.operator("wm.capture_key", text=f"파이메뉴 키 설정 ({self.pie_menu_key})")
        op.key_type = "pie_menu"
        
        # 스마트 셀렉트 키 설정
        row = box.row()
        op = row.operator("wm.capture_key", text=f"스마트 셀렉트 키 설정 ({self.smart_select_key})")
        op.key_type = "smart_select"
        
        # 기본 키 덮어쓰기 옵션
        box.prop(self, "override_default")

        # 파이메뉴 디스플레이 설정 섹션
        box = layout.box()
        box.label(text="파이메뉴 디스플레이 설정", icon='PREFERENCES')
        box.prop(self, "icon_size")
        box.prop(self, "show_text")

        # ★ 새로 추가: 카메라 해상도 설정 섹션 ★
        box = layout.box()
        box.label(text="카메라 해상도 설정", icon='CAMERA_DATA')
        
        col = box.column()
        col.prop(self, "min_resolution")
        col.prop(self, "max_resolution")
        
        col.separator()
        col.prop(self, "default_width")
        col.prop(self, "default_height")
        
        col.separator()
        col.label(text="※ 설정 변경 후 즉시 적용됩니다.", icon='INFO')

# 키맵 업데이트 함수
addon_keymaps = []

def update_keymaps():
    """환경설정이 변경될 때 키맵 재등록"""
    unregister_keymaps()
    register_keymaps()

def register_keymaps():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if not kc:
        return

    try:
        prefs = bpy.context.preferences.addons["modifier_pie_kit"].preferences
        grouping_key = prefs.grouping_key
        ungrouping_key = prefs.ungrouping_key
        pie_menu_key = prefs.pie_menu_key
        smart_select_key = prefs.smart_select_key
        override_default = prefs.override_default
    except:
        # 환경설정을 불러올 수 없는 경우 기본값 사용
        grouping_key = "G"
        ungrouping_key = "G"
        pie_menu_key = "Q"
        smart_select_key = "V"
        override_default = True

    # Object Mode 키맵
    km_obj = kc.keymaps.new(name='Object Mode', space_type='EMPTY')

    # 기본 키 덮어쓰기 (필요시)
    if override_default:
        # 기본 키맵에서 해당 키들 비활성화
        active_kc = bpy.context.window_manager.keyconfigs.active
        active_km = active_kc.keymaps.get('Object Mode')
        if active_km:
            for kmi in active_km.keymap_items:
                # 그룹핑 키 비활성화
                if (kmi.type == grouping_key and kmi.ctrl and not kmi.alt and kmi.active):
                    kmi.active = False
                    addon_keymaps.append((active_km, kmi))
                # 언그룹핑 키 비활성화
                elif (kmi.type == ungrouping_key and kmi.alt and not kmi.ctrl and kmi.active):
                    kmi.active = False
                    addon_keymaps.append((active_km, kmi))
                # 파이메뉴 키 비활성화
                elif (kmi.type == pie_menu_key and not kmi.ctrl and not kmi.alt and kmi.active):
                    kmi.active = False
                    addon_keymaps.append((active_km, kmi))
                # 스마트 셀렉트 키 비활성화
                elif (kmi.type == smart_select_key and not kmi.ctrl and not kmi.alt and kmi.active):
                    kmi.active = False
                    addon_keymaps.append((active_km, kmi))

    # 그룹핑 키맵 등록
    kmi = km_obj.keymap_items.new(
        'object.group_by_empty', type=grouping_key, value='PRESS', ctrl=True, alt=False
    )
    addon_keymaps.append((km_obj, kmi))

    # 언그룹핑 키맵 등록
    kmi = km_obj.keymap_items.new(
        'object.ungroup_empty', type=ungrouping_key, value='PRESS', ctrl=False, alt=True
    )
    addon_keymaps.append((km_obj, kmi))

    # 파이메뉴 키맵 등록
    kmi = km_obj.keymap_items.new(
        'wm.call_menu_pie', type=pie_menu_key, value='PRESS'
    )
    kmi.properties.name = 'PIE_MT_pivot_pie'
    addon_keymaps.append((km_obj, kmi))

    # Mesh Mode에도 파이메뉴 등록
    km_edit = kc.keymaps.new(name='Mesh', space_type='EMPTY')
    kmi = km_edit.keymap_items.new('wm.call_menu_pie', type=pie_menu_key, value='PRESS')
    kmi.properties.name = 'PIE_MT_pivot_pie'
    addon_keymaps.append((km_edit, kmi))

    # 스마트 셀렉트 키맵 등록
    for mode in ["Object Mode", "Mesh"]:
        km = kc.keymaps.new(name=mode, space_type='EMPTY')
        kmi = km.keymap_items.new("object.smartselect", type=smart_select_key, value='PRESS')
        addon_keymaps.append((km, kmi))

def unregister_keymaps():
    """키맵 해제 및 기본 키 복원"""
    for km, kmi in addon_keymaps:
        try:
            if kmi.idname in ["object.group_by_empty", "object.ungroup_empty", "wm.call_menu_pie", "object.smartselect"]:
                km.keymap_items.remove(kmi)
            else:
                kmi.active = True  # 기본 키 복원
        except Exception:
            pass
    addon_keymaps.clear()

# 등록할 클래스들
classes = (
    WM_OT_capture_key,
    ModifierPiePreferences,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.app.timers.register(lambda: register_keymaps() or None, first_interval=0.1)

def unregister():
    unregister_keymaps()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
