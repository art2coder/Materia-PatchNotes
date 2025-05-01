import bpy

# ─────────────────────────────────────────────
# Pivot 관련 오퍼레이터
# ─────────────────────────────────────────────

class PIVOT_OT_toggle_pivot(bpy.types.Operator):
    '''Pivot: Cursor ⇄ Median'''
    bl_idname = "modifier_pie.toggle_pivot"
    bl_label = "Pivot"

    def execute(self, context):
        current = context.scene.tool_settings.transform_pivot_point
        new_mode = 'MEDIAN_POINT' if current == 'CURSOR' else 'CURSOR'
        context.scene.tool_settings.transform_pivot_point = new_mode
        return {'FINISHED'}

class PIVOT_OT_cursor_to_selection(bpy.types.Operator):
    '''Cursor → Selection'''
    bl_idname = "modifier_pie.cursor_to_selection"
    bl_label = "Cursor"
    
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

class PIVOT_OT_cursor_to_origin(bpy.types.Operator):
    '''Cursor → Origin'''
    bl_idname = "modifier_pie.cursor_to_origin"
    bl_label = "Reset"

    def execute(self, context):
        context.scene.cursor.location = (0.0, 0.0, 0.0)
        return {'FINISHED'}

class PIVOT_OT_selection_to_cursor(bpy.types.Operator):
    """Selection → Cursor"""
    bl_idname = "modifier_pie.selection_to_cursor"
    bl_label = "Selection to Cursor"
    bl_description = "Snap selected objects to 3D Cursor"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        # 3D 뷰에서, 선택된 오브젝트가 하나 이상 있을 때만 활성화
        return (context.area.type == 'VIEW_3D' and
                len(context.selected_objects) > 0)

    def execute(self, context):
        # Blender 내장 스냅 오퍼레이터 호출
        bpy.ops.view3d.snap_selected_to_cursor(use_offset=False)
        self.report({'INFO'}, "Selection → Cursor")
        return {'FINISHED'}

class OBJECT_OT_origin_to_geometry(bpy.types.Operator):
    """Origin → Geometry"""
    bl_idname = "modifier_pie.origin_to_geometry"
    bl_label = "Origin to Geometry"
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

class OBJECT_OT_origin_to_cursor(bpy.types.Operator):
    """Origin → 3D Cursor"""
    bl_idname = "modifier_pie.origin_to_cursor"
    bl_label = "Origin to 3D Cursor"
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
    PIVOT_OT_toggle_pivot,
    PIVOT_OT_cursor_to_selection,
    PIVOT_OT_cursor_to_origin,
    PIVOT_OT_selection_to_cursor,
    OBJECT_OT_origin_to_geometry,
    OBJECT_OT_origin_to_cursor,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
