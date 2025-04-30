bl_info = {
    "name": "Modifier Pie Kit",
    "author": "EJ",
    "version": (1, 1, 7),
    "blender": (4, 2, 0),
    "location": "View3D > Object > Modifier Pie Kit",
    "description": "A pie of modifier shortcuts and rotational array",
    "category": "Object",
}

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
