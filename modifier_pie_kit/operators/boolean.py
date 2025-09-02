import bpy

from bpy.types import Operator

def auto_wireframe_update(self, context):
    """타겟 오브젝트 변경 시 자동 와이어프레임 적용"""
    obj = context.active_object
    if not obj or obj.type != 'MESH':
        return
    for mod in obj.modifiers:
        if mod.type == 'BOOLEAN' and mod.operand_type == 'OBJECT' and mod.object:
            if mod.object != obj and mod.object.type == 'MESH':
                set_wireframe_with_flag(mod.object)
                print(f"자동 와이어프레임 적용: {mod.object.name}")

def set_wireframe_with_flag(obj):
    """와이어프레임 설정과 함께 플래그 저장"""
    try:
        if obj and obj.name in bpy.data.objects:
            if obj.get('original_display_type') is None:
                obj['original_display_type'] = obj.display_type
            obj['boolean_wireframe'] = True
            obj.display_type = 'WIRE'
    except Exception as e:
        print(f"와이어프레임 설정 오류: {e}")

class MODIFIER_PIE_OT_add_boolean_popup(bpy.types.Operator):
    bl_idname = "modifier_pie.add_boolean_popup"
    bl_label = "Add Boolean Modifier"
    bl_description = "선택한 오브젝트에 Boolean 모디파이어를 추가하고 설정창을 엽니다. 타겟 오브젝트는 자동으로 와이어프레임으로 표시됩니다"
    bl_options = {'REGISTER', 'UNDO'}

    selected_modifier_index: bpy.props.IntProperty(default=0)

    _current_popup = None

    @classmethod
    def poll(cls, context):
        return (
            context.mode == 'OBJECT' and
            context.active_object is not None and
            context.active_object.type == 'MESH'
        )

    def invoke(self, context, event):
        if MODIFIER_PIE_OT_add_boolean_popup._current_popup is not None:
            try:
                MODIFIER_PIE_OT_add_boolean_popup._current_popup.cancel(context)
            except:
                pass
            MODIFIER_PIE_OT_add_boolean_popup._current_popup = None

        obj = context.active_object
        bool_mods = [m for m in obj.modifiers if m.type == 'BOOLEAN']
        if not bool_mods:
            obj.modifiers.new(name="Boolean", type='BOOLEAN')
            self.selected_modifier_index = 0
        else:
            if self.selected_modifier_index >= len(bool_mods):
                self.selected_modifier_index = 0

        MODIFIER_PIE_OT_add_boolean_popup._current_popup = self
        return context.window_manager.invoke_props_dialog(self, width=400)

    def check(self, context):
        obj = context.active_object
        bool_mods = [m for m in obj.modifiers if m.type == 'BOOLEAN']
        if bool_mods and self.selected_modifier_index < len(bool_mods):
            bpy.ops.ed.undo_push(message="Boolean Modifier Update")
            context.view_layer.update()
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()
            return True
        return False

    def execute(self, context):
        if MODIFIER_PIE_OT_add_boolean_popup._current_popup == self:
            MODIFIER_PIE_OT_add_boolean_popup._current_popup = None
        return {'FINISHED'}

    def cancel(self, context):
        if MODIFIER_PIE_OT_add_boolean_popup._current_popup == self:
            MODIFIER_PIE_OT_add_boolean_popup._current_popup = None
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
        bool_mods = [m for m in obj.modifiers if m.type == 'BOOLEAN']

        if not bool_mods:
            layout.label(text="No Boolean modifiers", icon='INFO')
            return

        if self.selected_modifier_index >= len(bool_mods):
            self.selected_modifier_index = len(bool_mods) - 1

        current_mod = bool_mods[self.selected_modifier_index]

        row = layout.row(align=True)
        row.label(text="Booleans:", icon='MOD_BOOLEAN')
        for i in range(len(bool_mods)):
            if i == self.selected_modifier_index:
                op = row.operator("modifier_pie.switch_boolean", text=f"●{i+1}", depress=True)
            else:
                op = row.operator("modifier_pie.switch_boolean", text=str(i+1))
            op.target_index = i
        row.separator()
        row.operator("modifier_pie.add_boolean_quick", text="", icon='ADD')

        layout.prop(current_mod, "operation", expand=True)
        layout.prop(current_mod, "operand_type")
        if current_mod.operand_type == 'OBJECT':
            target_row = layout.row()
            target_row.prop(current_mod, "object", text="Target Object (Auto Wireframe)")
            if current_mod.object and current_mod.object != obj:
                status_row = layout.row()
                status_row.label(text=f"✓ 와이어프레임 적용됨: {current_mod.object.name}", icon='CHECKMARK')
        elif current_mod.operand_type == 'COLLECTION':
            layout.prop(current_mod, "collection", text="Target Collection")
            if current_mod.collection:
                wire_row = layout.row()
                wire_row.operator("modifier_pie.set_wireframe_collection", text="Set Collection Wireframe", icon='SHADING_WIRE').mod_name = current_mod.name

        layout.separator()
        action_row = layout.row(align=True)
        action_row.operator("modifier_pie.apply_modifier_boolean_keep_wire", text="Apply This Boolean", icon='CHECKMARK').mod_name = current_mod.name
        

class MODIFIER_PIE_OT_switch_boolean(bpy.types.Operator):
    bl_idname = "modifier_pie.switch_boolean"
    bl_label = "Switch Boolean Modifier"
    bl_description = "팝업창에 표시할 Boolean 모디파이어를 전환합니다"
    target_index: bpy.props.IntProperty()

    def execute(self, context):
        if MODIFIER_PIE_OT_add_boolean_popup._current_popup:
            MODIFIER_PIE_OT_add_boolean_popup._current_popup.selected_modifier_index = self.target_index
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()
        return {'FINISHED'}

class MODIFIER_PIE_OT_add_boolean_quick(bpy.types.Operator):
    bl_idname = "modifier_pie.add_boolean_quick"
    bl_label = "Add New Boolean Modifier"
    bl_description = "활성 오브젝트에 새로운 Boolean 모디파이어를 추가합니다"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        bool_mods = [m for m in obj.modifiers if m.type == 'BOOLEAN']
        mod = obj.modifiers.new(name="Boolean", type='BOOLEAN')
        print(f"새 Boolean 추가: {mod.name}")

        if MODIFIER_PIE_OT_add_boolean_popup._current_popup:
            MODIFIER_PIE_OT_add_boolean_popup._current_popup.selected_modifier_index = len(bool_mods)
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()
        return {'FINISHED'}

class MODIFIER_PIE_OT_reset_target_wireframe(bpy.types.Operator):
    bl_idname = "modifier_pie.reset_target_wireframe"
    bl_label = "Reset Target Wireframe Display"
    bl_description = "Boolean 모디파이어의 타겟 오브젝트 또는 컬렉션의 와이어프레임 표시를 원래 상태로 되돌립니다"
    bl_options = {'REGISTER', 'UNDO'}

    mod_name: bpy.props.StringProperty()

    def execute(self, context):
        obj = context.active_object
        if not obj:
            return {'CANCELLED'}
        mod = obj.modifiers.get(self.mod_name)
        if mod and mod.type == 'BOOLEAN':
            if mod.operand_type == 'OBJECT' and mod.object:
                self.safe_reset_display(mod.object)
                self.report({'INFO'}, f"와이어프레임 리셋: {mod.object.name}")
            elif mod.operand_type == 'COLLECTION' and mod.collection:
                for target_obj in mod.collection.objects:
                    if target_obj.type == 'MESH':
                        self.safe_reset_display(target_obj)
                self.report({'INFO'}, f"컬렉션 와이어프레임 리셋: {mod.collection.name}")
        return {'FINISHED'}

    def safe_reset_display(self, obj):
        """안전한 방법으로 오브젝트 디스플레이 복원"""
        try:
            if obj and obj.name in bpy.data.objects:
                original_type = obj.get('original_display_type')
                if original_type is not None:
                    obj.display_type = original_type
                    del obj['original_display_type']
                else:
                    obj.display_type = 'TEXTURED'
                if obj.get('boolean_wireframe'):
                    del obj['boolean_wireframe']
        except Exception as e:
            print(f"디스플레이 복원 오류: {e}")

class MODIFIER_PIE_OT_apply_modifier_boolean_keep_wire(bpy.types.Operator):
    bl_idname = "modifier_pie.apply_modifier_boolean_keep_wire"
    bl_label = "Apply Boolean & Keep Wireframe"
    bl_description = "현재 Boolean 모디파이어를 적용합니다. 타겟 오브젝트의 와이어프레임 표시는 유지됩니다"
    bl_options = {'REGISTER', 'UNDO'}

    mod_name: bpy.props.StringProperty()

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "활성 오브젝트가 메시가 아닙니다.")
            return {'CANCELLED'}
        mod = obj.modifiers.get(self.mod_name)
        if not mod or mod.type != 'BOOLEAN':
            self.report({'WARNING'}, "Boolean 모디파이어를 찾을 수 없습니다.")
            return {'CANCELLED'}

        if mod.operand_type == 'OBJECT':
            if not mod.object:
                self.report({'ERROR'}, "타겟 오브젝트가 설정되지 않았습니다.")
                return {'CANCELLED'}
            if mod.object == obj:
                self.report({'ERROR'}, "자기 자신을 타겟으로 설정할 수 없습니다.")
                return {'CANCELLED'}
        elif mod.operand_type == 'COLLECTION':
            if not mod.collection:
                self.report({'ERROR'}, "타겟 컬렉션이 설정되지 않았습니다.")
                return {'CANCELLED'}

        wireframe_objects = []
        try:
            if mod.operand_type == 'OBJECT' and mod.object:
                if mod.object.get('boolean_wireframe'):
                    wireframe_objects.append(mod.object)
            elif mod.operand_type == 'COLLECTION' and mod.collection:
                for target_obj in mod.collection.objects:
                    if target_obj and target_obj.type == 'MESH' and target_obj.get('boolean_wireframe'):
                        wireframe_objects.append(target_obj)
        except Exception as e:
            print(f"와이어프레임 오브젝트 수집 오류: {e}")

        try:
            bpy.ops.object.modifier_apply(modifier=mod.name)
            self.report({'INFO'}, f"Boolean 모디파이어 '{mod.name}'이 적용되었습니다.")
        except Exception as e:
            self.report({'ERROR'}, f"모디파이어 적용 실패: {str(e)}")
            return {'CANCELLED'}

        for wire_obj in wireframe_objects:
            try:
                if wire_obj and wire_obj.name in bpy.data.objects:
                    wire_obj.display_type = 'WIRE'
                    wire_obj['boolean_wireframe'] = True
            except Exception as e:
                print(f"와이어프레임 유지 오류: {e}")

        if wireframe_objects:
            self.report({'INFO'}, f"와이어프레임 유지: {len(wireframe_objects)}개 오브젝트")
        return {'FINISHED'}

class MODIFIER_PIE_OT_set_wireframe_collection(bpy.types.Operator):
    bl_idname = "modifier_pie.set_wireframe_collection"
    bl_label = "Set Collection as Wireframe"
    bl_description = "Boolean 모디파이어의 타겟 컬렉션에 포함된 모든 오브젝트를 와이어프레임으로 표시합니다"
    bl_options = {'REGISTER', 'UNDO'}

    mod_name: bpy.props.StringProperty()

    def execute(self, context):
        obj = context.active_object
        if not obj:
            return {'CANCELLED'}
        mod = obj.modifiers.get(self.mod_name)
        if mod and mod.collection:
            count = 0
            for target_obj in mod.collection.objects:
                if target_obj and target_obj.type == 'MESH' and target_obj != obj:
                    set_wireframe_with_flag(target_obj)
                    count += 1
            self.report({'INFO'}, f"와이어프레임 설정: {count}개 오브젝트")
        return {'FINISHED'}

@bpy.app.handlers.persistent
def boolean_target_update_handler(scene, depsgraph):
    """Boolean 타겟 변경 감지 및 자동 와이어프레임 적용"""
    try:
        context = bpy.context
        if not context.active_object:
            return
        obj = context.active_object
        if obj.type != 'MESH':
            return
        for mod in obj.modifiers:
            if mod.type == 'BOOLEAN' and mod.operand_type == 'OBJECT':
                if mod.object and mod.object != obj and mod.object.type == 'MESH':
                    if mod.object.display_type != 'WIRE':
                        set_wireframe_with_flag(mod.object)
    except Exception as e:
        print(f"자동 와이어프레임 핸들러 오류: {e}")

classes = (
    MODIFIER_PIE_OT_add_boolean_popup,
    MODIFIER_PIE_OT_switch_boolean,
    MODIFIER_PIE_OT_add_boolean_quick,
    MODIFIER_PIE_OT_reset_target_wireframe,
    MODIFIER_PIE_OT_apply_modifier_boolean_keep_wire,
    MODIFIER_PIE_OT_set_wireframe_collection,
)

def register():
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
            print(f"✓ 등록 성공: {cls.__name__}")
        except Exception as e:
            print(f"✗ 등록 실패: {cls.__name__} - {e}")
    if boolean_target_update_handler not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(boolean_target_update_handler)

def unregister():
    if boolean_target_update_handler in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(boolean_target_update_handler)
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
            print(f"✓ 해제 성공: {cls.__name__}")
        except Exception as e:
            print(f"✗ 해제 실패: {cls.__name__} - {e}")

if __name__ == "__main__":
    register()