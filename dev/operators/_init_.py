# operators/__init__.py
from .grouping import OBJECT_OT_group_by_empty, OBJECT_OT_ungroup_empty

classes = (
    OBJECT_OT_group_by_empty,
    OBJECT_OT_ungroup_empty,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
