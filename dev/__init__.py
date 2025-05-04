bl_info = {
    "name": "Modifier Pie Kit",
    "author": "EJ",
    "version": (1, 2, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Object > Modifier Pie Kit",
    "description": "A pie of modifier shortcuts and rotational array",
    "category": "Object",
}

# Version history
# v1.0.0 - Initial Modifiers pie menu(Q)
# v1.1.1 - Added Pivot pie menu (W)
# v1.1.2 - Added Group_by_Empty (Ctrl + G)
# v1.1.3 - Added Ungroup_by_Empty (Alt + G)
# v1.1.4 - Fix crash issues
# v1.1.5 - Added Revive Gizmo 
# v1.1.6 - Fix Pivot pie menu 
# v1.1.7 - Refactoring process
# v1.1.8 - Added Rotational array 
# v1.1.9 - Added Select Tool (B)
# v1.2.0 - Added Extras Tool


import bpy
from . import ui
from .operators import register as register_ops, unregister as unregister_ops
from .utils.keymap import register_keymaps, unregister_keymaps


def register():
    register_ops()          
    ui.register()
    register_keymaps()

def unregister():
    unregister_keymaps()
    ui.unregister()
    unregister_ops()

if __name__ == "__main__":
    register()
