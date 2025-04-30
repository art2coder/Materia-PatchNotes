import bpy

# ─────────────────────────────────────────────
# Boolean Modifier
# ─────────────────────────────────────────────

class OBJECT_OT_add_boolean_popup(bpy.types.Operator):
    """Boolean Modifier"""
    bl_idname = "object.add_boolean_popup"
    bl_label = "Boolean Modifier Settings"
    bl_options = {'UNDO'}

    mod = None
    
    @classmethod
    def poll(cls, context):
        return (
        context.mode == 'OBJECT' and
        hasattr(context, "selected_objects") and
        context.selected_objects and
        any(o.type == 'MESH' for o in context.selected_objects)
    )

    def invoke(self, context, event):
        obj = context.active_object
        self.mod = next((m for m in obj.modifiers if m.type == 'BOOLEAN'), None)
        if not self.mod:
            self.mod = obj.modifiers.new(name="Boolean", type='BOOLEAN')
        return context.window_manager.invoke_props_dialog(self, width=300)

    def draw(self, context):
        layout = self.layout
        layout.prop(self.mod, "operation", expand=True)
        layout.prop(self.mod, "operand_type")
        if self.mod.operand_type == 'OBJECT':
            layout.prop(self.mod, "object", text="Target Object")
        elif self.mod.operand_type == 'COLLECTION':
            layout.prop(self.mod, "collection", text="Target Collection")
        layout.separator()
        layout.operator("object.apply_modifier_boolean", text="Apply", icon='CHECKMARK')

    def execute(self, context):
        return {'FINISHED'}

class OBJECT_OT_apply_modifier_boolean(bpy.types.Operator):
    bl_idname = "object.apply_modifier_boolean"
    bl_label = "Apply Boolean Modifier"

    def execute(self, context):
        mod = next((m for m in context.object.modifiers if m.type == 'BOOLEAN'), None)
        if not mod:
            self.report({'WARNING'}, "No Boolean modifier found.")
            return {'CANCELLED'}
        bpy.ops.object.modifier_apply(modifier=mod.name)
        return {'FINISHED'}

# ─────────────────────────────────────────────
#  Bevel Modifier
# ─────────────────────────────────────────────

class OBJECT_OT_add_bevel_popup(bpy.types.Operator):
    """Bevel Modifier"""
    bl_idname = "object.add_bevel_popup"
    bl_label = "Bevel Modifier Settings"
    bl_options = {'UNDO'}

    mod = None
    
    @classmethod
    def poll(cls, context):
        return (
        context.mode == 'OBJECT' and
        hasattr(context, "selected_objects") and
        context.selected_objects and
        any(o.type == 'MESH' for o in context.selected_objects)
    )

    def invoke(self, context, event):
        obj = context.active_object
        self.mod = next((m for m in obj.modifiers if m.type == 'BEVEL'), None)
        if not self.mod:
            self.mod = obj.modifiers.new(name="Bevel", type='BEVEL')
        return context.window_manager.invoke_props_dialog(self, width=300)

    def draw(self, context):
        mod = self.mod
        layout = self.layout
        layout.prop(mod, "affect", expand=True, text="Affect")  # Vertices / Edges
        layout.prop(mod, "width_type", text="Width Type")
        layout.prop(mod, "width", text="Amount")
        layout.prop(mod, "segments", text="Segments")
        layout.separator()
        layout.operator("object.apply_modifier_bevel", text="Apply", icon='CHECKMARK')

    def execute(self, context):
        return {'FINISHED'}

class OBJECT_OT_apply_modifier_bevel(bpy.types.Operator):
    bl_idname = "object.apply_modifier_bevel"
    bl_label = "Apply Bevel Modifier"

    def execute(self, context):
        mod = next((m for m in context.object.modifiers if m.type == 'BEVEL'), None)
        if not mod:
            self.report({'WARNING'}, "No Bevel modifier found.")
            return {'CANCELLED'}
        bpy.ops.object.modifier_apply(modifier=mod.name)
        return {'FINISHED'}

from mathutils import Vector

# ─────────────────────────────────────────────
# 미러 라이브 미리보기용
# ─────────────────────────────────────────────

def update_mirror_modifier(self, context):
    name = "- Mirror_Origin"
    empty = bpy.data.objects.get(name)
    if not empty:
        empty = bpy.data.objects.new(name, None)
        empty.empty_display_type = 'ARROWS'
        empty.empty_display_size = 0.5
        empty.location = Vector((0.0, 0.0, 0.0))
        context.collection.objects.link(empty)

    for obj in context.selected_objects:
        if obj.type != 'MESH':
            continue
        mod = next((m for m in obj.modifiers if m.type == 'MIRROR'), None)
        if not mod:
            mod = obj.modifiers.new(name="Mirror", type='MIRROR')
        mod.use_axis[0] = self.use_x
        mod.use_axis[1] = self.use_y
        mod.use_axis[2] = self.use_z
        mod.mirror_object = empty

    if not getattr(self, "_preview_undopushed", False):
        bpy.ops.ed.undo_push(message="Mirror Preview")
        self._preview_undopushed = True
# ─────────────────────────────────────────────
# 미러 팝업 오퍼레이터
# ─────────────────────────────────────────────
class OBJECT_OT_mirror_live_popup(bpy.types.Operator):
    bl_idname = "object.mirror_live_popup"
    bl_label  = "Mirror Live Popup"
    bl_options= {'UNDO'}

    use_x: bpy.props.BoolProperty(name="X Axis", default=True,  update=update_mirror_modifier)
    use_y: bpy.props.BoolProperty(name="Y Axis", default=False, update=update_mirror_modifier)
    use_z: bpy.props.BoolProperty(name="Z Axis", default=False, update=update_mirror_modifier)

    @classmethod
    def poll(cls, context):
        return (
        context.mode == 'OBJECT' and
        hasattr(context, "selected_objects") and
        context.selected_objects and
        any(o.type == 'MESH' for o in context.selected_objects)
    )
    
    def invoke(self, context, event):
        if hasattr(self, "_preview_undopushed"):
            del self._preview_undopushed
        update_mirror_modifier(self, context)
        return context.window_manager.invoke_props_dialog(self, width=240)

    def draw(self, context):
        layout = self.layout
        layout.label(text="Mirror Axes:")
        row = layout.row(align=True)
        row.prop(self, "use_x", toggle=True)
        row.prop(self, "use_y", toggle=True)
        row.prop(self, "use_z", toggle=True)
        layout.separator()
        layout.operator("object.confirm_mirror_and_apply", text="Apply", icon='CHECKMARK')

    def execute(self, context):
        self.report({'INFO'}, "Mirror preview settings applied.")
        return {'FINISHED'}


class OBJECT_OT_confirm_mirror_and_apply(bpy.types.Operator):
    """Apply Mirror Modifier"""
    bl_idname = "object.confirm_mirror_and_apply"
    bl_label  = "Apply Mirror"
    bl_options= {'UNDO'}

    def execute(self, context):
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                for mod in obj.modifiers:
                    if mod.type == 'MIRROR':
                        context.view_layer.objects.active = obj
                        bpy.ops.object.modifier_apply(modifier=mod.name)
                        break
        self.report({'INFO'}, "Mirror modifier applied.")
        return {'FINISHED'}


# ─────────────────────────────────────────────
# Apply 오퍼레이터
# ─────────────────────────────────────────────

class OBJECT_OT_confirm_mirror_and_apply(bpy.types.Operator):
    bl_idname = "object.confirm_mirror_and_apply"
    bl_label = "Apply Mirror Modifier"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                for mod in obj.modifiers:
                    if mod.type == 'MIRROR':
                        context.view_layer.objects.active = obj
                        bpy.ops.object.modifier_apply(modifier=mod.name)
                        break
        self.report({'INFO'}, "Mirror Modifier applied.")
        return {'FINISHED'}
    
# ─────────────────────────────────────────────
# Apply All Common Modifiers
# ─────────────────────────────────────────────

class OBJECT_OT_apply_all_common_modifiers(bpy.types.Operator):
    """This apply works only through the add-on"""
    bl_idname = "object.apply_all_common_modifiers"
    bl_label = "Apply All Modifiers"

    @classmethod
    def poll(cls, context):
        return (
        context.mode == 'OBJECT' and
        context.active_object is not None and
        context.active_object.type == 'MESH' and
        len(context.active_object.modifiers) > 0
    )
    
    def execute(self, context):
        obj = context.active_object
        if not obj:
            self.report({'WARNING'}, "No active object selected.")
            return {'CANCELLED'}

        applied = []
        for t in ['BOOLEAN', 'BEVEL', 'MIRROR', 'SUBSURF', 'ARRAY', 'SOLIDIFY']:
            mod = next((m for m in obj.modifiers if m.type == t), None)
            if mod:
                bpy.ops.object.modifier_apply(modifier=mod.name)
                applied.append(mod.type.title())

        if applied:
            self.report({'INFO'}, f"Applied: {', '.join(applied)}")
        else:
            self.report({'INFO'}, "No applicable modifiers found.")
        return {'FINISHED'}
    
# ─────────────────────────────────────────────    
# Curve Bevel 
# ─────────────────────────────────────────────

class OBJECT_OT_curve_bevel_popup(bpy.types.Operator):
    """Pipe creation tool"""
    bl_idname = "object.curve_bevel_popup"
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
    
# ─────────────────────────────────────────────    
# Subsurf Modifier 
# ─────────────────────────────────────────────

class OBJECT_OT_add_subsurf_popup(bpy.types.Operator):
    """Subdivision Surface Modifier"""
    bl_idname = "object.add_subsurf_popup"
    bl_label = "Subdivision Surface Settings"
    bl_options = {'UNDO'}

    mod = None
    
    @classmethod
    def poll(cls, context):
        return (
        context.mode == 'OBJECT' and
        any(obj.type == 'MESH' for obj in context.selected_objects)
    )

    def invoke(self, context, event):
        obj = context.active_object
        self.mod = next((m for m in obj.modifiers if m.type == 'SUBSURF'), None)
        if not self.mod:
            self.mod = obj.modifiers.new(name="Subdivision", type='SUBSURF')
        return context.window_manager.invoke_props_dialog(self, width=300)

    def draw(self, context):
        layout = self.layout
        mod = self.mod

        layout.prop(mod, "subdivision_type", expand=True, text="Type")  # Catmull-Clark / Simple
        layout.prop(mod, "levels", text="Viewport")
        layout.prop(mod, "render_levels", text="Render")
        layout.prop(mod, "uv_smooth", text="UV Smooth")

        layout.separator()
        layout.operator("object.apply_modifier_subsurf", text="Apply", icon='CHECKMARK')

    def execute(self, context):
        return {'FINISHED'}


class OBJECT_OT_apply_modifier_subsurf(bpy.types.Operator):
    bl_idname = "object.apply_modifier_subsurf"
    bl_label = "Apply Subsurf Modifier"

    def execute(self, context):
        mod = next((m for m in context.object.modifiers if m.type == 'SUBSURF'), None)
        if not mod:
            self.report({'WARNING'}, "No Subsurf modifier found.")
            return {'CANCELLED'}
        bpy.ops.object.modifier_apply(modifier=mod.name)
        return {'FINISHED'}
    
# ─────────────────────────────────────────────    
# Toggle_Display_Wire
# ─────────────────────────────────────────────
    
class OBJECT_OT_toggle_display_wire(bpy.types.Operator):
    """Toggle_Display_Wire"""
    bl_idname = "object.toggle_display_wire"
    bl_label = "Toggle Wire Display"
    bl_description = "Toggle Display As: Wire for selected objects"
    bl_options = {'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return (
            context.mode == 'OBJECT' and
            any(obj.type == 'MESH' for obj in context.selected_objects)
        )

    def execute(self, context):
        for obj in context.selected_objects:
            if obj.display_type != 'WIRE':
                obj.display_type = 'WIRE'
            else:
                obj.display_type = 'SOLID'
        self.report({'INFO'}, "Toggled Wire Display")
        return {'FINISHED'}
    

# ─────────────────────────────────────────────    
# Toggle_Overlay 
# ─────────────────────────────────────────────   


class VIEW3D_OT_toggle_overlay(bpy.types.Operator):
    
    bl_idname = "view3d.toggle_overlay"
    bl_label = "Toggle Overlays"
    bl_description = "Toggle 3D View Overlays"
    bl_options = {'UNDO'}

    def execute(self, context):
        space = context.space_data
        if space.type == 'VIEW_3D':
            space.overlay.show_overlays = not space.overlay.show_overlays
            self.report({'INFO'}, f"Overlays {'Enabled' if space.overlay.show_overlays else 'Disabled'}")
        return {'FINISHED'}


classes = (
     
    OBJECT_OT_apply_all_common_modifiers,
    OBJECT_OT_add_boolean_popup,
    OBJECT_OT_apply_modifier_boolean,
    OBJECT_OT_add_bevel_popup,
    OBJECT_OT_apply_modifier_bevel,
    OBJECT_OT_mirror_live_popup,
    OBJECT_OT_confirm_mirror_and_apply,
    OBJECT_OT_curve_bevel_popup,
    OBJECT_OT_add_subsurf_popup,
    OBJECT_OT_apply_modifier_subsurf,
    OBJECT_OT_toggle_display_wire,
    VIEW3D_OT_toggle_overlay, 
    
)        

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
