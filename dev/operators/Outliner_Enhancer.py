import bpy
from bpy.app.handlers import persistent

_owner_id = object()
_previous_active = None

def focus_on_active_object():
    """
    아웃라이너에서 현재 활성 오브젝트에 포커스를 맞춥니다.
    """
    outliner_area = None
    for area in bpy.context.screen.areas:
        if area.type == 'OUTLINER':
            outliner_area = area
            break

    if outliner_area is None: return

    outliner_region = None
    for region in outliner_area.regions:
        if region.type == 'WINDOW':
            outliner_region = region
            break
            
    if outliner_region is None: return

    with bpy.context.temp_override(area=outliner_area, region=outliner_region):
        bpy.ops.outliner.show_active()

def on_active_object_change(*args):
    """
    활성 오브젝트가 변경되었을 때 호출되는 메인 핸들러 함수입니다.
    """
    global _previous_active
    
    # 간혹 컨텍스트가 없는 경우가 있어 안전장치 추가
    if not hasattr(bpy.context, "active_object"):
        return
        
    active_obj = bpy.context.active_object
    
    if not active_obj or active_obj == _previous_active:
        return
        
    _previous_active = active_obj
    focus_on_active_object()


# --- 콜렉션 정리 및 닫기 기능을 위한 로직 ---

def collapse_all_hierarchies():
    """모든 하이라키를 효율적으로 축소"""
    try:
        for _ in range(10):
            bpy.ops.outliner.show_one_level(open=False)
    except RuntimeError:
        pass

COLLECTION_MAP = {
    'CAMERA': "Cameras", 'LIGHT': "Lighting", 'EMPTY_IMAGE': "Images", 'LINEART': "LineArt",
}

def ensure_collection(name):
    if name not in bpy.data.collections:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
        if name == COLLECTION_MAP['CAMERA']:
            col.color_tag = 'COLOR_01'
        col["auto_sort_generated"] = True
    return bpy.data.collections[name]

def move_to_collection(obj, target_coll_name):
    try:
        target_coll = ensure_collection(target_coll_name)
        for coll in list(obj.users_collection):
            coll.objects.unlink(obj)
        target_coll.objects.link(obj)
    except Exception as e: print(f"[Outliner Enhancer] Move error: {e}")

def is_lineart_object(obj):
    try:
        if "lineart" in obj.name.lower() or "라인아트" in obj.name.lower(): return True
        if obj.type == 'GPENCIL' and any(mod.type == 'LINEART' for mod in obj.grease_pencil_modifiers): return True
        return False
    except: return False

def is_image_empty(obj):
    try:
        return obj.type == 'EMPTY' and obj.empty_display_type == 'IMAGE' and obj.data is not None
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
        for obj in bpy.context.scene.objects: auto_sort_new_object(obj)
        move_collections_to_ordered_positions()
        remove_empty_collections()
    except Exception as e: print(f"[Outliner Enhancer] Sort all error: {e}")

def move_collections_to_ordered_positions():
    try:
        scene_col = bpy.context.scene.collection
        order = [COLLECTION_MAP['CAMERA'], COLLECTION_MAP['LIGHT'], COLLECTION_MAP['EMPTY_IMAGE'], COLLECTION_MAP['LINEART']]
        existing = [scene_col.children.get(name) for name in order if scene_col.children.get(name)]
        for col in existing: scene_col.children.unlink(col)
        for col in existing: scene_col.children.link(col)
    except Exception as e: print(f"[Outliner Enhancer] Reorder error: {e}")

def remove_empty_collections():
    try:
        for coll in list(bpy.data.collections):
            is_our_addon_coll = coll.get("auto_sort_generated")
            is_sketchup_coll = coll.name.startswith("SKP ")
            if (not coll.objects and not coll.children and coll.name != "Collection" and (is_our_addon_coll or is_sketchup_coll) and coll.users <= 1):
                bpy.data.collections.remove(coll)
    except Exception as e: print(f"[Outliner Enhancer] Remove empty error: {e}")


# --- Operators ---

class OUTLINER_ENHANCER_OT_sort_all(bpy.types.Operator):
    bl_idname = "outliner_enhancer.sort_all"
    bl_label = "컬렉션 정리"
    bl_description = "아웃라이너의 항목(카메라, 조명, 라인아트, 이미지)를 정렬합니다"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        sort_all_objects()
        self.report({'INFO'}, "콜렉션 정리 완료")
        return {'FINISHED'}

class OUTLINER_ENHANCER_OT_collapse_all(bpy.types.Operator):
    bl_idname = "outliner_enhancer.collapse_all"
    bl_label =  "컬렉션 닫기"
    bl_description = "아웃라이너의 모든 계층을 접습니다"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for area in context.screen.areas:
            if area.type == 'OUTLINER':
                outliner_region = next((r for r in area.regions if r.type == 'WINDOW'), None)
                if outliner_region:
                    with context.temp_override(area=area, region=outliner_region):
                        collapse_all_hierarchies()
                    break
        return {'FINISHED'}


# --- UI and Registration ---

def custom_outliner_buttons_draw(self, context):
    layout = self.layout
    row = layout.row(align=True)
    row.operator("outliner_enhancer.sort_all", text="", icon='FILE_REFRESH')
    row.operator("outliner_enhancer.collapse_all", text="", icon='TRIA_UP_BAR')
    layout.separator(factor=0.1)

classes = (
    OUTLINER_ENHANCER_OT_sort_all,
    OUTLINER_ENHANCER_OT_collapse_all,
)

# ▼▼▼ 이 부분이 수정되었습니다 ▼▼▼

# 이 함수는 새 파일이 열릴 때마다 자동으로 호출됩니다.
# @persistent 데코레이터는 이 핸들러가 블렌더에 의해 자동으로 제거되지 않도록 보장합니다.
@persistent
def reinitialize_handler(dummy):
    global _previous_active
    _previous_active = None
    
    # 이전에 등록된 핸들러가 있다면 안전하게 제거합니다.
    bpy.msgbus.clear_by_owner(_owner_id)
    
    # 핸들러를 새로 등록합니다.
    subscribe_to = (bpy.types.LayerObjects, "active")
    bpy.msgbus.subscribe_rna(
        key=subscribe_to,
        owner=_owner_id,
        args=(),
        notify=on_active_object_change,
    )
    print("[Outliner Enhancer] Auto-focus handler re-initialized for new file.")

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.OUTLINER_HT_header.prepend(custom_outliner_buttons_draw)
    
    # load_post 핸들러 리스트에 우리의 재초기화 함수를 추가합니다.
    if reinitialize_handler not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(reinitialize_handler)
    
    # 현재 세션을 위해 한 번 실행합니다.
    reinitialize_handler(None)
    
    print("[Outliner Enhancer] 애드온이 등록되었습니다.")

def unregister():
    # 구독을 해제합니다.
    bpy.msgbus.clear_by_owner(_owner_id)

    # load_post 핸들러 리스트에서 재초기화 함수를 제거합니다.
    if reinitialize_handler in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(reinitialize_handler)

    bpy.types.OUTLINER_HT_header.remove(custom_outliner_buttons_draw)
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
        
    print("[Outliner Enhancer] 애드온이 해제되었습니다.")

if __name__ == "__main__":
    register()
