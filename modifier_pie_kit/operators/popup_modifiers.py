import bpy
import math
import bmesh
from mathutils import Euler, Vector
from bpy.types import Operator


# ─────────────────────────────────────────────
# 회전 어레이
# ─────────────────────────────────────────────

class MODIFIER_PIE_OT_rotational_array(bpy.types.Operator):
    """3D 커서 기준 회전 어레이 (축 선택 포함)"""
    bl_idname = "modifier_pie.rotational_array"
    bl_label = "Rotational Array"
    bl_description = "활성 오브젝트를 3D 커서 기준으로 회전 복사하여 원형 배열을 만듭니다"
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
#  Bevel Modifier
# ─────────────────────────────────────────────

class MODIFIER_PIE_OT_add_bevel_popup(bpy.types.Operator):
    bl_idname = "modifier_pie.add_bevel_popup"
    bl_label = "Add Bevel Modifier"
    bl_description = "선택한 오브젝트에 Bevel 모디파이어를 추가하고 설정창을 엽니다. 모서리를 부드럽게 깎습니다"
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

class MODIFIER_PIE_OT_apply_modifier_bevel(bpy.types.Operator):
    bl_idname = "modifier_pie.apply_modifier_bevel"
    bl_label = "Apply Bevel Modifier"
    bl_description = "Bevel 모디파이어를 적용합니다"

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
    for obj in context.selected_objects:
        if obj.type != 'MESH':
            continue
        mod = obj.modifiers.get("Mirror")
        if not mod:
            mod = obj.modifiers.new(name="Mirror", type='MIRROR')
        mod.use_axis = (self.use_x, self.use_y, self.use_z)
        
    if not getattr(self, '_undo_pushed', False):
        bpy.ops.ed.undo_push(message="Mirror Preview")
        self._undo_pushed = True


class MODIFIER_PIE_OT_mirror_live_popup(bpy.types.Operator):
    bl_idname = "modifier_pie.mirror_live_popup"
    bl_label = "Add Mirror Modifier"
    bl_description = "선택한 오브젝트에 Mirror 모디파이어를 추가하고 실시간으로 축을 설정하는 창을 엽니다"
    bl_options = {'REGISTER', 'UNDO'}

    use_x: bpy.props.BoolProperty(name="X Axis", default=True, update=update_mirror_modifier)
    use_y: bpy.props.BoolProperty(name="Y Axis", default=False, update=update_mirror_modifier)
    use_z: bpy.props.BoolProperty(name="Z Axis", default=False, update=update_mirror_modifier)

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and any(o.type == 'MESH' for o in context.selected_objects)

    def invoke(self, context, event):
        if hasattr(self, '_undo_pushed'):
            del self._undo_pushed
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
        layout.operator("modifier_pie.confirm_mirror_and_apply", text="Apply", icon='CHECKMARK')

    def execute(self, context):
        return {'FINISHED'}

class MODIFIER_PIE_OT_confirm_mirror_and_apply(bpy.types.Operator):
    bl_idname = "modifier_pie.confirm_mirror_and_apply"
    bl_label = "Apply Mirror Modifier"
    bl_description = "활성화된 Mirror 모디파이어를 적용합니다"
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
# Apply All Common Modifiers with Auto Cleanup
# ─────────────────────────────────────────────
class MODIFIER_PIE_OT_apply_all_common_modifiers(bpy.types.Operator):
    bl_idname = "modifier_pie.apply_all_common_modifiers"
    bl_label = "Apply Common Modifiers"
    bl_description = "선택한 모든 오브젝트의 주요 모디파이어(Bevel, Mirror, Subsurf 등)를 한 번에 적용합니다"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (
            context.mode == 'OBJECT' and
            len(context.selected_objects) > 0 and
            any(obj.type == 'MESH' and len(obj.modifiers) > 0 for obj in context.selected_objects)
        )
    
    def execute(self, context):
        selected_mesh_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        
        if not selected_mesh_objects:
            self.report({'WARNING'}, "No mesh objects selected.")
            return {'CANCELLED'}

        total_applied = []
        total_deleted = 0
        processed_objects = 0
        
        modifier_types = ['BOOLEAN', 'BEVEL', 'MIRROR', 'SUBSURF', 'ARRAY', 'SOLIDIFY', 'WIREFRAME', 'SCREW', 'REMESH', 'DISPLACE', 'DECIMATE']
        
        for obj in selected_mesh_objects:
            if len(obj.modifiers) == 0:
                continue
                
            context.view_layer.objects.active = obj
            
            has_remesh = any(m.type == 'REMESH' for m in obj.modifiers)
            has_displace = any(m.type == 'DISPLACE' for m in obj.modifiers)
            has_subsurf = any(m.type == 'SUBSURF' for m in obj.modifiers)
            skip_subsurf = has_remesh and has_displace and has_subsurf
            
            applied = []
            failed_modifiers = []
            
            print(f"\n=== 오브젝트 '{obj.name}' 처리 시작 ===")
            if skip_subsurf:
                print(f"특정 조합(Remesh + Displace + Subsurf) 감지: Subsurf 적용 스킵")
            
            for t in modifier_types:
                if skip_subsurf and t == 'SUBSURF':
                    print(f"Subsurf 타입 스킵: {obj.name}")
                    continue
                
                mods = [m for m in obj.modifiers if m.type == t]
                
                for mod in mods:
                    try:
                        if not mod.show_viewport:
                            mod.show_viewport = True
                            print(f"뷰포트 표시 활성화: {mod.name}")
                        
                        if not mod.show_render:
                            mod.show_render = True
                            print(f"렌더 표시 활성화: {mod.name}")
                        
                        if not self.validate_modifier(mod):
                            print(f"모디파이어 유효성 검사 실패: {mod.name}")
                            failed_modifiers.append(mod)
                            continue
                        
                        modifier_name = mod.name
                        bpy.ops.object.modifier_apply(modifier=modifier_name)
                        applied.append(mod.type.title())
                        print(f"모디파이어 적용 성공: {modifier_name}")
                        
                    except Exception as e:
                        print(f"모디파이어 적용 실패 - {mod.name}: {e}")
                        failed_modifiers.append(mod)

            deleted_count = self.cleanup_failed_modifiers(obj, failed_modifiers)
            
            total_applied.extend(applied)
            total_deleted += deleted_count
            if applied or deleted_count > 0:
                processed_objects += 1
            
            print(f"=== 오브젝트 '{obj.name}' 처리 완료 ===")

        messages = []
        if processed_objects > 0:
            messages.append(f"Processed {processed_objects} objects")
        if total_applied:
            unique_applied = list(set(total_applied))
            messages.append(f"Applied: {', '.join(unique_applied)}")
        if total_deleted > 0:
            messages.append(f"Cleaned up: {total_deleted} failed modifiers")
            
        if messages:
            self.report({'INFO'}, " | ".join(messages))
        else:
            self.report({'INFO'}, "No applicable modifiers found in selected objects.")
            
        return {'FINISHED'}
    
    def validate_modifier(self, mod):
        """모디파이어 유효성 검사"""
        try:
            if mod.type == 'BOOLEAN':
                if mod.operand_type == 'OBJECT':
                    if not mod.object:
                        print(f"Boolean 모디파이어 '{mod.name}': 타겟 오브젝트 없음")
                        return False
                    if not mod.object.name in bpy.data.objects:
                        print(f"Boolean 모디파이어 '{mod.name}': 타겟 오브젝트가 존재하지 않음")
                        return False
                elif mod.operand_type == 'COLLECTION':
                    if not mod.collection:
                        print(f"Boolean 모디파이어 '{mod.name}': 타겟 컬렉션 없음")
                        return False
                    if not mod.collection.name in bpy.data.collections:
                        print(f"Boolean 모디파이어 '{mod.name}': 타겟 컬렉션이 존재하지 않음")
                        return False
            
            elif mod.type == 'ARRAY':
                if hasattr(mod, 'count') and mod.count <= 0:
                    print(f"Array 모디파이어 '{mod.name}': 잘못된 카운트 값")
                    return False
            
            elif mod.type == 'MIRROR':
                pass
            
            elif mod.type == 'BEVEL':
                if hasattr(mod, 'width') and mod.width <= 0:
                    print(f"Bevel 모디파이어 '{mod.name}': 잘못된 너비 값")
                    return False
            
            elif mod.type == 'SUBSURF':
                pass
            
            elif mod.type == 'SOLIDIFY':
                if hasattr(mod, 'thickness') and mod.thickness == 0:
                    print(f"Solidify 모디파이어 '{mod.name}': 두께가 0")
                    return False
            
            return True
            
        except Exception as e:
            print(f"모디파이어 유효성 검사 중 오류 - {mod.name}: {e}")
            return False
    
    def cleanup_failed_modifiers(self, obj, failed_modifiers):
        """실패한 모디파이어 삭제"""
        deleted_count = 0
        
        for mod in failed_modifiers:
            try:
                if mod and mod.name in [m.name for m in obj.modifiers]:
                    modifier_name = mod.name
                    obj.modifiers.remove(mod)
                    deleted_count += 1
                    print(f"실패한 모디파이어 삭제: {modifier_name}")
            except Exception as e:
                print(f"모디파이어 삭제 실패 - {mod.name}: {e}")
        
        return deleted_count



# ─────────────────────────────────────────────
# Move_Bottom Modifiers
# ─────────────────────────────────────────────

class MODIFIER_PIE_OT_move_bottom_to_z0(bpy.types.Operator):
    bl_idname = "modifier_pie.move_bottom_to_z0"
    bl_label = "Drop to Ground"
    bl_description = "선택한 오브젝트의 가장 낮은 지점을 월드 바닥(Z=0)에 맞춥니다"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue

            bbox = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
            min_z = min(v.z for v in bbox)
            delta_z = -min_z

            obj.location.z += delta_z

        return {'FINISHED'}

# ─────────────────────────────────────────────    
# Subsurf Modifier 
# ─────────────────────────────────────────────

class MODIFIER_PIE_OT_add_subsurf_popup(bpy.types.Operator):
    bl_idname = "modifier_pie.add_subsurf_popup"
    bl_label = "Add Subdivision Surface"
    bl_description = "선택한 오브젝트에 Subdivision Surface 모디파이어를 추가하고 설정창을 엽니다. 메쉬를 부드럽게 만들고 면을 나눕니다"
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

        layout.prop(mod, "subdivision_type", expand=True, text="Type")
        layout.prop(mod, "levels", text="Viewport")
        layout.prop(mod, "render_levels", text="Render")
        layout.prop(mod, "uv_smooth", text="UV Smooth")

        layout.separator()
        layout.operator("modifier_pie.apply_modifier_subsurf", text="Apply", icon='CHECKMARK')

    def execute(self, context):
        return {'FINISHED'}

class MODIFIER_PIE_OT_apply_modifier_subsurf(bpy.types.Operator):
    bl_idname = "modifier_pie.apply_modifier_subsurf"
    bl_label = "Apply Subdivision Modifier"
    bl_description = "Subdivision Surface 모디파이어를 적용합니다"

    def execute(self, context):
        mod = next((m for m in context.object.modifiers if m.type == 'SUBSURF'), None)
        if not mod:
            self.report({'WARNING'}, "No Subsurf modifier found.")
            return {'CANCELLED'}
        bpy.ops.object.modifier_apply(modifier=mod.name)
        return {'FINISHED'}
    
# ─────────────────────────────────────────────
# Solidify Modifier
# ─────────────────────────────────────────────

class MODIFIER_PIE_OT_add_solidify_popup(bpy.types.Operator):
    bl_idname = "modifier_pie.add_solidify_popup"
    bl_label = "Add Solidify Modifier"
    bl_description = "선택한 오브젝트에 Solidify 모디파이어를 추가하고 설정창을 엽니다. 면에 두께를 부여합니다"
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
        self.mod = next((m for m in obj.modifiers if m.type == 'SOLIDIFY'), None)
        if not self.mod:
            self.mod = obj.modifiers.new(name="Solidify", type='SOLIDIFY')
            self.mod.thickness = 0.1
            self.mod.offset = -1.0
            self.mod.use_even_offset = True
            self.mod.use_rim = True
            self.mod.use_rim_only = False
        
        return context.window_manager.invoke_props_dialog(self, width=300)
    
    def draw(self, context):
        layout = self.layout
        mod = self.mod
        
        layout.prop(mod, "solidify_mode", text="Mode")
        layout.prop(mod, "thickness", text="Thickness")
        layout.prop(mod, "offset", text="Offset")
        layout.prop(mod, "use_even_offset", text="Even Thickness")
        
        layout.separator()
        layout.label(text="Rim:")
        layout.prop(mod, "use_rim", text="Fill")
        layout.prop(mod, "use_rim_only", text="Only Rim")
        
        layout.separator()
        layout.operator("modifier_pie.apply_modifier_solidify", text="Apply", icon='CHECKMARK')
    
    def execute(self, context):
        return {'FINISHED'}

class MODIFIER_PIE_OT_apply_modifier_solidify(bpy.types.Operator):
    bl_idname = "modifier_pie.apply_modifier_solidify"
    bl_label = "Apply Solidify Modifier"
    bl_description = "Solidify 모디파이어를 적용합니다"

    def execute(self, context):
        mod = next((m for m in context.object.modifiers if m.type == 'SOLIDIFY'), None)
        if not mod:
            self.report({'WARNING'}, "No Solidify modifier found.")
            return {'CANCELLED'}
        
        bpy.ops.object.modifier_apply(modifier=mod.name)
        return {'FINISHED'}


# ─────────────────────────────────────────────    
# Toggle_Display_Wire
# ─────────────────────────────────────────────
    
class MODIFIER_PIE_OT_toggle_display_wire(bpy.types.Operator):
    bl_idname = "modifier_pie.toggle_display_wire"
    bl_label = "Toggle Wireframe Display"
    bl_description = "선택한 오브젝트의 뷰포트 표시를 와이어프레임(Wireframe)과 텍스처(Solid) 모드 사이에서 전환합니다"
    bl_options = {'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return (
            context.mode == 'OBJECT' and
            any(obj.type == 'MESH' for obj in context.selected_objects)
        )

    def execute(self, context):
        is_wire = all(obj.display_type == 'WIRE' for obj in context.selected_objects)
        display_type = 'SOLID' if is_wire else 'WIRE'
        for obj in context.selected_objects:
            obj.display_type = display_type
        self.report({'INFO'}, f"Display set to {display_type}")
        return {'FINISHED'}
    

# ─────────────────────────────────────────────    
# Toggle_Overlay 
# ─────────────────────────────────────────────   


class VIEW3D_OT_toggle_overlay(bpy.types.Operator):
    bl_idname = "view3d.toggle_overlay"
    bl_label = "Toggle Overlays"
    bl_description = "3D 뷰포트의 오버레이(그리드, 축 등 안내선)를 켜고 끕니다"
    bl_options = {'UNDO'}

    def execute(self, context):
        space = context.space_data
        if space.type == 'VIEW_3D':
            space.overlay.show_overlays = not space.overlay.show_overlays
            self.report({'INFO'}, f"Overlays {'Enabled' if space.overlay.show_overlays else 'Disabled'}")
        return {'FINISHED'}

# ─────────────────────────────────────────────    
# 단일 버택스 생성
# ─────────────────────────────────────────────         
class MESH_VERTEX_OT_add_vertex_at_cursor(bpy.types.Operator):
    bl_idname = "mesh_vertex.add_vertex_at_cursor"
    bl_label = "Add Single Vertex"
    bl_description = "오브젝트 또는 에디트 모드에서 3D 커서 위치에 단일 버텍스를 생성합니다"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'
    
    def execute(self, context):
        cursor_location = context.scene.cursor.location.copy()
        
        if context.mode == 'EDIT_MESH':
            obj = context.active_object
            cursor_local = obj.matrix_world.inverted() @ cursor_location
            
            bm = bmesh.from_edit_mesh(obj.data)
            new_vert = bm.verts.new(cursor_local)
            bm.verts.ensure_lookup_table()
            
            bm.select_flush_mode()
            for v in bm.verts:
                v.select = False
            new_vert.select = True
            
            bmesh.update_edit_mesh(obj.data)
            self.report({'INFO'}, f"기존 메시에 버텍스 추가: {cursor_local}")
            
        else:
            mesh = bpy.data.meshes.new("Vertex")
            
            bm = bmesh.new()
            bm.verts.new((0, 0, 0))
            bm.to_mesh(mesh)
            bm.free()
            
            obj = bpy.data.objects.new("Vertex", mesh)
            obj.location = cursor_location
            
            context.collection.objects.link(obj)
            
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            context.view_layer.objects.active = obj
            
            self.report({'INFO'}, f"새 버텍스 오브젝트 생성: {cursor_location}")
        
        return {'FINISHED'}

# ─────────────────────────────────────────────
# Remesh Modifier
# ─────────────────────────────────────────────

class MODIFIER_PIE_OT_add_remesh_popup(bpy.types.Operator):
    bl_idname = "modifier_pie.add_remesh_popup"
    bl_label = "Add Remesh Modifier"
    bl_description = "선택한 오브젝트에 Remesh 모디파이어를 추가하고 설정창을 엽니다. 메쉬의 토폴로지를 재구성합니다"
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
        self.mod = next((m for m in obj.modifiers if m.type == 'REMESH'), None)
        if not self.mod:
            self.mod = obj.modifiers.new(name="Remesh", type='REMESH')
            self.mod.mode = 'VOXEL'
            self.mod.voxel_size = 0.1
        
        return context.window_manager.invoke_props_dialog(self, width=300)
    
    def draw(self, context):
        layout = self.layout
        mod = self.mod
        
        layout.prop(mod, "mode", text="Mode")
        
        if mod.mode == 'VOXEL':
            layout.prop(mod, "voxel_size", text="Voxel Size")
            layout.prop(mod, "adaptivity", text="Adaptivity")
        else:
            layout.prop(mod, "octree_depth", text="Octree Depth")
            layout.prop(mod, "scale", text="Scale")
            
            if mod.mode == 'SMOOTH':
                layout.prop(mod, "sharpness", text="Sharpness")
        
        layout.separator()
        
        layout.prop(mod, "use_remove_disconnected", text="Remove Disconnected")
        if mod.use_remove_disconnected:
            layout.prop(mod, "threshold", text="Threshold")
        
        layout.prop(mod, "use_smooth_shade", text="Smooth Shading")
        
        layout.separator()
        layout.operator("modifier_pie.apply_modifier_remesh", text="Apply", icon='CHECKMARK')
    
    def execute(self, context):
        return {'FINISHED'}

class MODIFIER_PIE_OT_apply_modifier_remesh(bpy.types.Operator):
    bl_idname = "modifier_pie.apply_modifier_remesh"
    bl_label = "Apply Remesh Modifier"
    bl_description = "Remesh 모디파이어를 적용합니다"

    def execute(self, context):
        mod = next((m for m in context.object.modifiers if m.type == 'REMESH'), None)
        if not mod:
            self.report({'WARNING'}, "No Remesh modifier found.")
            return {'CANCELLED'}
        
        bpy.ops.object.modifier_apply(modifier=mod.name)
        return {'FINISHED'}

# ─────────────────────────────────────────────
# Displace Modifier
# ─────────────────────────────────────────────

class MODIFIER_PIE_OT_add_displace_popup(bpy.types.Operator):
    bl_idname = "modifier_pie.add_displace_popup"
    bl_label = "Add Displace Modifier"
    bl_description = "선택한 오브젝트에 Displace 모디파이어를 추가하고 설정창을 엽니다. 텍스처를 이용해 메쉬를 변형시킵니다"
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
        self.mod = next((m for m in obj.modifiers if m.type == 'DISPLACE'), None)
        if not self.mod:
            self.mod = obj.modifiers.new(name="Displace", type='DISPLACE')
            self.mod.strength = 0.1
            self.mod.direction = 'NORMAL'
        
        return context.window_manager.invoke_props_dialog(self, width=300)
    
    def draw(self, context):
        layout = self.layout
        mod = self.mod
        
        row = layout.row()
        row.prop(mod, "texture", text="Texture")
        row.operator("modifier_pie.create_new_texture", text="새 텍스처 만들기")
        
        if mod.texture:
            layout.separator()
            layout.prop(mod.texture, "type", text="Type")
            layout.template_preview(mod.texture)
            
            if mod.texture.type == 'CLOUDS':
                layout.prop(mod.texture, "noise_basis", text="Noise Basis")
                layout.prop(mod.texture, "noise_type", text="Type")
                layout.prop(mod.texture, "cloud_type", text="Color")
                layout.prop(mod.texture, "noise_scale", text="Size")
                layout.prop(mod.texture, "noise_depth", text="Depth")
                layout.prop(mod.texture, "nabla", text="Nabla")
            elif mod.texture.type == 'IMAGE':
                layout.prop(mod.texture, "image", text="")

        layout.separator()
        
        layout.prop(mod, "texture_coords", text="Coordinates")
        if mod.texture_coords == 'OBJECT':
            layout.prop(mod, "texture_coords_object", text="Object")
        elif mod.texture_coords == 'UV':
            layout.prop_search(mod, "uv_layer", context.object.data, "uv_layers", text="UV Map")
        
        layout.separator()
        
        layout.prop(mod, "direction", text="Direction")
        layout.prop(mod, "strength", text="Strength")
        layout.prop(mod, "mid_level", text="Midlevel")
        
        layout.separator()
        
        layout.prop_search(mod, "vertex_group", context.object, "vertex_groups", text="Vertex Group")
        
        layout.separator()
        layout.operator("modifier_pie.apply_modifier_displace", text="Apply", icon='CHECKMARK')
    
    def execute(self, context):
        return {'FINISHED'}

class MODIFIER_PIE_OT_create_new_texture(bpy.types.Operator):
    bl_idname = "modifier_pie.create_new_texture"
    bl_label = "Create New Texture"
    bl_description = "Displace 모디파이어를 위한 새로운 텍스처를 생성합니다"

    def execute(self, context):
        obj = context.active_object
        mod = next((m for m in obj.modifiers if m.type == 'DISPLACE'), None)
        if not mod:
            self.report({'WARNING'}, "No Displace modifier found.")
            return {'CANCELLED'}
        
        new_image = bpy.data.images.new(name="NewImage", width=1024, height=1024)
        
        new_tex = bpy.data.textures.new(name="NewTexture", type='IMAGE')
        new_tex.image = new_image
        
        mod.texture = new_tex
        
        return {'FINISHED'}

class MODIFIER_PIE_OT_apply_modifier_displace(bpy.types.Operator):
    bl_idname = "modifier_pie.apply_modifier_displace"
    bl_label = "Apply Displace Modifier"
    bl_description = "Displace 모디파이어를 적용합니다"

    def execute(self, context):
        mod = next((m for m in context.object.modifiers if m.type == 'DISPLACE'), None)
        if not mod:
            self.report({'WARNING'}, "No Displace modifier found.")
            return {'CANCELLED'}
        
        bpy.ops.object.modifier_apply(modifier=mod.name)
        return {'FINISHED'}


# ─────────────────────────────────────────────
# Wireframe Modifier
# ─────────────────────────────────────────────

class MODIFIER_PIE_OT_add_wireframe_popup(bpy.types.Operator):
    bl_idname = "modifier_pie.add_wireframe_popup"
    bl_label = "Add Wireframe Modifier"
    bl_description = "선택한 오브젝트에 Wireframe 모디파이어를 추가하고 설정창을 엽니다. 메쉬의 뼈대만 남깁니다"
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
        self.mod = next((m for m in obj.modifiers if m.type == 'WIREFRAME'), None)
        if not self.mod:
            self.mod = obj.modifiers.new(name="Wireframe", type='WIREFRAME')
            self.mod.thickness = 0.02
            self.mod.use_even_offset = True
        
        return context.window_manager.invoke_props_dialog(self, width=300)
    
    def draw(self, context):
        layout = self.layout
        mod = self.mod
        
        layout.prop(mod, "thickness", text="Thickness")
        layout.prop(mod, "offset", text="Offset")
        
        layout.separator()
        
        layout.prop(mod, "use_even_offset", text="Even Thickness")
        layout.prop(mod, "use_relative_offset", text="Relative Thickness")
        layout.prop(mod, "use_crease", text="Crease Edges")
        
        if mod.use_crease:
            layout.prop(mod, "crease_weight", text="Crease Weight")
        
        layout.separator()
        
        layout.prop(mod, "material_offset", text="Material Offset")
        
        layout.prop_search(mod, "vertex_group", context.object, "vertex_groups", text="Vertex Group")
        layout.prop(mod, "invert_vertex_group", text="Invert")
        
        layout.separator()
        layout.operator("modifier_pie.apply_modifier_wireframe", text="Apply", icon='CHECKMARK')
    
    def execute(self, context):
        return {'FINISHED'}

class MODIFIER_PIE_OT_apply_modifier_wireframe(bpy.types.Operator):
    bl_idname = "modifier_pie.apply_modifier_wireframe"
    bl_label = "Apply Wireframe Modifier"
    bl_description = "Wireframe 모디파이어를 적용합니다"

    def execute(self, context):
        mod = next((m for m in context.object.modifiers if m.type == 'WIREFRAME'), None)
        if not mod:
            self.report({'WARNING'}, "No Wireframe modifier found.")
            return {'CANCELLED'}
        
        bpy.ops.object.modifier_apply(modifier=mod.name)
        return {'FINISHED'}

# ─────────────────────────────────────────────
# Screw Modifier
# ─────────────────────────────────────────────

class MODIFIER_PIE_OT_add_screw_popup(bpy.types.Operator):
    bl_idname = "modifier_pie.add_screw_popup"
    bl_label = "Add Screw Modifier"
    bl_description = "선택한 오브젝트에 Screw 모디파이어를 추가하고 설정창을 엽니다. 프로파일을 축 중심으로 회전시켜 입체를 만듭니다"
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
        self.mod = next((m for m in obj.modifiers if m.type == 'SCREW'), None)
        if not self.mod:
            self.mod = obj.modifiers.new(name="Screw", type='SCREW')
            self.mod.angle = math.radians(360)
            self.mod.screw_offset = 0
            self.mod.iterations = 1
            self.mod.axis = 'Z'
        
        return context.window_manager.invoke_props_dialog(self, width=300)
    
    def draw(self, context):
        layout = self.layout
        mod = self.mod
        
        layout.prop(mod, "axis", text="Axis")
        layout.prop(mod, "object", text="Object")
        
        layout.separator()
        
        layout.prop(mod, "angle", text="Angle")
        layout.prop(mod, "screw_offset", text="Screw")
        layout.prop(mod, "iterations", text="Iterations")
        
        layout.separator()
        
        layout.prop(mod, "use_smooth_shade", text="Smooth Shading")
        layout.prop(mod, "use_merge_vertices", text="Merge Vertices")
        
        if mod.use_merge_vertices:
            layout.prop(mod, "merge_threshold", text="Merge Distance")
        
        layout.prop(mod, "use_stretch_u", text="Stretch U")
        layout.prop(mod, "use_stretch_v", text="Stretch V")
        
        layout.separator()
        layout.operator("modifier_pie.apply_modifier_screw", text="Apply", icon='CHECKMARK')
    
    def execute(self, context):
        return {'FINISHED'}

class MODIFIER_PIE_OT_apply_modifier_screw(bpy.types.Operator):
    bl_idname = "modifier_pie.apply_modifier_screw"
    bl_label = "Apply Screw Modifier"
    bl_description = "Screw 모디파이어를 적용합니다"

    def execute(self, context):
        mod = next((m for m in context.object.modifiers if m.type == 'SCREW'), None)
        if not mod:
            self.report({'WARNING'}, "No Screw modifier found.")
            return {'CANCELLED'}
        
        bpy.ops.object.modifier_apply(modifier=mod.name)
        return {'FINISHED'}

class SmartSelect(bpy.types.Operator):
    bl_idname = "object.smartselect"
    bl_label = "Smart Select Tool"
    bl_description = "현재 툴과 상관없이 항상 선택 상자(Select Box) 툴로 전환합니다"

    @classmethod
    def get_current_tool(cls):
        return bpy.context.workspace.tools.from_space_view3d_mode(bpy.context.mode).idname

    def execute(self, context):
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        self.report({'INFO'}, "Select Tool: Box")
        return {'FINISHED'}       


classes = (
     
    # Bevel
    MODIFIER_PIE_OT_add_bevel_popup,
    MODIFIER_PIE_OT_apply_modifier_bevel,

    # Subsurf
    MODIFIER_PIE_OT_add_subsurf_popup,
    MODIFIER_PIE_OT_apply_modifier_subsurf,

    # Solidify
    MODIFIER_PIE_OT_add_solidify_popup,
    MODIFIER_PIE_OT_apply_modifier_solidify,

    # Mirror
    MODIFIER_PIE_OT_mirror_live_popup,
    MODIFIER_PIE_OT_confirm_mirror_and_apply,

    # Apply All
    MODIFIER_PIE_OT_apply_all_common_modifiers,

    # Wire & Overlay
    MODIFIER_PIE_OT_toggle_display_wire,
    VIEW3D_OT_toggle_overlay,

    MODIFIER_PIE_OT_rotational_array,
    MODIFIER_PIE_OT_move_bottom_to_z0,
    MESH_VERTEX_OT_add_vertex_at_cursor,
    
    # Remesh
    MODIFIER_PIE_OT_add_remesh_popup,
    MODIFIER_PIE_OT_apply_modifier_remesh,
    
    # Displace
    MODIFIER_PIE_OT_add_displace_popup,
    MODIFIER_PIE_OT_create_new_texture,
    MODIFIER_PIE_OT_apply_modifier_displace,
    
    # Wireframe
    MODIFIER_PIE_OT_add_wireframe_popup,
    MODIFIER_PIE_OT_apply_modifier_wireframe,
    
    # Screw
    MODIFIER_PIE_OT_add_screw_popup,
    MODIFIER_PIE_OT_apply_modifier_screw,

    SmartSelect,
)
  

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
