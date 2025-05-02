
bl_info = {
    "name": "Smart Select Tool Cycler",
    "blender": (4, 2, 0),
    "category": "3D View",
    "author": "ChatGPT",
    "description": "Cycle between Box, Circle, and Lasso select tools with B key; remembers last tool when switching back.",
}

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

addon_keymaps = []

def register():
    bpy.utils.register_class(SmartSelectCycleOperator)

    # Register keymap in Object Mode and Edit Mode (Mesh)
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        for mode in ["Object Mode", "Mesh"]:
            km = kc.keymaps.new(name=mode, space_type='EMPTY')
            kmi = km.keymap_items.new("object.smart_select_cycle", type='B', value='PRESS')
            addon_keymaps.append((km, kmi))

def unregister():
    bpy.utils.unregister_class(SmartSelectCycleOperator)

    # Remove keymaps
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

if __name__ == "__main__":
    register()
