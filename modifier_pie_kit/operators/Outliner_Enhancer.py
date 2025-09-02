# 파일 이름: Outliner_Enhancer.py

import bpy
from bpy.app.handlers import persistent

# --- 전역 변수 ---
_owner_id = object()
_previous_active = None

# --- 자동 포커스 로직 (변경 없음) ---
def focus_on_active_object():
    outliner_area = next((area for area in bpy.context.screen.areas if area.type == 'OUTLINER'), None)
    if not outliner_area: return
    outliner_region = next((region for region in outliner_area.regions if region.type == 'WINDOW'), None)
    if not outliner_region: return
    with bpy.context.temp_override(area=outliner_area, region=outliner_region):
        bpy.ops.outliner.show_active()

def on_active_object_change(*args):
    global _previous_active
    if not hasattr(bpy.context, "active_object"): return
    active_obj = bpy.context.active_object
    if not active_obj or active_obj == _previous_active: return
    _previous_active = active_obj
    focus_on_active_object()

# --- 콜렉션 정리 및 닫기 로직 (변경 없음) ---
def collapse_all_hierarchies():
    try:
        for _ in range(10): bpy.ops.outliner.show_one_level(open=False)
    except RuntimeError: pass
COLLECTION_MAP = {'CAMERA': "Cameras", 'LIGHT': "Lighting", 'EMPTY_IMAGE': "Images", 'LINEART': "LineArt"}
def ensure_collection(name):
    if name not in bpy.data.collections:
        col = bpy.data.collections.new(name); bpy.context.scene.collection.children.link(col)
        if name == COLLECTION_MAP['CAMERA']: col.color_tag = 'COLOR_01'
        col["auto_sort_generated"] = True
    return bpy.data.collections[name]
def move_to_collection(obj, target_coll_name):
    try:
        target_coll = ensure_collection(target_coll_name); [coll.objects.unlink(obj) for coll in list(obj.users_collection)]; target_coll.objects.link(obj)
    except Exception as e: print(f"[Outliner Enhancer] Move error: {e}")
def is_lineart_object(obj):
    try:
        if "lineart" in obj.name.lower() or "라인아트" in obj.name.lower(): return True
        return obj.type == 'GPENCIL' and any(mod.type == 'LINEART' for mod in obj.grease_pencil_modifiers)
    except: return False
def is_image_empty(obj):
    try: return obj.type == 'EMPTY' and obj.empty_display_type == 'IMAGE' and obj.data is not None
    except: return False
def auto_sort_new_object(obj):
    try:
        if obj.type == 'CAMERA': move_to_collection(obj, COLLECTION_MAP['CAMERA'])
        elif obj.type == 'LIGHT': move_to_collection(obj, COLLECTION_MAP['LIGHT'])
        elif is_image_empty(obj): move_to_collection(obj, COLLECTION_MAP['EMPTY_IMAGE'])
        elif is_lineart_object(obj): move_to_collection(obj, COLLECTION_MAP['LINEART'])
    except Exception as e: print(f"[Outliner Enhancer] Sort error: {e}")
def sort_all_objects():
    try:
        [auto_sort_new_object(obj) for obj in bpy.context.scene.objects]; move_collections_to_ordered_positions(); remove_empty_collections()
    except Exception as e: print(f"[Outliner Enhancer] Sort all error: {e}")
def move_collections_to_ordered_positions():
    try:
        scene_col = bpy.context.scene.collection; order = list(COLLECTION_MAP.values()); existing = [scene_col.children.get(n) for n in order if scene_col.children.get(n)]
        for col in existing: scene_col.children.unlink(col); scene_col.children.link(col)
    except Exception as e: print(f"[Outliner Enhancer] Reorder error: {e}")
def remove_empty_collections():
    try:
        for coll in list(bpy.data.collections):
            is_addon_coll = coll.get("auto_sort_generated") or coll.name.startswith("SKP ")
            if not coll.objects and not coll.children and coll.name != "Collection" and is_addon_coll and coll.users <= 1: bpy.data.collections.remove(coll)
    except Exception as e: print(f"[Outliner Enhancer] Remove empty error: {e}")

# --- Operators (변경 없음) ---
class OUTLINER_ENHANCER_OT_sort_all(bpy.types.Operator):
    bl_idname = "outliner_enhancer.sort_all"; bl_label = "컬렉션 정리"; bl_description = "카메라, 조명 등을 지정된 컬렉션으로 자동 정렬합니다"; bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context): sort_all_objects(); self.report({'INFO'}, "콜렉션 정리 완료"); return {'FINISHED'}
class OUTLINER_ENHANCER_OT_collapse_all(bpy.types.Operator):
    bl_idname = "outliner_enhancer.collapse_all"; bl_label = "컬렉션 닫기"; bl_description = "아웃라이너의 모든 계층을 접습니다"; bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        area = next((a for a in context.screen.areas if a.type == 'OUTLINER'), None)
        if area:
            region = next((r for r in area.regions if r.type == 'WINDOW'), None)
            if region:
                with context.temp_override(area=area, region=region): collapse_all_hierarchies()
        return {'FINISHED'}

# --- UI 및 등록/해제 ---
def custom_outliner_buttons_draw(self, context):
    try: prefs = context.preferences.addons["modifier_pie_kit"].preferences
    except (KeyError, AttributeError): return
    layout = self.layout; row = layout.row(align=True)
    if prefs.use_collection_sorting: row.operator("outliner_enhancer.sort_all", text="", icon='SORTSIZE')
    row.operator("outliner_enhancer.collapse_all", text="", icon='TRIA_UP_BAR')
    layout.separator(factor=0.1)

classes = (OUTLINER_ENHANCER_OT_sort_all, OUTLINER_ENHANCER_OT_collapse_all)

# `reinitialize_handler` 함수 자체는 이전과 동일합니다.
@persistent
def reinitialize_handler(is_enabled):
    global _previous_active; _previous_active = None
    bpy.msgbus.clear_by_owner(_owner_id)
    if not isinstance(is_enabled, bool):
        try:
            prefs = bpy.context.preferences.addons["modifier_pie_kit"].preferences
            is_enabled = prefs.use_outliner_auto_focus
        except (KeyError, AttributeError):
            is_enabled = False
    if not is_enabled:
        print("[Outliner Enhancer] 자동 포커스 기능이 비활성화 상태입니다.")
        return
    subscribe_to = (bpy.types.LayerObjects, "active")
    bpy.msgbus.subscribe_rna(key=subscribe_to, owner=_owner_id, args=(), notify=on_active_object_change)
    print("[Outliner Enhancer] 자동 포커스 핸들러가 활성화되었습니다.")

# ▼▼▼ 이 부분이 수정되었습니다 ▼▼▼
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # 다른 파일(preferences.py)에서 이 함수를 쉽게 찾을 수 있도록
    # 블렌더의 Scene 타입에 함수 참조를 저장합니다.
    bpy.types.Scene.outliner_enhancer_reinit_handler = reinitialize_handler
    
    bpy.types.OUTLINER_HT_header.prepend(custom_outliner_buttons_draw)
    if reinitialize_handler not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(reinitialize_handler)
    bpy.app.timers.register(lambda: reinitialize_handler(None), first_interval=0.1)
    print("[Outliner Enhancer] 모듈이 등록되었습니다.")

def unregister():
    bpy.msgbus.clear_by_owner(_owner_id)
    if reinitialize_handler in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(reinitialize_handler)
    bpy.types.OUTLINER_HT_header.remove(custom_outliner_buttons_draw)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
        
    # 애드온이 비활성화될 때 Scene에 저장했던 함수 참조를 깨끗하게 삭제합니다.
    if hasattr(bpy.types.Scene, "outliner_enhancer_reinit_handler"):
        del bpy.types.Scene.outliner_enhancer_reinit_handler
        
    print("[Outliner Enhancer] 모듈이 해제되었습니다.")
# ▲▲▲ 수정 완료 ▲▲▲