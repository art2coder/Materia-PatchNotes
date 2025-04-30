import bpy

# operators/popup_modifiers.py
classes = (
    # Boolean
    OBJECT_OT_add_boolean_popup,
    OBJECT_OT_apply_modifier_boolean,

    # Bevel
    OBJECT_OT_add_bevel_popup,
    OBJECT_OT_apply_modifier_bevel,

    # Curve Bevel
    OBJECT_OT_curve_bevel_popup,

    # Subsurf
    OBJECT_OT_add_subsurf_popup,
    OBJECT_OT_apply_modifier_subsurf,

    # Mirror
    OBJECT_OT_mirror_live_popup,
    OBJECT_OT_confirm_mirror_and_apply,

    # Apply All
    OBJECT_OT_apply_all_common_modifiers,

    # Wire & Overlay
    OBJECT_OT_toggle_display_wire,
    VIEW3D_OT_toggle_overlay,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
