bl_info = {
    "name": "Modifier Pie Kit",
    "author": "Your Name",
    "version": (1, 1, 7),
    "blender": (4, 2, 0),      # ← 여기!
    "location": "View3D > Object > Modifier Pie Kit",
    "description": "A pie of modifier shortcuts and rotational array",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
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
