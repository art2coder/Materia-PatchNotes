import bpy

class MODIFIER_PIE_OT_add_array_popup(bpy.types.Operator):
    bl_idname = "modifier_pie.add_array_popup"
    bl_label = "Add Array Modifier"
    bl_description = "선택한 오브젝트에 Array 모디파이어를 추가하고 설정창을 엽니다. 오브젝트를 규칙적으로 복제 배열합니다"
    bl_options = {'UNDO'}
    
    selected_modifier_index: bpy.props.IntProperty(default=0)
    
    _current_popup = None
    
    @classmethod
    def poll(cls, context):
        return (
            context.mode == 'OBJECT' and
            any(obj.type == 'MESH' for obj in context.selected_objects)
        )
    
    def invoke(self, context, event):
        if MODIFIER_PIE_OT_add_array_popup._current_popup is not None:
            try:
                MODIFIER_PIE_OT_add_array_popup._current_popup.cancel(context)
            except:
                pass
            MODIFIER_PIE_OT_add_array_popup._current_popup = None
        
        obj = context.active_object
        array_modifiers = [m for m in obj.modifiers if m.type == 'ARRAY']
        
        if not array_modifiers:
            modifier_name = "Array"
            new_mod = obj.modifiers.new(name=modifier_name, type='ARRAY')
            new_mod.count = 2
            new_mod.relative_offset_displace[0] = 1.0
            new_mod.relative_offset_displace[1] = 0.0
            new_mod.relative_offset_displace[2] = 0.0
            self.selected_modifier_index = 0
        else:
            if self.selected_modifier_index >= len(array_modifiers):
                self.selected_modifier_index = 0
        
        MODIFIER_PIE_OT_add_array_popup._current_popup = self
        return context.window_manager.invoke_props_dialog(self, width=350)
    
    def check(self, context):
        obj = context.active_object
        array_modifiers = [m for m in obj.modifiers if m.type == 'ARRAY']
        if array_modifiers and self.selected_modifier_index < len(array_modifiers):
            bpy.ops.ed.undo_push(message="Array Modifier Update")
            context.view_layer.update()
            if context.area:
                context.area.tag_redraw()
        return True
    
    def execute(self, context):
        if MODIFIER_PIE_OT_add_array_popup._current_popup == self:
            MODIFIER_PIE_OT_add_array_popup._current_popup = None
        return {'FINISHED'}
    
    def cancel(self, context):
        if MODIFIER_PIE_OT_add_array_popup._current_popup == self:
            MODIFIER_PIE_OT_add_array_popup._current_popup = None
        return {'CANCELLED'}
    
    @classmethod
    def close_current_popup(cls):
        if cls._current_popup is not None:
            try:
                cls._current_popup.cancel(bpy.context)
            except:
                pass
            cls._current_popup = None
    
    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        array_modifiers = [m for m in obj.modifiers if m.type == 'ARRAY']
        
        if not array_modifiers:
            layout.label(text="No Array modifiers", icon='INFO')
            return
        
        if self.selected_modifier_index >= len(array_modifiers):
            self.selected_modifier_index = len(array_modifiers) - 1
        current_mod = array_modifiers[self.selected_modifier_index]
        
        if len(array_modifiers) > 1:
            row = layout.row(align=True)
            row.label(text="Arrays:", icon='MOD_ARRAY')
            
            for i, mod in enumerate(array_modifiers):
                if i == self.selected_modifier_index:
                    op = row.operator("modifier_pie.switch_array", text=f"●{i+1}", depress=True)
                else:
                    op = row.operator("modifier_pie.switch_array", text=str(i+1))
                op.target_index = i
            
            row.separator()
            row.operator("modifier_pie.add_array_quick", text="", icon='ADD')
            if len(array_modifiers) > 1:
                op_del = row.operator("modifier_pie.delete_array_quick", text="", icon='X')
                op_del.target_index = self.selected_modifier_index
        else:
            row = layout.row(align=True)
            row.label(text=f"Array: {current_mod.name}", icon='MOD_ARRAY')
            row.operator("modifier_pie.add_array_quick", text="", icon='ADD')
        
        row = layout.row(align=True)
        row.prop(current_mod, "count", text="Count")
        row.prop(current_mod, "use_relative_offset", text="Offset")
        
        if current_mod.use_relative_offset:
            row = layout.row(align=True)
            row.prop(current_mod, "relative_offset_displace", index=0, text="X")
            row.prop(current_mod, "relative_offset_displace", index=1, text="Y")
            row.prop(current_mod, "relative_offset_displace", index=2, text="Z")
        
        op_apply = layout.operator("modifier_pie.apply_modifier_array", text="Apply", icon='CHECKMARK')
        if op_apply is not None:
            op_apply.modifier_name = current_mod.name

class MODIFIER_PIE_OT_switch_array(bpy.types.Operator):
    bl_idname = "modifier_pie.switch_array"
    bl_label = "Switch Array Modifier"
    bl_description = "팝업창에 표시할 Array 모디파이어를 전환합니다"
    
    target_index: bpy.props.IntProperty()
    
    def execute(self, context):
        if MODIFIER_PIE_OT_add_array_popup._current_popup:
            MODIFIER_PIE_OT_add_array_popup._current_popup.selected_modifier_index = self.target_index
            if context.area:
                context.area.tag_redraw()
        return {'FINISHED'}

class MODIFIER_PIE_OT_add_array_quick(bpy.types.Operator):
    bl_idname = "modifier_pie.add_array_quick"
    bl_label = "Add New Array Modifier"
    bl_description = "활성 오브젝트에 새로운 Array 모디파이어를 추가합니다"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.active_object
        array_modifiers = [m for m in obj.modifiers if m.type == 'ARRAY']
        modifier_count = len(array_modifiers)
        
        modifier_name = f"Array.{modifier_count:03d}" if array_modifiers else "Array"
        new_mod = obj.modifiers.new(name=modifier_name, type='ARRAY')
        
        new_mod.count = 2
        
        axis_cycle = modifier_count % 3
        if axis_cycle == 0:
            new_mod.relative_offset_displace[0] = 1.0
            new_mod.relative_offset_displace[1] = 0.0
            new_mod.relative_offset_displace[2] = 0.0
        elif axis_cycle == 1:
            new_mod.relative_offset_displace[0] = 0.0
            new_mod.relative_offset_displace[1] = 1.0
            new_mod.relative_offset_displace[2] = 0.0
        else:
            new_mod.relative_offset_displace[0] = 0.0
            new_mod.relative_offset_displace[1] = 0.0
            new_mod.relative_offset_displace[2] = 1.0
        
        if MODIFIER_PIE_OT_add_array_popup._current_popup:
            MODIFIER_PIE_OT_add_array_popup._current_popup.selected_modifier_index = len(array_modifiers)
            if context.area:
                context.area.tag_redraw()
        
        return {'FINISHED'}

class MODIFIER_PIE_OT_delete_array_quick(bpy.types.Operator):
    bl_idname = "modifier_pie.delete_array_quick"
    bl_label = "Delete Selected Array Modifier"
    bl_description = "현재 선택된 Array 모디파이어를 삭제합니다"
    bl_options = {'REGISTER', 'UNDO'}
    
    target_index: bpy.props.IntProperty()
    
    def execute(self, context):
        obj = context.active_object
        array_modifiers = [m for m in obj.modifiers if m.type == 'ARRAY']
        
        if self.target_index < len(array_modifiers):
            mod = array_modifiers[self.target_index]
            modifier_name = mod.name
            obj.modifiers.remove(mod)
            self.report({'INFO'}, f"Deleted {modifier_name}")
        
        if MODIFIER_PIE_OT_add_array_popup._current_popup:
            popup = MODIFIER_PIE_OT_add_array_popup._current_popup
            if popup.selected_modifier_index >= len(array_modifiers) - 1:
                popup.selected_modifier_index = max(0, len(array_modifiers) - 2)
            if context.area:
                context.area.tag_redraw()
        
        return {'FINISHED'}

class MODIFIER_PIE_OT_apply_modifier_array(bpy.types.Operator):
    bl_idname = "modifier_pie.apply_modifier_array"
    bl_label = "Apply Array Modifier"
    bl_description = "활성화된 Array 모디파이어를 적용합니다"
    bl_options = {'REGISTER', 'UNDO'}
    
    modifier_name: bpy.props.StringProperty()
    
    def execute(self, context):
        obj = context.active_object
        
        if self.modifier_name:
            mod = obj.modifiers.get(self.modifier_name)
            if not mod:
                self.report({'WARNING'}, f"No modifier named '{self.modifier_name}' found.")
                return {'CANCELLED'}
            
            bpy.ops.object.modifier_apply(modifier=self.modifier_name)
            self.report({'INFO'}, f"Applied {self.modifier_name}")
        else:
            mod = next((m for m in obj.modifiers if m.type == 'ARRAY'), None)
            if not mod:
                self.report({'WARNING'}, "No Array modifier found.")
                return {'CANCELLED'}
            
            bpy.ops.object.modifier_apply(modifier=mod.name)
            self.report({'INFO'}, f"Applied {mod.name}")
        
        if MODIFIER_PIE_OT_add_array_popup._current_popup and context.area:
            context.area.tag_redraw()
        
        return {'FINISHED'}

classes = (
    MODIFIER_PIE_OT_add_array_popup,
    MODIFIER_PIE_OT_switch_array,
    MODIFIER_PIE_OT_add_array_quick,
    MODIFIER_PIE_OT_delete_array_quick,
    MODIFIER_PIE_OT_apply_modifier_array,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
