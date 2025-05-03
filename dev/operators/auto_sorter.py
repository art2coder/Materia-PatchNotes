import bpy

# --- 설정 ---
COLLECTION_MAP = {
    'CAMERA': "Cameras",
    'LIGHT': "Lighting",
    'EMPTY_IMAGE': "Images",
    'GPENCIL_LINEART': "LineArt",
}

ROOT_TYPES = {'MESH', 'CURVE', 'SURFACE', 'FONT', 'EMPTY'}

# --- 상태 저장용 전역 변수 ---
auto_sort_ignore_list = set()

# --- 유틸리티 함수 ---
def ensure_collection(name):
    if name not in bpy.data.collections:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
        col["auto_sort_generated"] = True
    return bpy.data.collections[name]

def move_to_collection(obj, target_coll_name):
    target_coll = ensure_collection(target_coll_name)
    for coll in obj.users_collection:
        coll.objects.unlink(obj)
    target_coll.objects.link(obj)

def remove_empty_collections():
    for coll in list(bpy.data.collections):
        if not coll.objects and not coll.children and coll.name != "Collection":
            if coll.get("auto_sort_generated") and (coll.users == 0 or not coll.library):
                bpy.data.collections.remove(coll)

# --- 자동 소팅 처리 ---
def auto_sort_new_object(obj):
    if obj.type == 'CAMERA':
        move_to_collection(obj, COLLECTION_MAP['CAMERA'])
    elif obj.type == 'LIGHT':
        move_to_collection(obj, COLLECTION_MAP['LIGHT'])
    elif obj.type == 'EMPTY' and obj.empty_display_type == 'IMAGE':
        move_to_collection(obj, COLLECTION_MAP['EMPTY_IMAGE'])
    elif obj.type == 'GPENCIL':
        if 'lineart' in obj.name.lower().replace(" ", ""):
            move_to_collection(obj, COLLECTION_MAP['GPENCIL_LINEART'])
    elif obj.type in ROOT_TYPES:
        for coll in obj.users_collection:
            coll.objects.unlink(obj)
        bpy.context.scene.collection.objects.link(obj)

# --- 전체 소팅 기능 ---
def sort_all():
    for obj in bpy.context.scene.objects:
        if obj.type in {'CAMERA', 'LIGHT', 'EMPTY'}:
            auto_sort_new_object(obj)

    remove_empty_collections()

# --- 핸들러 ---
def depsgraph_handler(scene):
    global auto_sort_ignore_list

    try:
        last_objs = getattr(depsgraph_handler, '_last_objs', set())
        current_objs = {obj.name for obj in scene.objects}
        new_objs = current_objs - last_objs

        new_count = len(new_objs)
        if new_count > 100:
            print(f"[Auto Sorter] 새로 생성된 오브젝트 수가 너무 많아 자동 소팅을 일시 중지합니다 ({new_count}개)")
            return

        for i, obj_name in enumerate(sorted(new_objs)):
            if obj_name in auto_sort_ignore_list:
                continue

            obj = scene.objects.get(obj_name)
            if obj:
                auto_sort_new_object(obj)

            if new_count > 10:
                percent = int((i + 1) / new_count * 100)
                print(f"[Auto Sorter] 소팅 중... {percent}%")

        remove_empty_collections()
        depsgraph_handler._last_objs = current_objs

    except Exception as e:
        print(f"[Auto Sorter] 오류 발생: {e}")

# --- UI: N 패널 토글 ---
class AUTO_SORTER_PT_panel(bpy.types.Panel):
    bl_label = "Auto Sorter"
    bl_idname = "AUTO_SORTER_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "정리"

    def draw(self, context):
        layout = self.layout
        if context.scene.enable_auto_sort:
            layout.label(text="자동 소팅 활성화됨")
        else:
            layout.label(text="자동 소팅 비활성화됨")
        layout.prop(context.scene, "enable_auto_sort", toggle=True)
        layout.operator("auto_sorter.sort_all", icon="SORTALPHA")

# --- 오퍼레이터 ---
class AUTO_SORTER_OT_sort_all(bpy.types.Operator):
    bl_idname = "auto_sorter.sort_all"
    bl_label = "전체 소팅"
    bl_description = "카메라/라이트/이미지를 전체 정리합니다"

    def execute(self, context):
        sort_all()
        self.report({'INFO'}, "전체 소팅 완료")
        return {'FINISHED'}

# --- 핸들러 토글 함수 ---
def toggle_auto_sort(self, context):
    global auto_sort_ignore_list

    if context.scene.enable_auto_sort:
        if depsgraph_handler not in bpy.app.handlers.depsgraph_update_post:
            bpy.app.handlers.depsgraph_update_post.append(depsgraph_handler)
        depsgraph_handler._last_objs = {obj.name for obj in context.scene.objects}
    else:
        auto_sort_ignore_list = {obj.name for obj in context.scene.objects}
        if depsgraph_handler in bpy.app.handlers.depsgraph_update_post:
            bpy.app.handlers.depsgraph_update_post.remove(depsgraph_handler)

# --- 파일 열 때 자동 소팅 비활성화 ---
def disable_auto_sort_on_file_load(dummy):
    bpy.context.scene.enable_auto_sort = False

# --- 등록 / 해제 ---
classes = [
    AUTO_SORTER_PT_panel,
    AUTO_SORTER_OT_sort_all,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.enable_auto_sort = bpy.props.BoolProperty(
        name="자동 소팅 활성화",
        default=False,
        description="오브젝트가 생성될 때 자동으로 콜렉션에 정리됩니다.",
        update=toggle_auto_sort,
        options={'SKIP_SAVE'}
    )

    bpy.app.handlers.load_post.append(disable_auto_sort_on_file_load)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    if hasattr(bpy.types.Scene, "enable_auto_sort"):
        del bpy.types.Scene.enable_auto_sort

    if depsgraph_handler in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(depsgraph_handler)

    if disable_auto_sort_on_file_load in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(disable_auto_sort_on_file_load)

if __name__ == "__main__":
    register()
