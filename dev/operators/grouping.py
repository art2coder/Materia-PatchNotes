import bpy
from mathutils import Vector

# ─────────────────────────────────────────────
# 1) 그루핑 오퍼레이터
# ─────────────────────────────────────────────
class OBJECT_OT_group_by_empty(bpy.types.Operator):
    """선택한 오브젝트들의 오리진을 지오메트리 중앙으로 설정,
    최상단 Z+5 m 위치에 Empty를 만들고 부모로 연결한다."""

    bl_idname = "object.group_by_empty"
    bl_label  = "Group by Empty"
    bl_options = {'REGISTER', 'UNDO'}

    # --------------------------------------------------
    # 실행 가능 여부
    # --------------------------------------------------
    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and len(context.selected_objects) > 0

    # --------------------------------------------------
    # 실행
    # --------------------------------------------------
    def execute(self, context):
        # 선택된 오브젝트(Empty 제외)
        sel = [o for o in context.selected_objects if o.type != 'EMPTY']
        if not sel:
            self.report({'WARNING'}, "No objects to group")
            return {'CANCELLED'}

        # 1) XY 평균 무게중심
        center = sum((o.matrix_world.translation for o in sel), Vector()) / len(sel)

        # 2) 선택 오브젝트들의 바운딩 박스 최상단 Z
        max_z = max(max(o.matrix_world @ Vector(corner) for corner in o.bound_box)[2]
                    for o in sel)

        # 3) Empty 위치 = 무게중심 XY + (최상단 Z + 5 m)
        empty_location = Vector((center.x, center.y, max_z + 5.0))

        # 4) 각 오브젝트 오리진을 지오메트리 중앙으로
        for obj in sel:
            obj.select_set(True)
            context.view_layer.objects.active = obj
            for other in sel:
                if other != obj:
                    other.select_set(False)
            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')

        # 5) 선택한 오브젝트를 루트(Scene Collection)로 이동
        scene_collection = context.scene.collection
        for obj in sel:
            for col in obj.users_collection:
                col.objects.unlink(obj)
            scene_collection.objects.link(obj)

        # 6) Empty를 루트(Scene Collection)에 직접 생성-링크
        bpy.ops.object.select_all(action='DESELECT')

        empty = bpy.data.objects.new("TempEmpty", None)          # 데이터 생성
        empty.empty_display_type = 'PLAIN_AXES'
        empty.location = empty_location
        scene_collection.objects.link(empty)                     # 루트에 링크

        # 7) 자동 이름 부여: "- Group", "- Group_001", …
        base_name = "- Group"
        name      = base_name
        i = 1
        while name in bpy.data.objects:
            name = f"{base_name}_{i:03d}"
            i += 1
        empty.name = name

        # 8) 선택 오브젝트들을 다시 선택해 Empty에 부모로 설정
        for o in sel:
            o.select_set(True)
        context.view_layer.objects.active = empty
        bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)

        # 9) 완료 메시지
        self.report({'INFO'}, f"Grouped {len(sel)} object(s) into '{empty.name}' "
                              f"and moved all to the root collection.")
        return {'FINISHED'}


# ─────────────────────────────────────────────
# 2) 언그루핑 오퍼레이터
# ─────────────────────────────────────────────
class OBJECT_OT_ungroup_empty(bpy.types.Operator):
    """부모 해제(Clear Keep Transform) 후 방금 사용한 Empty 삭제"""
    bl_idname = "object.ungroup_empty"
    bl_label  = "Ungroup (Clear Keep + Remove Empty)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and any(o.parent for o in context.selected_objects)

    def execute(self, context):
        # 1) 선택 오브젝트의 부모 Empty 이름 수집
        selected_objs = list(context.selected_objects)
        parent_names  = {o.parent.name for o in selected_objs if o.parent}

        # 2) 부모 해제(Transform 유지)
        bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

        # 3) 삭제할 Empty 객체 목록
        empties = [bpy.data.objects.get(name) for name in parent_names
                   if bpy.data.objects.get(name) and
                      bpy.data.objects[name].type == 'EMPTY']

        if empties:
            if context.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')

            bpy.ops.object.select_all(action='DESELECT')
            for em in empties:
                em.select_set(True)
            context.view_layer.objects.active = empties[0]
            bpy.ops.object.delete()

        self.report({'INFO'},
                    f"Ungrouped {len(selected_objs)} object(s), "
                    f"removed {len(empties)} empty(s).")
        return {'FINISHED'}


# ─────────────────────────────────────────────
# 3) 애드온 등록
# ─────────────────────────────────────────────
classes = (
    OBJECT_OT_group_by_empty,
    OBJECT_OT_ungroup_empty,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


# 스크립트를 텍스트 에디터에서 실행할 때 자동 등록되게
if __name__ == "__main__":
    register()
