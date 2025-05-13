# extras/__init__.py

from . import curve_bevel_popup

submodules = [curve_bevel_popup]

def register():
    for m in submodules:
        m.register()

def unregister():
    for m in reversed(submodules):
        m.unregister()
