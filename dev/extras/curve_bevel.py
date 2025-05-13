import bpy

class OBJECT_OT_curve_bevel_popup(bpy.types.Operator):
    """Pipe creation tool"""
    bl_idname = "modifier_pie.curve_bevel_popup"
    bl_label = "Curve Bevel Settings"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        selected = context.selected_objects
        return (
            context.mode == 'OBJECT' and
            len(selected) == 1 and
            selected[0].type == 'CURVE'
    )
     
    def invoke(self, context, event):
        obj = context.object
        if not obj or obj.type != 'CURVE':
            self.report({'WARNING'}, "Selected object is not a Curve.")
            return {'CANCELLED'}
        return context.window_manager.invoke_props_dialog(self, width=300)

    def draw(self, context):
        curve = context.object.data
        layout = self.layout

        layout.prop(curve, "bevel_depth", text="Bevel Depth")
        layout.prop(curve, "bevel_resolution", text="Resolution")
        layout.prop(curve, "use_fill_caps", text="Fill Caps")
        layout.prop(curve, "bevel_object", text="Bevel Object")

    def execute(self, context):
        return {'FINISHED'}
    

def menu_func(self, context):
    self.layout.operator(
        OBJECT_OT_curve_bevel_popup.bl_idname,
        text="Curve Bevel",
        icon='MESH_CYLINDER'
    )



def register():
    bpy.utils.register_class(OBJECT_OT_curve_bevel_popup)
    bpy.types.VIEW3D_MT_curve_add.append(menu_func)

def unregister():
    bpy.types.VIEW3D_MT_curve_add.remove(menu_func)
    bpy.utils.unregister_class(OBJECT_OT_curve_bevel_popup)

if __name__ == "__main__":
    try:
        unregister()
    except:
        pass
    register()
