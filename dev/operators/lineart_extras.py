import bpy
from bpy.props import StringProperty

class EXTRAS_PT_lineart_panel(bpy.types.Panel):
    bl_label = "LineArt Controls"
    bl_idname = "EXTRAS_PT_lineart_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Extras"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        # LineArt 객체 선택 드롭다운
        box = layout.box()
        box.label(text="LineArt Selection:")
        
        # 씬의 모든 Grease Pencil 객체 중 LineArt 모디파이어가 있는 것들을 찾기
        lineart_objects = []
        for obj in scene.objects:
            if obj.type == 'GPENCIL':
                for modifier in obj.grease_pencil_modifiers:
                    if modifier.type == 'GP_LINEART':
                        lineart_objects.append((obj.name, obj.name, ""))
                        break
        
        if lineart_objects:
            box.prop_search(scene, "selected_lineart_object", scene, "objects", text="LineArt Object")
        else:
            box.label(text="No LineArt objects found", icon='INFO')
        
        # 선택된 LineArt 객체가 있을 때만 컨트롤 표시
        if hasattr(scene, 'selected_lineart_object') and scene.selected_lineart_object:
            selected_obj = scene.objects.get(scene.selected_lineart_object)
            
            if selected_obj and selected_obj.type == 'GPENCIL':
                # LineArt 모디파이어 찾기
                lineart_modifier = None
                for modifier in selected_obj.grease_pencil_modifiers:
                    if modifier.type == 'GP_LINEART':
                        lineart_modifier = modifier
                        break
                
                if lineart_modifier:
                    # Line Thickness 조절
                    thickness_box = layout.box()
                    thickness_box.label(text="Line Thickness (Modifier):")
                    thickness_box.prop(lineart_modifier, "thickness", text="Thickness")
                
                # Object Data Properties - Strokes 설정
                if selected_obj.data:
                    strokes_box = layout.box()
                    strokes_box.label(text="Stroke Properties:")
                    
                    # Stroke Thickness Space 드롭다운
                    strokes_box.prop(selected_obj.data, "stroke_thickness_space", text="Thickness Space")
                    
                    # Thickness Scale 슬라이더
                    strokes_box.prop(selected_obj.data, "pixel_factor", text="Thickness Scale")
        
        # Render Properties - Film Transparent
        render_box = layout.box()
        render_box.label(text="Render Settings:")
        render_box.prop(scene.render, "film_transparent", text="Film Transparent")
        
        # View Transform 드롭다운 메뉴 추가
        colormanagement = scene.view_settings
        render_box.prop(colormanagement, "view_transform", text="View Transform")

class EXTRAS_OT_refresh_lineart(bpy.types.Operator):
    """LineArt 객체 목록 새로고침"""
    bl_idname = "extras.refresh_lineart"
    bl_label = "Refresh LineArt Objects"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        # 강제로 UI 업데이트
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()
        return {'FINISHED'}

def update_lineart_selection(self, context):
    """LineArt 객체 선택이 변경될 때 호출되는 콜백"""
    if hasattr(context.scene, 'selected_lineart_object'):
        obj_name = context.scene.selected_lineart_object
        if obj_name and obj_name in context.scene.objects:
            obj = context.scene.objects[obj_name]
            # 객체를 활성화하고 선택
            context.view_layer.objects.active = obj
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)

# 등록할 클래스들
classes = [
    EXTRAS_PT_lineart_panel,
    EXTRAS_OT_refresh_lineart,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # 씬 속성 등록
    bpy.types.Scene.selected_lineart_object = StringProperty(
        name="Selected LineArt Object",
        description="현재 선택된 LineArt 객체",
        default="",
        update=update_lineart_selection
    )

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    # 씬 속성 제거
    if hasattr(bpy.types.Scene, 'selected_lineart_object'):
        del bpy.types.Scene.selected_lineart_object
