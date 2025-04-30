# operators/__init__.py

from .grouping          import register as register_group,   unregister as unregister_group
from .popup_modifiers  import register as register_mods,    unregister as unregister_mods
from .pie_menu         import register as register_pie,     unregister as unregister_pie

def register():
    # 1) grouping operators
    register_group()
    # 2) modifier popup operators
    register_mods()
    # 3) pie menu definition
    register_pie()

def unregister():
    # 1) pie menu
    unregister_pie()
    # 2) popup modifiers
    unregister_mods()
    # 3) grouping
    unregister_group()
