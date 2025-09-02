import bpy

bl_info = {
    "name": "Modifier Pie Kit",
    "author": "EJ",
    "version": (1, 4, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Object > Modifier Pie Kit",
    "description": "Simple Workflow Pie Menu Toolkit",
    "category": "Object",
}


from . import ui
from .operators import register as register_ops, unregister as unregister_ops


def register():
    register_ops()
    ui.register()
    

def unregister():
    
    ui.unregister()
    unregister_ops()

if __name__ == "__main__":
    register()
