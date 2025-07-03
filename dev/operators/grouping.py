import bpy
from mathutils import Vector

# ─────────────────────────────────────────────
# 1) 그루핑 오퍼레이터 (수정됨)
# ─────────────────────────────────────────────

class OBJECT_OT_group_by_empty(bpy.types.Operator):
    """Set origins to geometry center, create Empty 5m above center, and parent"""
    bl_idname = "object.group_by_empty"
    bl_label = "Group by Empty"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and len(context.selected_objects) > 0

    def execute(self, context):
        sel = [o for o in context.selected_objects if o.type != 'EMPTY']
        if not sel:
            self.report({'WARNING'}, "No objects to group")
            return {'CANCELLED'}

        # 1) 무게중심 계산 (X, Y축 중심)
        center = sum((o.matrix_world.translation for o in sel), Vector()) / len(sel)
        
        # 2) 각 오브젝트의 바운딩 박스 최상단 Z값 찾기
        max_z = max(max(o.matrix_world @ Vector(corner) for corner in o.bound_box)[2] for o in sel)
        
        # 3) Empty 위치: 무게중심 X,Y + 최상단 Z + 5미터
        empty_location = Vector((center.x, center.y, max_z + 5.0))

        # 4) 각 오브젝트의 오리진을 각각의 지오메트리 중앙으로 설정
        for obj in sel:
            obj.select_set(True)
            context.view_layer.objects.active = obj
            # 다른 오브젝트들은 선택 해제
            for other_obj in sel:
                if other_obj != obj:
                    other_obj.select_set(False)
            # 현재 오브젝트의 오리진을 지오메트리 중앙으로 설정
            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')

        # 5) Empty 생성
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=empty_location)
        empty = context.active_object
        
        # 6) 자동 이름 지정: "Group", "Group_001", ...
        base_name = "- Group"
        name = base_name
        i = 1
        while name in bpy.data.objects:
            name = f"{base_name}_{i:03d}"
            i += 1
        empty.name = name

        # 7) 선택한 객체들 재선택 후 페런트
        for o in sel:
            o.select_set(True)
        context.view_layer.objects.active = empty
        bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)

        # 8) 결과 리포트
        self.report({'INFO'}, f"Grouped {len(sel)} objects into '{empty.name}' at center location")
        return {'FINISHED'}


# ─────────────────────────────────────────────
# 2) 언그루핑 오퍼레이터 (기존과 동일)
# ─────────────────────────────────────────────

class OBJECT_OT_ungroup_empty(bpy.types.Operator):
    """부모 해제 + 위치 유지하고, 방금 언그룹한 Empty만 삭제"""
    bl_idname = "object.ungroup_empty"
    bl_label  = "Ungroup (Clear Keep + Remove Empty)"
    bl_options= {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and any(o.parent for o in context.selected_objects)

    def execute(self, context):
        # 1) 언그룹 대상 및 방금 언그룹된 부모 Empty 이름 저장
        selected_objs = list(context.selected_objects)
        parent_names   = {o.parent.name for o in selected_objs if o.parent}

        # 2) 부모 해제 + 위치 유지
        bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

        # 3) 삭제할 Empty 객체 리스트로 가져오기
        empties = [bpy.data.objects.get(name) 
                   for name in parent_names 
                   if bpy.data.objects.get(name) and bpy.data.objects[name].type == 'EMPTY']

        if empties:
            # 4) OBJECT 모드 보장
            if context.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')

            # 5) 현재 선택 모두 해제
            bpy.ops.object.select_all(action='DESELECT')

            # 6) 삭제 대상 Empty 전부 선택 & 첫번째를 활성화
            for em in empties:
                em.select_set(True)
            context.view_layer.objects.active = empties[0]

            # 7) Blender 내장 delete 오퍼레이터 호출
            bpy.ops.object.delete()

        # 8) 결과 보고
        self.report({'INFO'},
            f"Ungrouped {len(selected_objs)} objects, removed {len(empties)} empty(s).")
        return {'FINISHED'}


# ▶ 클래스 리스트로 통합
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
