import bpy

class PIE_MT_pivot_pie(bpy.types.Menu):
    bl_label = "Pivot Pie Menu"
    bl_idname = "PIE_MT_pivot_pie"

    def draw(self, context):
        pie = self.layout.menu_pie()

        # 위쪽 (키패드 8)
        pie.operator("modifier_pie.origin_to_geometry", text="Origin to Geometry", icon='OBJECT_ORIGIN')
        
        # 오른쪽 위 (키패드 9)
        pie.operator("modifier_pie.origin_to_cursor", text="Origin to 3D Cursor", icon='PIVOT_CURSOR')
        
        # 오른쪽 (키패드 6)
        pie.operator("modifier_pie.cursor_to_selection", text="Cursor", icon='CURSOR')
        
        # 오른쪽 아래 (키패드 3)
        pie.operator("modifier_pie.selection_to_cursor", text="Move", icon='ARROW_LEFTRIGHT')

        # 아래쪽 (키패드 2)
        pie.separator()

        # 왼쪽 아래 (키패드 1)
        pie.separator()

        # 왼쪽 (키패드 4)
        current = context.scene.tool_settings.transform_pivot_point
        label = "Median" if current == 'CURSOR' else "3D Cursor"
        icon = 'PIVOT_MEDIAN' if current == 'CURSOR' else 'PIVOT_CURSOR'
        pie.operator("modifier_pie.toggle_pivot", text=label, icon=icon)

        # 왼쪽 위 (키패드 7)
        pie.operator("modifier_pie.cursor_to_origin", text="Reset", icon='FILE_REFRESH')

classes = (PIE_MT_pivot_pie,)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
