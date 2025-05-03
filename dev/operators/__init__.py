# operators/__init__.py

from .grouping           import register as register_group,        unregister as unregister_group
from .popup_modifiers    import register as register_mods,         unregister as unregister_mods
from .pie_modifiers      import register as register_pie,          unregister as unregister_pie
from .popup_pivot        import register as register_pivot_ops,    unregister as unregister_pivot_ops
from .pie_pivot          import register as register_pivot,        unregister as unregister_pivot
from .tools_extra import register as register_select, unregister as unregister_select
from . import auto_sorter

def register():
    register_group()
    register_mods()
    register_pie()
    register_pivot_ops()   
    register_pivot()
    register_select()
    auto_sorter.register()

def unregister():
    auto_sorter.unregister()
    unregister_select()
    unregister_pivot()
    unregister_pivot_ops()  
    unregister_pie()
    unregister_mods()
    unregister_group()
