import bpy
import os
import bpy.utils.previews

custom_icons = None

class INTERNAL_OT_create_image_plane(bpy.types.Operator):
    """
    현재 바라보는 방향에 맞춰 이미지가 정면으로 생성됩니다
   
    """
    bl_idname = "internal.create_image_plane"
    bl_label = "Create Image Plane (Internal)"
    bl_description = "이미지 파일을 선택하여 현재 바라보는 방향을 기준으로 3D 뷰포트에 레퍼런스 이미지를 생성합니다"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: bpy.props.StringProperty(subtype="FILE_PATH", options={'HIDDEN'})

    def execute(self, context):
        try:
            image_data = bpy.data.images.load(self.filepath)
        except Exception as e:
            self.report({'ERROR'}, f"이미지를 불러올 수 없습니다: {e}")
            return {'CANCELLED'}

        # 'align' 옵션을 'VIEW'로 변경하여 현재 보는 방향에 맞춰 생성
        bpy.ops.object.empty_add(type='PLAIN_AXES', align='VIEW', location=context.scene.cursor.location)
        empty_obj = context.active_object

        empty_obj.empty_display_type = 'IMAGE'
        empty_obj.data = image_data
        empty_obj.empty_display_size = 2.0

        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class PIE_MT_pivot_pie(bpy.types.Menu):
    bl_label = " "
    bl_idname = "PIE_MT_pivot_pie"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        try:
            addon_name = __name__.split('.')[0]
            prefs = context.preferences.addons[addon_name].preferences
            icon_scale = prefs.icon_size
            show_text = prefs.show_text
        except (KeyError, AttributeError):
            icon_scale = 1.0
            show_text = True

        grid_left = pie.grid_flow(row_major=True, columns=3, even_columns=True, even_rows=True, align=True)
        grid_left.scale_x = icon_scale
        grid_left.scale_y = icon_scale

        if custom_icons and "object_origin_icon" in custom_icons:
            
            grid_left.operator("modifier_pie.origin_to_geometry", text="Geometry" if show_text else "", 
                               icon_value=custom_icons["object_origin_icon"].icon_id)
        else:
            grid_left.operator("modifier_pie.origin_to_geometry", text="Geometry" if show_text else "", icon='OBJECT_ORIGIN')


        grid_left.operator("object.origin_to_bottom", text="Bottom" if show_text else "", icon='AXIS_TOP')

   
        if custom_icons and "pivot_cursor_icon" in custom_icons:
            
            grid_left.operator("modifier_pie.origin_to_cursor", text="3D Cursor" if show_text else "", 
                               icon_value=custom_icons["pivot_cursor_icon"].icon_id)
        else:
            grid_left.operator("modifier_pie.origin_to_cursor", text="3D Cursor" if show_text else "", icon='PIVOT_CURSOR')
        
        
        grid_left.operator("modifier_pie.cursor_to_selection", text="to Select" if show_text else "", icon='CURSOR')

        if custom_icons and "file_refresh_icon" in custom_icons:
            
            grid_left.operator("modifier_pie.cursor_to_origin", text="World Origin" if show_text else "", 
                               icon_value=custom_icons["file_refresh_icon"].icon_id)
        else:
            grid_left.operator("modifier_pie.cursor_to_origin", text="World Origin" if show_text else "", icon='FILE_REFRESH')

        grid_left.operator("modifier_pie.selection_to_cursor", text="to Cursor" if show_text else "", icon='FORWARD')
        grid_left.operator("modifier_pie.toggle_pivot", text="Tog Pivot" if show_text else "", icon='PIVOT_MEDIAN')
        grid_left.operator("view3d.toggle_overlay", text="Tog Overlay" if show_text else "", icon='OVERLAY')
        grid_left.operator("view3d.view_selected", text="Focus" if show_text else "", icon='ZOOM_SELECTED')
        grid_left.separator()
        grid_left.operator("modifier_pie.apply_all_common_modifiers", text="Apply All" if show_text else "", icon='CHECKMARK')        
        op = grid_left.operator("object.transform_apply", text="Scale&Rot" if show_text else "", icon='CON_LOCLIKE')
        op.location = False
        op.rotation = True 
        op.scale = True
        
        # (이하 생략 - draw 함수의 나머지 부분은 기존과 동일합니다.)

        grid_right = pie.grid_flow(row_major=True, columns=3, even_columns=True, even_rows=True, align=True)
        grid_right.scale_x = icon_scale
        grid_right.scale_y = icon_scale
        grid_right.operator("mesh_vertex.add_vertex_at_cursor", text="Vertex" if show_text else "", icon='VERTEXSEL')
        grid_right.operator("mesh.primitive_plane_add", text="Plane" if show_text else "", icon='MESH_PLANE')
        grid_right.operator("mesh.primitive_cube_add", text="Cube" if show_text else "", icon='MESH_CUBE')
        grid_right.operator("mesh.primitive_circle_add", text="Circle" if show_text else "", icon='MESH_CIRCLE')
        grid_right.operator("mesh.primitive_uv_sphere_add", text="Sphere" if show_text else "", icon='MESH_UVSPHERE')
        grid_right.operator("mesh.primitive_cylinder_add", text="Cylinder" if show_text else "", icon='MESH_CYLINDER')
        grid_right.operator("curve.primitive_nurbs_path_add", text="Nb Path" if show_text else "", icon='CURVE_PATH')
        grid_right.operator("curve.primitive_nurbs_curve_add", text="Nb Curve" if show_text else "", icon='CURVE_NCURVE')
        grid_right.operator("curve.primitive_bezier_circle_add", text="Bz Circle" if show_text else "", icon='CURVE_BEZCIRCLE')
        
        grid_right.operator("internal.create_image_plane", text="Reference" if show_text else "", icon='IMAGE_REFERENCE')
        empty_axes = grid_right.operator("object.empty_add", text="Empty Axes" if show_text else "", icon='EMPTY_AXIS')
        empty_axes.type = 'PLAIN_AXES'

        grid_right.label(text="")

        grid_bottom = pie.grid_flow(row_major=True, columns=3, even_columns=True, even_rows=True, align=True)
        grid_bottom.scale_x = icon_scale
        grid_bottom.scale_y = icon_scale
        grid_bottom.separator()
        grid_bottom.operator("modifier_pie.move_bottom_to_z0", text="Drop" if show_text else "", icon='TRIA_DOWN')
        grid_bottom.separator()
        grid_bottom.operator("modifier_pie.add_solidify_popup", text="Solidify" if show_text else "", icon='MOD_SOLIDIFY')
        grid_bottom.operator("modifier_pie.add_boolean_popup", text="Boolean" if show_text else "", icon='MOD_BOOLEAN')
        grid_bottom.operator("modifier_pie.add_subsurf_popup", text="Subsur" if show_text else "", icon='MOD_SUBSURF')
        grid_bottom.operator("modifier_pie.mirror_live_popup", text="Mirror" if show_text else "", icon='MOD_MIRROR')
        grid_bottom.operator("modifier_pie.add_bevel_popup", text="Bevel" if show_text else "", icon='MOD_BEVEL')
        grid_bottom.operator("modifier_pie.rotational_array", text="Rotate" if show_text else "", icon='FORCE_MAGNETIC')
        grid_bottom.operator("modifier_pie.add_array_popup", text="Array" if show_text else "", icon='MOD_ARRAY')
        grid_bottom.operator("modifier_pie.add_screw_popup", text="Screw" if show_text else "", icon='MOD_SCREW')        
        grid_bottom.operator("modifier_pie.add_wireframe_popup", text="Wire" if show_text else "", icon='MOD_WIREFRAME')
        

        pie.separator()
        pie.separator()
        pie.separator()
        pie.separator()
        pie.separator()

classes = (
    INTERNAL_OT_create_image_plane,
    PIE_MT_pivot_pie,
)

def register():
    print("--- PIVOT PIE ADDON REGISTERING ---")
    global custom_icons
    custom_icons = bpy.utils.previews.new()

    addon_dir = os.path.dirname(__file__)
    icons_dir = os.path.join(addon_dir, "icons")
    
    print(f"Searching for icons in: {icons_dir}")

    if os.path.exists(icons_dir):
        loaded_icons = []
        for f in os.listdir(icons_dir):
            if f.endswith(".png"):
                icon_name = os.path.splitext(f)[0]
                custom_icons.load(icon_name, os.path.join(icons_dir, f), 'IMAGE')
                loaded_icons.append(icon_name)
        if loaded_icons:
            print(f"Successfully loaded icons: {loaded_icons}")
        else:
            print("Found 'icons' folder, but no .png files inside.")
    else:
        print("Error: 'icons' folder not found.")

    for cls in classes:
        bpy.utils.register_class(cls)
    
    print("--- REGISTER COMPLETE ---")

def unregister():
    global custom_icons
    bpy.utils.previews.remove(custom_icons)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()