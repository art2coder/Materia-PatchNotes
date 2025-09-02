# operators/__init__.py

from .grouping           import register as register_group,        unregister as unregister_group
from .popup_modifiers    import register as register_mods,         unregister as unregister_mods
from .popup_pivot        import register as register_pivot_ops,    unregister as unregister_pivot_ops
from .pie_pivot          import register as register_pivot,        unregister as unregister_pivot
from .boolean            import register as register_boolean,      unregister as unregister_boolean
from .preferences        import register as register_preferences,  unregister as unregister_preferences 
from .array_modifier_popup import register as register_array_popup, unregister as unregister_array_popup


from . import clean_view
from . import camera_quick_settings
from . import Outliner_Enhancer


def register():
    register_group()
    register_mods()    
    register_pivot_ops()   
    register_pivot()
    register_boolean()
    register_preferences()
    register_array_popup()
    
    clean_view.register()
    camera_quick_settings.register()
    Outliner_Enhancer.register()
    

def unregister():
    
    Outliner_Enhancer.unregister()
    camera_quick_settings.unregister()
    clean_view.unregister()
    
    unregister_array_popup()
    unregister_preferences()
    unregister_boolean()
    unregister_pivot()
    unregister_pivot_ops()    
    unregister_mods()
    unregister_group()
