# extras/__init__.py

def register():
    from . import curve_bevel
    curve_bevel.register()

def unregister():
    from . import curve_bevel
    curve_bevel.unregister()

