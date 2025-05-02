import bpy

class SmartSelectCycleOperator(bpy.types.Operator):
    bl_idname = "object.smart_select_cycle"
    bl_label = "Smart Select Tool Cycle"
    bl_description = "Cycle Select Box, Circle, and Lasso tools, and remember last used when switching back"

    last_tool = "box"  # Default starting tool
    tool_order = ["box", "circle", "lasso"]

    tool_map = {
        "box": "builtin.select_box",
        "circle": "builtin.select_circle",
        "lasso": "builtin.select_lasso",
    }

    @classmethod
    def get_current_tool(cls):
        return bpy.context.workspace.tools.from_space_view3d_mode(bpy.context.mode).idname

    def execute(self, context):
        current_tool = self.get_current_tool()

        # If already on a select tool, cycle to next
        if current_tool in self.tool_map.values():
            current_index = list(self.tool_map.values()).index(current_tool)
            next_index = (current_index + 1) % len(self.tool_map)
            next_key = list(self.tool_map.keys())[next_index]
            next_tool = self.tool_map[next_key]

            SmartSelectCycleOperator.last_tool = next_key
            bpy.ops.wm.tool_set_by_id(name=next_tool)
            self.report({'INFO'}, f"Select Tool: {next_key.capitalize()}")
        else:
            # Not in a select tool: restore last remembered select tool
            remembered_tool = self.tool_map[self.last_tool]
            bpy.ops.wm.tool_set_by_id(name=remembered_tool)
            self.report({'INFO'}, f"Select Tool: {self.last_tool.capitalize()}")

        return {'FINISHED'}


classes = (SmartSelectCycleOperator,)



def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
