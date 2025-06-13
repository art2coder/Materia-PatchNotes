import bpy
import math
from mathutils import Euler, Vector

# ─────────────────────────────────────────────
# 회전 어레이
# ─────────────────────────────────────────────

class OBJECT_OT_rotational_array(bpy.types.Operator):
    """3D 커서 기준 회전 어레이 (축 선택 포함)"""
    bl_idname = "modifier_pie.rotational_array"
    bl_label = "Rotational Array"
    bl_options = {'REGISTER', 'UNDO'}

    count: bpy.props.IntProperty(
        name="Count",
        default=6,
        min=1
    )

    axis: bpy.props.EnumProperty(
        name="Axis",
        items=[
            ('X', "X Axis", "Rotate around X Axis"),
            ('Y', "Y Axis", "Rotate around Y Axis"),
            ('Z', "Z Axis", "Rotate around Z Axis")
        ],
        default='Z'
    )

    @classmethod
    def poll(cls, context):
        return (
            context.mode == 'OBJECT' and
            context.active_object is not None and
            len(context.selected_objects) == 1 and
            context.active_object.type == 'MESH'
        )

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.prop(self, "axis", expand=True)
        layout.prop(self, "count")

    def execute(self, context):
        obj = context.active_object
        cursor = context.scene.cursor.location.copy()

        # 1) Apply transforms and move origin to 3D cursor
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR')

        # 2) Create rotation empty at cursor
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=cursor)
        empty_rotation = context.active_object
        empty_rotation.name = f"RotArray_Empty_{obj.name}"

        # 3) Add array modifier
        if "RotationalArray" in obj.modifiers:
            obj.modifiers.remove(obj.modifiers["RotationalArray"])
        mod = obj.modifiers.new("RotationalArray", 'ARRAY')
        mod.use_relative_offset = False
        mod.use_object_offset = True
        mod.offset_object = empty_rotation
        mod.count = self.count

        # 4) Set initial rotation on the empty
        rot_angle = math.radians(360.0 / self.count)
        if self.axis == 'X':
            empty_rotation.rotation_euler = Euler((rot_angle, 0, 0), 'XYZ')
            drv_index = 0
        elif self.axis == 'Y':
            empty_rotation.rotation_euler = Euler((0, rot_angle, 0), 'XYZ')
            drv_index = 1
        else:
            empty_rotation.rotation_euler = Euler((0, 0, rot_angle), 'XYZ')
            drv_index = 2

        # 5) Add driver to update rotation dynamically
        drv = empty_rotation.driver_add("rotation_euler", drv_index).driver
        var = drv.variables.new()
        var.name = "cnt"
        var.targets[0].id_type = 'OBJECT'
        var.targets[0].id = obj
        var.targets[0].data_path = f'modifiers["{mod.name}"].count'
        drv.expression = "radians(360/cnt)"

        # 6) Parent empty to object for grouped transform
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        empty_rotation.select_set(True)
        context.view_layer.objects.active = obj
        bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)

        self.report({'INFO'}, f"Rotational array created around {self.axis}-axis.")
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

# ─────────────────────────────────────────────
# Boolean Modifier
# ─────────────────────────────────────────────

class OBJECT_OT_add_boolean_popup(bpy.types.Operator):
    """Boolean Modifier"""
    bl_idname = "modifier_pie.add_boolean_popup"
    bl_label = "Boolean Modifier Settings"
    bl_options = {'UNDO'}

    mod = None
    target_object = None
    
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
            # 타겟 오브젝트가 변경되었는지 확인하고 와이어프레임 설정 버튼 추가
            if self.mod.object and self.mod.object != context.active_object:
                if self.target_object != self.mod.object:
                    self.target_object = self.mod.object
                layout.operator("modifier_pie.set_wireframe", text="Set Wireframe", icon='SHADING_WIRE')
        elif self.mod.operand_type == 'COLLECTION':
            layout.prop(self.mod, "collection", text="Target Collection")
            if self.mod.collection:
                layout.operator("modifier_pie.set_wireframe_collection", text="Set Collection Wireframe", icon='SHADING_WIRE')
        
        layout.separator()
        layout.operator("modifier_pie.apply_modifier_boolean", text="Apply", icon='CHECKMARK')
        layout.operator("modifier_pie.reset_wireframe", text="Reset Display", icon='RESTRICT_VIEW_OFF')

    def execute(self, context):
        return {'FINISHED'}

class OBJECT_OT_set_wireframe(bpy.types.Operator):
    bl_idname = "modifier_pie.set_wireframe"
    bl_label = "Set Target Wireframe"

    def execute(self, context):
        mod = next((m for m in context.object.modifiers if m.type == 'BOOLEAN'), None)
        if mod and mod.object:
            self.set_wireframe_display(mod.object, True)
        return {'FINISHED'}
    
    def set_wireframe_display(self, obj, wireframe=True):
        """오브젝트의 디스플레이 타입을 와이어프레임으로 설정"""
        if wireframe:
            # 안전한 방법으로 커스텀 프로퍼티 확인 및 설정
            if obj.get('original_display_type') is None:
                obj['original_display_type'] = obj.display_type
            obj.display_type = 'WIRE'

class OBJECT_OT_set_wireframe_collection(bpy.types.Operator):
    bl_idname = "modifier_pie.set_wireframe_collection"
    bl_label = "Set Collection Wireframe"

    def execute(self, context):
        mod = next((m for m in context.object.modifiers if m.type == 'BOOLEAN'), None)
        if mod and mod.collection:
            for obj in mod.collection.objects:
                if obj.type == 'MESH' and obj != context.active_object:
                    self.set_wireframe_display(obj, True)
        return {'FINISHED'}
    
    def set_wireframe_display(self, obj, wireframe=True):
        """오브젝트의 디스플레이 타입을 와이어프레임으로 설정"""
        if wireframe:
            if obj.get('original_display_type') is None:
                obj['original_display_type'] = obj.display_type
            obj.display_type = 'WIRE'

class OBJECT_OT_apply_modifier_boolean(bpy.types.Operator):
    bl_idname = "modifier_pie.apply_modifier_boolean"
    bl_label = "Apply Boolean Modifier"

    def execute(self, context):
        mod = next((m for m in context.object.modifiers if m.type == 'BOOLEAN'), None)
        if not mod:
            self.report({'WARNING'}, "No Boolean modifier found.")
            return {'CANCELLED'}
        
        # 모디파이어 적용 전에 타겟 오브젝트의 디스플레이 복원
        if mod.operand_type == 'OBJECT' and mod.object:
            self.reset_display(mod.object)
        elif mod.operand_type == 'COLLECTION' and mod.collection:
            for obj in mod.collection.objects:
                if obj.type == 'MESH':
                    self.reset_display(obj)
        
        bpy.ops.object.modifier_apply(modifier=mod.name)
        return {'FINISHED'}
    
    def reset_display(self, obj):
        """오브젝트의 디스플레이를 원래대로 복원"""
        original_type = obj.get('original_display_type')
        if original_type is not None:
            obj.display_type = original_type
            del obj['original_display_type']
        else:
            obj.display_type = 'TEXTURED'

class OBJECT_OT_reset_wireframe(bpy.types.Operator):
    bl_idname = "modifier_pie.reset_wireframe"
    bl_label = "Reset Wireframe Display"

    def execute(self, context):
        mod = next((m for m in context.object.modifiers if m.type == 'BOOLEAN'), None)
        if not mod:
            return {'CANCELLED'}
        
        if mod.operand_type == 'OBJECT' and mod.object:
            self.reset_display(mod.object)
        elif mod.operand_type == 'COLLECTION' and mod.collection:
            for obj in mod.collection.objects:
                if obj.type == 'MESH':
                    self.reset_display(obj)
        
        return {'FINISHED'}
    
    def reset_display(self, obj):
        """오브젝트의 디스플레이를 원래대로 복원"""
        original_type = obj.get('original_display_type')
        if original_type is not None:
            obj.display_type = original_type
            del obj['original_display_type']
        else:
            obj.display_type = 'TEXTURED'

# ─────────────────────────────────────────────
#  Bevel Modifier
# ─────────────────────────────────────────────

class OBJECT_OT_add_bevel_popup(bpy.types.Operator):
    """Bevel Modifier"""
    bl_idname = "modifier_pie.add_bevel_popup"
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
        layout.operator("modifier_pie.apply_modifier_bevel", text="Apply", icon='CHECKMARK')

    def execute(self, context):
        return {'FINISHED'}

class OBJECT_OT_apply_modifier_bevel(bpy.types.Operator):
    bl_idname = "modifier_pie.apply_modifier_bevel"
    bl_label = "Apply Bevel Modifier"

    def execute(self, context):
        mod = next((m for m in context.object.modifiers if m.type == 'BEVEL'), None)
        if not mod:
            self.report({'WARNING'}, "No Bevel modifier found.")
            return {'CANCELLED'}
        bpy.ops.object.modifier_apply(modifier=mod.name)
        return {'FINISHED'}


# ─────────────────────────────────────────────
# 미러 
# ─────────────────────────────────────────────

def update_mirror_modifier(self, context):
    name_base = "- Mirror_Origin"
    origin = Vector((0.0, 0.0, 0.0))
    empty = None
    # 원점에 위치한 동일 이름 엠프티가 없을 때만 새로 생성
    for obj in bpy.data.objects:
        if obj.name.startswith(name_base) and (obj.location - origin).length < 1e-4:
            empty = obj
            break
    if not empty:
        empty = bpy.data.objects.new(name_base, None)
        empty.empty_display_type = 'ARROWS'
        empty.empty_display_size = 0.5
        empty.location = origin
        context.collection.objects.link(empty)

    # 선택된 메쉬에 Mirror 모디파이어 미리 적용
    for obj in context.selected_objects:
        if obj.type != 'MESH':
            continue
        mod = obj.modifiers.get("Mirror")
        if not mod:
            mod = obj.modifiers.new(name="Mirror", type='MIRROR')
        mod.use_axis = (self.use_x, self.use_y, self.use_z)
        mod.mirror_object = empty

    # Undo 기록 한 번만
    if not getattr(self, '_undo_pushed', False):
        bpy.ops.ed.undo_push(message="Mirror Preview")
        self._undo_pushed = True


class OBJECT_OT_mirror_live_popup(bpy.types.Operator):
    bl_idname = "modifier_pie.mirror_live_popup"
    bl_label = "Mirror Live Popup"
    bl_options = {'REGISTER', 'UNDO'}

    use_x: bpy.props.BoolProperty(name="X Axis", default=True, update=update_mirror_modifier)
    use_y: bpy.props.BoolProperty(name="Y Axis", default=False, update=update_mirror_modifier)
    use_z: bpy.props.BoolProperty(name="Z Axis", default=False, update=update_mirror_modifier)

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and any(o.type == 'MESH' for o in context.selected_objects)

    def invoke(self, context, event):
        # 초기화
        if hasattr(self, '_undo_pushed'):
            del self._undo_pushed
        update_mirror_modifier(self, context)
        # 다이얼로그로 표시: OK/Cancel 기본 버튼 포함
        return context.window_manager.invoke_props_dialog(self, width=240)

    def draw(self, context):
        layout = self.layout
        layout.label(text="Mirror Axes:")
        row = layout.row(align=True)
        row.prop(self, "use_x", toggle=True)
        row.prop(self, "use_y", toggle=True)
        row.prop(self, "use_z", toggle=True)
        layout.separator()
        # Apply 버튼이 실행될 때 모디파이어 확정
        layout.operator("modifier_pie.confirm_mirror_and_apply", text="Apply", icon='CHECKMARK')

    def execute(self, context):
        # 다이얼로그 OK 버튼은 미리보기 그대로 유지
        return {'FINISHED'}

class OBJECT_OT_confirm_mirror_and_apply(bpy.types.Operator):
    """Apply Mirror Modifier"""
    bl_idname = "modifier_pie.confirm_mirror_and_apply"
    bl_label = "Apply Mirror"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue
            for mod in obj.modifiers:
                if mod.type == 'MIRROR':
                    context.view_layer.objects.active = obj
                    bpy.ops.object.modifier_apply(modifier=mod.name)
                    break
        self.report({'INFO'}, "Mirror modifier applied.")
        return {'FINISHED'}

    
# ─────────────────────────────────────────────
# Apply All Common Modifiers
# ─────────────────────────────────────────────

class OBJECT_OT_apply_all_common_modifiers(bpy.types.Operator):
    """This apply works only through the add-on"""
    bl_idname = "modifier_pie.apply_all_common_modifiers"
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
# Move_Bottom Modifiers
# ─────────────────────────────────────────────

class OBJECT_OT_move_bottom_to_z0(bpy.types.Operator):
    bl_idname = "modifier_pi.move_bottom_to_z0"
    bl_label = "Move Bottom"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue

            # 월드 공간에서 바닥면 계산
            bbox = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
            min_z = min(v.z for v in bbox)
            delta_z = -min_z

            # 이동 적용
            obj.location.z += delta_z

        return {'FINISHED'}

# ─────────────────────────────────────────────    
# Subsurf Modifier 
# ─────────────────────────────────────────────

class OBJECT_OT_add_subsurf_popup(bpy.types.Operator):
    """Subdivision Surface Modifier"""
    bl_idname = "modifier_pie.add_subsurf_popup"
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
        layout.operator("modifier_pie.apply_modifier_subsurf", text="Apply", icon='CHECKMARK')

    def execute(self, context):
        return {'FINISHED'}

class OBJECT_OT_apply_modifier_subsurf(bpy.types.Operator):
    bl_idname = "modifier_pie.apply_modifier_subsurf"
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
    bl_idname = "modifier_pie.toggle_display_wire"
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
     
     # Boolean
    OBJECT_OT_add_boolean_popup,
    OBJECT_OT_set_wireframe,
    OBJECT_OT_set_wireframe_collection,
    OBJECT_OT_apply_modifier_boolean,
    OBJECT_OT_reset_wireframe,

    # Bevel
    OBJECT_OT_add_bevel_popup,
    OBJECT_OT_apply_modifier_bevel,

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

    OBJECT_OT_rotational_array,

    OBJECT_OT_move_bottom_to_z0,
    
)        

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
