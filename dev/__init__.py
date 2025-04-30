bl_info = {
    "name": "Modifier Pie Kit",
    "author": "Your Name",
    "version": (1, 1, 7),
    "blender": (4, 2, 0),     
    "location": "View3D > Object > Modifier Pie Kit",
    "description": "A pie of modifier shortcuts and rotational array",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Object",
}

import bpy
from . import ui
from .operators import grouping
from .operators import popup_modifiers, pie_menu
from .utils.keymap import register_keymaps, unregister_keymaps


def register():
    popup_modifiers.register()
    pie_menu.register()
    grouping.register()
    ui.register()
    register_keymaps()

def unregister():
    unregister_keymaps()
    ui.unregister()
    grouping.unregister()
    pie_menu.register()
    popup_modifiers.register()

if __name__ == "__main__":
    register()
