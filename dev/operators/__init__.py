# operators/__init__.py

from .grouping          import register as register_group,   unregister as unregister_group
from .popup_modifiers  import register as register_mods,    unregister as unregister_mods
from .pie_modifiers         import register as register_pie,     unregister as unregister_pie
from .pie_pivot import register as register_pivot, unregister as unregister_pivot
from .popup_pivot import register as register_pivot_ops, unregister as unregister_pivot_ops

def register():
    register_group()
    register_mods()
    register_pie()
    register_pivot()
    register_pivot_ops()

def unregister():
    unregister_pivot_ops()
    unregister_pivot()
    unregister_pie()
    unregister_mods()
    unregister_group()
