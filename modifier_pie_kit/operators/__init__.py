import importlib


from . import grouping
from . import popup_modifiers
from . import popup_pivot
from . import pie_pivot
from . import boolean
from . import array_modifier_popup
from . import clean_view
from . import camera_quick_settings
from . import Outliner_Enhancer

modules = [
    grouping,
    popup_modifiers,
    popup_pivot,
    pie_pivot,
    boolean,    
    array_modifier_popup,
    clean_view,
    camera_quick_settings,
    Outliner_Enhancer,
]

def register():  
    for mod in modules:
        importlib.reload(mod)
        
    for mod in modules:
        if hasattr(mod, 'register'):
            mod.register()
            
def unregister(): 
    for mod in reversed(modules):
        if hasattr(mod, 'unregister'):
            mod.unregister()