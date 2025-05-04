import bpy

# --- 설정 ---
COLLECTION_MAP = {
    'CAMERA': "Cameras",
    'LIGHT': "Lighting",
    'EMPTY_IMAGE': "Images",
    'GPENCIL_LINEART': "LineArt",
}

ROOT_TYPES = {'MESH', 'CURVE', 'SURFACE', 'FONT', 'EMPTY'}

auto_sort_ignore_list = set()

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

def move_collections_to_ordered_positions():
    scene_col = bpy.context.scene.collection
    order = ["Cameras", "Lighting", "Images", "LineArt"]
    existing = [col for col in order if col in bpy.data.collections and bpy.data.collections[col].name in scene_col.children.keys()]

    # 기존 순서를 리스트로 가져오고 재정렬
    sorted_children = list(scene_col.children)
    new_children = []
    for name in existing:
        col = bpy.data.collections[name]
        new_children.append(col)
        sorted_children.remove(col)
    sorted_children = new_children + sorted_children

    # 링크 제거 후 다시 링크
    for col in scene_col.children:
        scene_col.children.unlink(col)
    for col in sorted_children:
        scene_col.children.link(col)

def remove_empty_collections():
    for coll in list(bpy.data.collections):
        if not coll.objects and not coll.children and coll.name != "Collection":
            if coll.get("auto_sort_generated") and (coll.users == 0 or not coll.library):
                bpy.data.collections.remove(coll)

def auto_sort_new_object(obj):
    if obj.type == 'CAMERA':
        move_to_collection(obj, COLLECTION_MAP['CAMERA'])
    elif obj.type == 'LIGHT':
        move_to_collection(obj, COLLECTION_MAP['LIGHT'])
    elif obj.type == 'EMPTY' and obj.empty_display_type == 'IMAGE':
        move_to_collection(obj, COLLECTION_MAP['EMPTY_IMAGE'])
    elif obj.type == 'GPENCIL':
        # LineArt 오브젝트인지 판단
        if 'lineart' in obj.name.lower().replace(" ", "") or any(
            m.type == 'LINEART' for m in getattr(obj, 'grease_pencil_modifiers', [])):
            move_to_collection(obj, COLLECTION_MAP['GPENCIL_LINEART'])
    elif obj.type in ROOT_TYPES:
        for coll in obj.users_collection:
            coll.objects.unlink(obj)
        bpy.context.scene.collection.objects.link(obj)

def sort_all():
    for obj in bpy.context.scene.objects:
        if obj.type in {'CAMERA', 'LIGHT', 'EMPTY', 'GPENCIL'}:
            auto_sort_new_object(obj)
    move_collections_to_ordered_positions()
    remove_empty_collections()

def depsgraph_handler(scene):
    global auto_sort_ignore_list
    try:
        last_objs = getattr(depsgraph_handler, '_last_objs', set())
        current_objs = {obj.name for obj in scene.objects}
        new_objs = current_objs - last_objs
        new_count = len(new_objs)
        if new_count > 100:
            print(f"[Collection Sorter] 새로 생성된 오브젝트 수가 너무 많아 자동 정리를 일시 중지합니다 ({new_count}개)")
            return
        for i, obj_name in enumerate(sorted(new_objs)):
            if obj_name in auto_sort_ignore_list:
                continue
            obj = scene.objects.get(obj_name)
            if obj:
                auto_sort_new_object(obj)
            if new_count > 10:
                percent = int((i + 1) / new_count * 100)
                print(f"[Collection Sorter] 정리 중... {percent}%")
        move_collections_to_ordered_positions()
        remove_empty_collections()
        depsgraph_handler._last_objs = current_objs
    except Exception as e:
        print(f"[Collection Sorter] 오류 발생: {e}")

class COLLECTION_SORTER_PT_panel(bpy.types.Panel):
    bl_label = "컬렉션 정리 도우미"
    bl_idname = "COLLECTION_SORTER_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Extras"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        icon = "PLAY" if scene.enable_auto_sort else "PAUSE"
        row = layout.row(align=True)
        row.prop(scene, "enable_auto_sort", text="자동 정리", toggle=True, icon=icon)

        layout.operator("collection_sorter.sort_all", text="지금 정리하기", icon="FILE_REFRESH")

class COLLECTION_SORTER_OT_sort_all(bpy.types.Operator):
    bl_idname = "collection_sorter.sort_all"
    bl_label = "지금 정리하기"
    bl_description = "카메라, 라이트, 이미지 등을 컬렉션으로 정리합니다"

    def execute(self, context):
        sort_all()
        self.report({'INFO'}, "정리 완료")
        return {'FINISHED'}

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

def disable_auto_sort_on_file_load(dummy):
    bpy.context.scene.enable_auto_sort = False

classes = [
    COLLECTION_SORTER_PT_panel,
    COLLECTION_SORTER_OT_sort_all,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.enable_auto_sort = bpy.props.BoolProperty(
        name="자동 정리",
        default=False,
        description="오브젝트가 생성될 때 자동으로 컬렉션으로 정리됩니다.",
        update=toggle_auto_sort,
        options={'SKIP_SAVE'}
    )
    bpy.app.handlers.load_post.append(disable_auto_sort_on_file_load)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    if hasattr(bpy.types.Scene, "enable_auto_sort"):
        del bpy.types.Scene.enable_auto_sort
    if depsgraph_handler in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(depsgraph_handler)
    if disable_auto_sort_on_file_load in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(disable_auto_sort_on_file_load)

if __name__ == "__main__":
    register()
