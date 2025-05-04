import bpy
import functools
from bpy.app import version as blender_version

# --- 설정 ---
COLLECTION_MAP = {
    'CAMERA': "Cameras",
    'LIGHT': "Lighting",
    'EMPTY_IMAGE': "Images",
    'LINEART': "LineArt",
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
    existing = [scene_col.children.get(name) for name in order if scene_col.children.get(name)]

    for col in existing:
        if col and col.name in scene_col.children:
            scene_col.children.unlink(col)
    for col in existing:
        if col:
            scene_col.children.link(col)

def remove_empty_collections():
    for coll in list(bpy.data.collections):
        if not coll.objects and not coll.children and coll.name != "Collection":
            if coll.get("auto_sort_generated") and (coll.users == 0 or not coll.library):
                bpy.data.collections.remove(coll)

def is_lineart_object(obj):
    if blender_version >= (4, 3, 0):
        # 이름에 'lineart' 또는 '라인아트' 포함 여부만 검사 (대소문자 무시)
        name = obj.name.lower()
        return "lineart" in name or "라인아트" in name

    # 4.2.9 이하: 기존 방식 유지
    if obj.type != 'GPENCIL':
        return False
    name_check = 'lineart' in obj.name.lower().replace(" ", "") or "라인아트" in obj.name
    mod_check = hasattr(obj.data, 'modifiers') and any(
        m.type == 'LINEART' for m in obj.data.modifiers
    )
    return name_check or mod_check

def is_image_empty(obj):
    if obj.type != 'EMPTY':
        return False
    if obj.empty_display_type != 'IMAGE':
        return False

    if blender_version >= (4, 3, 0):
        try:
            return getattr(obj, 'image', None) is not None
        except AttributeError:
            return False
    else:
        return True

def delayed_sort_object(obj_name, delay=0.3):
    if "lineart" in obj_name.lower() or "라인아트" in obj_name.lower():
        delay = 0.5

    def _do_sort():
        obj = bpy.context.scene.objects.get(obj_name)
        if obj:
            auto_sort_new_object(obj)
        return None

    bpy.app.timers.register(functools.partial(_do_sort), first_interval=delay)

def auto_sort_new_object(obj):
    try:
        if obj.type == 'CAMERA':
            move_to_collection(obj, COLLECTION_MAP['CAMERA'])
        elif obj.type == 'LIGHT':
            move_to_collection(obj, COLLECTION_MAP['LIGHT'])
        elif is_image_empty(obj):
            move_to_collection(obj, COLLECTION_MAP['EMPTY_IMAGE'])
        elif is_lineart_object(obj):
            move_to_collection(obj, COLLECTION_MAP['LINEART'])
        elif obj.type in ROOT_TYPES:
            for coll in obj.users_collection:
                coll.objects.unlink(obj)
            bpy.context.scene.collection.objects.link(obj)
    except Exception as e:
        print(f"[Collection Sorter] 정리 중 예외 발생: {e}")

def sort_all():
    for obj in bpy.context.scene.objects:
        auto_sort_new_object(obj)
    move_collections_to_ordered_positions()
    remove_empty_collections()

def depsgraph_handler(scene):
    global auto_sort_ignore_list
    try:
        depsgraph = bpy.context.evaluated_depsgraph_get()
        last_objs = getattr(depsgraph_handler, '_last_objs', set())
        current_objs = {getattr(obj.original, "name", obj.name) for obj in depsgraph.objects}
        new_objs = current_objs - last_objs
        new_count = len(new_objs)
        if new_count > 100:
            print(f"[Collection Sorter] 새로 생성된 오브젝트 수가 너무 많아 자동 정리를 일시 중지합니다 ({new_count}개)")
            return
        for i, obj_name in enumerate(sorted(new_objs)):
            if obj_name in auto_sort_ignore_list:
                continue
            obj = bpy.context.scene.objects.get(obj_name)
            if obj and obj.type in {'CAMERA', 'LIGHT'}:
                auto_sort_new_object(obj)
            else:
                delayed_sort_object(obj_name)
            if new_count > 10:
                percent = int((i + 1) / new_count * 100)
                print(f"[Collection Sorter] 정리 중... {percent}%")
        move_collections_to_ordered_positions()
        remove_empty_collections()
        depsgraph_handler._last_objs = current_objs
    except Exception as e:
        print(f"[Collection Sorter] 오류 발생: {e}")

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
    if hasattr(bpy.context.scene, "enable_auto_sort"):
        bpy.context.scene.enable_auto_sort = False

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
