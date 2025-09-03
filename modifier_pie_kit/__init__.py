import bpy
from . import preferences
from . import ui
from .operators import register as register_ops, unregister as unregister_ops

bl_info = {
    "name": "Modifier Pie Kit",
    "author": "EJ",
    "version": (1, 4, 7), 
    "blender": (4, 2, 0), 
    "location": "View3D > Object > Modifier Pie Kit",
    "description": "Simple Workflow Pie Menu Toolkit",
    "category": "Object",
}

def register():
    register_ops()
    ui.register()
    preferences.register()

def unregister():
    preferences.unregister()
    ui.unregister()
    unregister_ops()