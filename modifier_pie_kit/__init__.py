bl_info = {
    "name": "Modifier Pie Kit",
    "author": "EJ x ChatGPT",
    "version": (1, 1, 8),
    "blender": (4, 2, 9),
    "location": "Q / W / G / Alt+G / Clt+G in 3D View",
    "description": "A kit of pie-style menus for Modifiers, Pivot tools and Group/Ungroup",
    "category": "3D View"
}


# Version history
# v1.0.0 - Initial Modifiers pie menu(Q)
# v1.1.1 - Added Pivot pie menu (W)
# v1.1.2 - Added Group_by_Empty (Ctrl + G)
# v1.1.3 - Added Ungroup_by_Empty (Alt + G)
# v1.1.4 - Fix crash issues
# v1.1.5 - Added Revive Gizmo 
# v1.1.6 - Fix Pivot pie menu 
# v1.1.7 - Refactoring process
# v1.1.8 - Added Rotational array

import bpy
from mathutils import Vector
import bmesh




# 전역 변수: 키맵 백업 저장소
original_shortcuts = {}
addon_keymaps = []

# ─────────────────────────────────────────────
# 이동 기즈모 및 셀렉트 박스 툴 강제 설정 함수
# ─────────────────────────────────────────────
def ensure_move_gizmo_enabled(context):
    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    # 이동 기즈모 켜기
                    space.show_gizmo = True
                    space.show_gizmo_move = True
                    space.show_gizmo_rotate = False
                    space.show_gizmo_scale = False

                    # 셀렉트 박스 툴로 강제 지정
                    tool = context.workspace.tools.from_space_view3d_mode(context.mode)
                    tool.idname = "builtin.select_box"


# ─────────────────────────────────────────────
# 의도치 않게 꺼졌을 때 다시 켜기 위한 핸들러
# ─────────────────────────────────────────────
def depsgraph_update_handler(scene, depsgraph):
    context = bpy.context
    if context.mode == 'OBJECT' and context.selected_objects:
        ensure_move_gizmo_enabled(context)


# ─────────────────────────────────────────────
# 기존 단축키 백업 & 제거 (조합 키 지정 가능)
# ─────────────────────────────────────────────
def backup_and_remove_keymap_item(km, key_type, ctrl=False, shift=False, alt=False):
    """
    km: KeyMap (e.g. kc.keymaps['3D View'])
    key_type: e.g. 'G', 'Q', 'W'
    ctrl/shift/alt: 부가 키 조합 지정
    """
    for kmi in km.keymap_items:
        if (kmi.type  == key_type   and
            kmi.value == 'PRESS'    and
            kmi.ctrl  == ctrl       and
            kmi.shift == shift      and
            kmi.alt   == alt):
            # 원래 매핑 정보 백업
            original_shortcuts[(key_type, ctrl, shift, alt)] = {
                'idname':     kmi.idname,
                'value':      kmi.value,
                'ctrl':       kmi.ctrl,
                'shift':      kmi.shift,
                'alt':        kmi.alt,
                'properties': {
                    p.identifier: getattr(kmi.properties, p.identifier)
                    for p in kmi.properties.bl_rna.properties.values()
                    if not p.is_readonly
                } if hasattr(kmi, 'properties') else {}
            }
            # 매핑 제거
            km.keymap_items.remove(kmi)
            break

# ─────────────────────────────────────────────
# 기존 단축키 복원
# ─────────────────────────────────────────────

def restore_keymap_item(km, key_type, ctrl=False, shift=False, alt=False):
    """
    km: KeyMap
    key_type+ctrl/shift/alt: 복원할 매핑 키
    """
    key = (key_type, ctrl, shift, alt)
    if key in original_shortcuts:
        data = original_shortcuts.pop(key)
        kmi = km.keymap_items.new(
            data['idname'],
            type=key_type,
            value=data['value'],
            ctrl=data['ctrl'],
            shift=data['shift'],
            alt=data['alt']
        )
        for prop, val in data['properties'].items():
            try:
                setattr(kmi.properties, prop, val)
            except Exception:
                pass
        
# ─────────────────────────────────────────────
# Group_by_Empty
# ─────────────────────────────────────────────

class OBJECT_OT_group_by_empty(bpy.types.Operator):
    """Create an Empty at median pivot and parent selected objects (one‐step undo)"""
    bl_idname = "object.group_by_empty"
    bl_label = "Group by Empty"
    bl_options = {'REGISTER', 'UNDO'}  # UNDO 옵션으로 전체를 한 스텝에 묶기

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and len(context.selected_objects) > 0

    def execute(self, context):
        sel = [o for o in context.selected_objects if o.type != 'EMPTY']
        if not sel:
            self.report({'WARNING'}, "No objects to group")
            return {'CANCELLED'}

        # 1) 센터 계산
        center = sum((o.matrix_world.translation for o in sel), Vector()) / len(sel)

        # 2) Empty 생성 (내장 오퍼레이터 사용)
        bpy.ops.object.select_all(action='DESELECT')
        # 빈이 생성될 레이어와 컨텍스트가 VIEW_3D 인지 확인 필요
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=center)
        empty = context.active_object
        
        # 🎯 자동 이름 지정: "Group", "Group_001", ...
        base_name = "- Group"
        name = base_name
        i = 1
        while name in bpy.data.objects:
            name = f"{base_name}_{i:03d}"
            i += 1
        empty.name = name

        # 3) 선택한 객체들 재선택 후 페런트
        for o in sel:
            o.select_set(True)
        context.view_layer.objects.active = empty
        bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)

        # 4) 결과 리포트
        self.report({'INFO'}, f"Grouped {len(sel)} objects into '{empty.name}'")
        return {'FINISHED'}


    
# ─────────────────────────────────────────────
# 1) 언그루핑 오퍼레이터
# ─────────────────────────────────────────────

class OBJECT_OT_ungroup_empty(bpy.types.Operator):
    """부모 해제 + 위치 유지하고, 방금 언그룹한 Empty만 삭제"""
    bl_idname = "object.ungroup_empty"
    bl_label  = "Ungroup (Clear Keep + Remove Empty)"
    bl_options= {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and any(o.parent for o in context.selected_objects)

    def execute(self, context):
        # 1) 언그룹 대상 및 방금 언그룹된 부모 Empty 이름 저장
        selected_objs = list(context.selected_objects)
        parent_names   = {o.parent.name for o in selected_objs if o.parent}

        # 2) 부모 해제 + 위치 유지
        bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

        # 3) 삭제할 Empty 객체 리스트로 가져오기
        empties = [bpy.data.objects.get(name) 
                   for name in parent_names 
                   if bpy.data.objects.get(name) and bpy.data.objects[name].type == 'EMPTY']

        if empties:
            # 4) OBJECT 모드 보장
            if context.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')

            # 5) 현재 선택 모두 해제
            bpy.ops.object.select_all(action='DESELECT')

            # 6) 삭제 대상 Empty 전부 선택 & 첫번째를 활성화
            for em in empties:
                em.select_set(True)
            context.view_layer.objects.active = empties[0]

            # 7) Blender 내장 delete 오퍼레이터 호출
            bpy.ops.object.delete()

        # 8) 결과 보고
        self.report({'INFO'},
            f"Ungrouped {len(selected_objs)} objects, removed {len(empties)} empty(s).")
        return {'FINISHED'}

            
# ─────────────────────────────────────────────
# Pivot 관련 오퍼레이터
# ─────────────────────────────────────────────

class PIVOT_OT_toggle_pivot(bpy.types.Operator):
    '''Pivot: Cursor ⇄ Median'''
    bl_idname = "pivot.toggle_pivot"
    bl_label = "Pivot"

    def execute(self, context):
        current = context.scene.tool_settings.transform_pivot_point
        new_mode = 'MEDIAN_POINT' if current == 'CURSOR' else 'CURSOR'
        context.scene.tool_settings.transform_pivot_point = new_mode
        return {'FINISHED'}

class PIVOT_OT_cursor_to_selection(bpy.types.Operator):
    '''Cursor ← Selection'''
    bl_idname = "pivot.cursor_to_selection"
    bl_label = "Cursor"
    
    @classmethod
    def poll(cls, context):
        return (
        context.area.type == 'VIEW_3D'
        and context.mode in {'OBJECT', 'EDIT_MESH'}
        and context.selected_objects
    )

    def execute(self, context):
        bpy.ops.view3d.snap_cursor_to_selected()
        return {'FINISHED'}

class PIVOT_OT_cursor_to_origin(bpy.types.Operator):
    '''Cursor → Origin'''
    bl_idname = "pivot.cursor_to_origin"
    bl_label = "Reset"

    def execute(self, context):
        context.scene.cursor.location = (0.0, 0.0, 0.0)
        return {'FINISHED'}

class PIVOT_OT_selection_to_cursor(bpy.types.Operator):
    """Selection → Cursor"""
    bl_idname = "pivot.selection_to_cursor"
    bl_label = "Selection to Cursor"
    bl_description = "Snap selected objects to 3D Cursor"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        # 3D 뷰에서, 선택된 오브젝트가 하나 이상 있을 때만 활성화
        return (context.area.type == 'VIEW_3D' and
                len(context.selected_objects) > 0)

    def execute(self, context):
        # Blender 내장 스냅 오퍼레이터 호출
        bpy.ops.view3d.snap_selected_to_cursor(use_offset=False)
        self.report({'INFO'}, "Selection → Cursor")
        return {'FINISHED'}

class OBJECT_OT_origin_to_geometry(bpy.types.Operator):
    """Origin → Geometry"""
    bl_idname = "object.origin_to_geometry"
    bl_label = "Origin to Geometry"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (
            context.mode == 'OBJECT' and
            context.selected_objects and
            any(o.type in {'MESH', 'CURVE', 'EMPTY'} for o in context.selected_objects)
        )

    def execute(self, context):
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
        self.report({'INFO'}, "Origin set to Geometry.")
        return {'FINISHED'}

class OBJECT_OT_origin_to_cursor(bpy.types.Operator):
    """Origin → 3D Cursor"""
    bl_idname = "object.origin_to_cursor"
    bl_label = "Origin to 3D Cursor"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (
            context.mode == 'OBJECT' and
            context.selected_objects and
            any(o.type in {'MESH', 'CURVE', 'EMPTY'} for o in context.selected_objects)
        )

    def execute(self, context):
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
        self.report({'INFO'}, "Origin set to 3D Cursor.")
        return {'FINISHED'}
        


# ─────────────────────────────────────────────
# Pivot 파이메뉴
# ─────────────────────────────────────────────

class PIVOT_MT_pie_menu(bpy.types.Menu):
    bl_label = "Pivot Menu"
    bl_idname = "PIVOT_MT_pie_menu"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        
        # 현재 Pivot 상태 확인
        pivot_mode = context.scene.tool_settings.transform_pivot_point
        label = "Pivot: 3D Cursor" if pivot_mode == 'CURSOR' else "Pivot: Median"
        icon = 'PIVOT_CURSOR' if pivot_mode == 'CURSOR' else 'PIVOT_MEDIAN'

     
        # 동적 라벨과 아이콘 반영
        pie.operator("object.origin_to_geometry", text="Origin to Geometry", icon='OBJECT_ORIGIN')
        pie.operator("object.origin_to_cursor", text="Origin to 3D Cursor", icon='PIVOT_CURSOR')
        pie.operator("pivot.cursor_to_selection", text="Cursor", icon='CURSOR')
        pie.operator("pivot.selection_to_cursor", text="Move", icon='ARROW_LEFTRIGHT')
        pie.separator() 
        pie.separator()
        pie.operator("pivot.toggle_pivot", text=label, icon=icon)
        pie.operator("pivot.cursor_to_origin", text="Reset", icon='FILE_REFRESH')
        
             
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
# 미러 라이브 미리보기용 업데이트 함수
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
# Apply 오퍼레이터 (완전 독립적이고 안전)
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
        for t in ['BOOLEAN', 'BEVEL', 'MIRROR', 'SUBSURF']:
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

# ─────────────────────────────────────────────
# Pie Menu
# ─────────────────────────────────────────────

class PIE_MT_modifiers_pie(bpy.types.Menu):
    bl_label = "Modifier Pie Menu"
    bl_idname = "PIE_MT_modifiers_pie"

    def draw(self, context):
        pie = self.layout.menu_pie()
        
        pie.operator("object.add_boolean_popup", text="Boolean", icon='MOD_BOOLEAN')  # ↑
        pie.operator("object.add_bevel_popup", text="Bevel", icon='MOD_BEVEL')        # ↓
        pie.operator("object.mirror_live_popup", text="Mirror", icon='MOD_MIRROR')     # →
        pie.operator("object.curve_bevel_popup", text="Curve Bevel", icon='CURVE_DATA')  # 8
        
        pie.operator("object.toggle_display_wire", text="Toggle Wire", icon='SHADING_WIRE')
        pie.operator("view3d.toggle_overlay", text="Toggle Overlay", icon='OVERLAY')  # 
        pie.operator("object.apply_all_common_modifiers", text="Apply All", icon='CHECKMARK')  # ←
        pie.operator("object.add_subsurf_popup", text="Subsurf", icon='MOD_SUBSURF')  # ↘

# ─────────────────────────────────────────────
# 등록 처리 
# ─────────────────────────────────────────────

addon_keymaps = []

classes = (
    OBJECT_OT_group_by_empty,
    OBJECT_OT_ungroup_empty,  
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
    PIE_MT_modifiers_pie,
    
    # ⬇ 추가할 Pivot 관련 오퍼레이터 및 메뉴
    PIVOT_OT_toggle_pivot,
    PIVOT_OT_cursor_to_selection,
    PIVOT_OT_cursor_to_origin,
    PIVOT_OT_selection_to_cursor,
    OBJECT_OT_origin_to_geometry,
    OBJECT_OT_origin_to_cursor,
    PIVOT_MT_pie_menu,
             
)

# ─────────────────────────────────────────────
# 등록 함수에 통합
# ─────────────────────────────────────────────
def register():
    # 1) 모든 클래스 등록
    for cls in classes:
        bpy.utils.register_class(cls)

    # 2) active 키맵 가져오기
    wm     = bpy.context.window_manager
    kc_act = wm.keyconfigs.active
    if not kc_act:
        return

    # ——— 3D View 키맵 ———
    km3d = kc_act.keymaps.get('3D View')
    if not km3d:
        km3d = kc_act.keymaps.new('3D View', space_type='VIEW_3D')
        
    
    # Q 키 (Modifiers Pie)
    backup_and_remove_keymap_item(km3d, 'Q')
    kmi = km3d.keymap_items.new('wm.call_menu_pie', 'Q', 'PRESS')
    kmi.properties.name = "PIE_MT_modifiers_pie"
    addon_keymaps.append((km3d, kmi))

    # W 키 (Pivot Pie)
    backup_and_remove_keymap_item(km3d, 'W')
    kmi = km3d.keymap_items.new('wm.call_menu_pie', 'W', 'PRESS')
    kmi.properties.name = "PIVOT_MT_pie_menu"
    addon_keymaps.append((km3d, kmi))

    # Ctrl+G 키 (Group by Empty)
    backup_and_remove_keymap_item(km3d, 'G', ctrl=True)
    kmi = km3d.keymap_items.new('object.group_by_empty', 'G', 'PRESS', ctrl=True)
    addon_keymaps.append((km3d, kmi))

    # ——— Object Mode 키맵에서도 기본 Ctrl+G 제거 ———
    km_obj = kc_act.keymaps.get('Object Mode')
    if km_obj:
        backup_and_remove_keymap_item(km_obj, 'G', ctrl=True)
                # 기본 Alt+G (Clear Location) 백업·제거
        backup_and_remove_keymap_item(km_obj, 'G', alt=True)
        # 우리의 Ungroup 오퍼레이터를 Alt+G 로 등록
        kmi = km_obj.keymap_items.new(
            'object.ungroup_empty',
            type='G', value='PRESS',
            alt=True
        )
        addon_keymaps.append((km_obj, kmi))
    
    # ──────────── Ungroup Alt+G ────────────    
    backup_and_remove_keymap_item(km3d, 'G', alt=True)
    kmi = km3d.keymap_items.new(
        'object.ungroup_empty',  # bl_idname
        type='G', value='PRESS',
        alt=True
    )
    addon_keymaps.append((km3d, kmi))
    
    # 기즈모 핸들러 추가
    bpy.app.handlers.depsgraph_update_post.append(depsgraph_update_handler)
       

def unregister():
    # 1) 애드온이 추가한 매핑 모두 제거
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    # 2) 클래스 언레지스터
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    # 3) active 키맵에서 원래 매핑 복원
    wm     = bpy.context.window_manager
    kc_act = wm.keyconfigs.active
    if not kc_act:
        return

    # ——— 3D View 복원 ———
    km3d = kc_act.keymaps.get('3D View')
    if km3d:
        restore_keymap_item(km3d, 'Q')
        restore_keymap_item(km3d, 'W')
        restore_keymap_item(km3d, 'G', ctrl=True)

    # ——— Object Mode 복원 ———
    km_obj = kc_act.keymaps.get('Object Mode')
    if km_obj:
        restore_keymap_item(km_obj, 'G', ctrl=True)
        
    # 핸들러 제거
    if depsgraph_update_handler in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(depsgraph_update_handler)    
          

if __name__ == "__main__":
    register()

