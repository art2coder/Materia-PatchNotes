bl_info = {
    "name": "Modifier Pie Kit",
    "blender": (1, 1, 7),
    "category": "Object",
}

import bpy
from .operators import grouping
from . import ui

def register():
    grouping.register()
    ui.register()

def unregister():
    ui.unregister()
    grouping.unregister()

if __name__ == "__main__":
    register()
