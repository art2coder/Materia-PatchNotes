import bpy
import bmesh
from mathutils import Vector

# ─────────────────────────────────────────────
# Pivot 관련 오퍼레이터
# ─────────────────────────────────────────────

class OBJECT_OT_origin_to_bottom(bpy.types.Operator):
    """Origin to Bottom without Cumulative Movement on Repeat"""
    bl_idname = "object.origin_to_bottom"
    bl_label = "Set Origin to Bottom"
    bl_description = "오브젝트의 월드상 위치는 유지한 채, 오브젝트의 가장 아래쪽 중앙으로 오리진을 이동시킵니다"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.area.type == 'VIEW_3D' and
                len(context.selected_objects) > 0)

    def execute(self, context):
        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue

            mw = obj.matrix_world.copy()
            original_location = obj.location.copy()

            # 활성 객체 설정 및 에디트 모드 진입
            context.view_layer.objects.active = obj
            bpy.ops.object.mode_set(mode='EDIT')

            bm = bmesh.from_edit_mesh(obj.data)

            # 글로벌 Z 최소값 찾기
            world_zs = [(mw @ v.co).z for v in bm.verts]
            if not world_zs:
                bpy.ops.object.mode_set(mode='OBJECT')
                continue

            min_z_global = min(world_zs)
            threshold = 1e-6
            bottom_verts = [v for i, v in enumerate(bm.verts) if abs(world_zs[i] - min_z_global) < threshold]

            if not bottom_verts:
                bpy.ops.object.mode_set(mode='OBJECT')
                continue

            # 바닥 버텍스의 로컬 중앙 계산
            center_local = sum((v.co for v in bottom_verts), Vector((0, 0, 0))) / len(bottom_verts)

            # 현재 오리진의 글로벌 위치
            origin_global = mw @ Vector((0, 0, 0))

            # 목표 오리진의 글로벌 위치
            target_global = mw @ center_local

            # 오프셋 계산
            offset = target_global - origin_global

            # 누적 방지: 오프셋이 매우 작으면 스킵 (이미 바닥에 있음)
            if offset.length < threshold:
                bpy.ops.object.mode_set(mode='OBJECT')
                continue

            # 버텍스 이동: geometry를 오프셋만큼 조정
            for v in bm.verts:
                v.co -= center_local  # 부호 조정으로 누적 방지

            bmesh.update_edit_mesh(obj.data)

            # 모드 복귀
            bpy.ops.object.mode_set(mode='OBJECT')

            # 객체 위치 보정: 글로벌 위치 유지
            obj.location += offset

        self.report({'INFO'}, "Origin moved to bottom")
        return {'FINISHED'}


class MODIFIER_PIE_OT_toggle_pivot(bpy.types.Operator):
    '''Pivot: Cursor ⇄ Median'''
    bl_idname = "modifier_pie.toggle_pivot"
    bl_label = "Toggle Pivot Point"
    bl_description = "피봇 포인트를 3D 커서와 중간 지점(Median Point) 사이에서 전환합니다"

    def execute(self, context):
        current = context.scene.tool_settings.transform_pivot_point
        new_mode = 'MEDIAN_POINT' if current == 'CURSOR' else 'CURSOR'
        context.scene.tool_settings.transform_pivot_point = new_mode
        return {'FINISHED'}

class MODIFIER_PIE_OT_cursor_to_selection(bpy.types.Operator):
    '''Cursor → Selection'''
    bl_idname = "modifier_pie.cursor_to_selection"
    bl_label = "Snap Cursor to Selected"
    bl_description = "선택한 요소(오브젝트, 버텍스 등)의 중심으로 3D 커서를 이동시킵니다"

    @classmethod
    def poll(cls, context):
        return (
            context.area.type == 'VIEW_3D'
            and context.mode in {'OBJECT', 'EDIT_MESH'}
            and context.selected_objects
        )

    def execute(self, context):
        bpy.ops.view3d.snap_cursor_to_selected()
        return {'FINISHED'}

class MODIFIER_PIE_OT_cursor_to_origin(bpy.types.Operator):
    '''Cursor → Origin'''
    bl_idname = "modifier_pie.cursor_to_origin"
    bl_label = "Snap Cursor to World Origin"
    bl_description = "3D 커서를 월드 원점(0, 0, 0)으로 되돌립니다"

    def execute(self, context):
        context.scene.cursor.location = (0.0, 0.0, 0.0)
        return {'FINISHED'}

class MODIFIER_PIE_OT_selection_to_cursor(bpy.types.Operator):
    """Selection → Cursor"""
    bl_idname = "modifier_pie.selection_to_cursor"
    bl_label = "Snap Selection to Cursor"
    bl_description = "선택한 오브젝트를 3D 커서의 위치로 이동시킵니다. 실행 후 F9를 눌러 세부 옵션을 조절할 수 있습니다"
    bl_options = {'REGISTER', 'UNDO'}

    # redo 패널 옵션 속성 추가
    use_offset: bpy.props.BoolProperty(
        name="Offset",
        description="Keep relative position of selected objects",
        default=False
    )
    use_rotation: bpy.props.BoolProperty(
        name="Rotation",
        description="Apply cursor rotation (for tilted surfaces)",
        default=False
    )

    @classmethod
    def poll(cls, context):
        return (context.area.type == 'VIEW_3D' and
                len(context.selected_objects) > 0)

    def execute(self, context):
        # 블렌더 버전을 확인하여 세 가지 경우로 분기합니다.
        if bpy.app.version >= (4, 5, 0):
            # 4.5 이상: use_offset와 use_rotation 모두 사용
            bpy.ops.view3d.snap_selected_to_cursor(
                use_offset=self.use_offset,
                use_rotation=self.use_rotation
            )
            self.report({'INFO'}, f"Selection → Cursor (Offset: {self.use_offset}, Rotation: {self.use_rotation})")

        elif bpy.app.version >= (4, 2, 0):
            # 4.2 이상 ~ 4.5 미만: use_offset만 사용
            bpy.ops.view3d.snap_selected_to_cursor(
                use_offset=self.use_offset
            )
            self.report({'INFO'}, f"Selection → Cursor (Offset: {self.use_offset})")

        else:
            # 4.2 미만: 옵션 없이 기본 기능만 실행
            bpy.ops.view3d.snap_selected_to_cursor()
            self.report({'INFO'}, "Selection → Cursor")
        
        return {'FINISHED'}

class MODIFIER_PIE_OT_origin_to_geometry(bpy.types.Operator):
    """Origin → Geometry"""
    bl_idname = "modifier_pie.origin_to_geometry"
    bl_label = "Set Origin to Geometry"
    bl_description = "오브젝트의 지오메트리(형상) 중심으로 오리진을 이동시킵니다"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (
            context.mode == 'OBJECT' and
            context.selected_objects and
            any(o.type in {'MESH', 'CURVE', 'EMPTY'} for o in context.selected_objects)
        )

    def execute(self, context):
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
        self.report({'INFO'}, "Origin set to Geometry.")
        return {'FINISHED'}

class MODIFIER_PIE_OT_origin_to_cursor(bpy.types.Operator):
    """Origin → 3D Cursor"""
    bl_idname = "modifier_pie.origin_to_cursor"
    bl_label = "Set Origin to 3D Cursor"
    bl_description = "오브젝트의 오리진을 3D 커서의 현재 위치로 이동시킵니다"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (
            context.mode == 'OBJECT' and
            context.selected_objects and
            any(o.type in {'MESH', 'CURVE', 'EMPTY'} for o in context.selected_objects)
        )

    def execute(self, context):
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
        self.report({'INFO'}, "Origin set to 3D Cursor.")
        return {'FINISHED'}
        
# ─────────────────────────────────────────────
# 클래스 등록
# ─────────────────────────────────────────────

classes = (
    OBJECT_OT_origin_to_bottom,
    MODIFIER_PIE_OT_toggle_pivot,
    MODIFIER_PIE_OT_cursor_to_selection,
    MODIFIER_PIE_OT_cursor_to_origin,
    MODIFIER_PIE_OT_selection_to_cursor,
    MODIFIER_PIE_OT_origin_to_geometry,
    MODIFIER_PIE_OT_origin_to_cursor,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
