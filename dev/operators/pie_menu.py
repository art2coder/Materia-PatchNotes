import bpy

class PIE_MT_modifiers_pie(bpy.types.Menu):
    bl_label = "Modifier Pie Menu"
    bl_idname = "PIE_MT_modifiers_pie"

    def draw(self, context):
        pie = self.layout.menu_pie()

        # ↑ Top
        pie.operator("modifier_pie.add_boolean_popup",         text="Boolean",      icon='MOD_BOOLEAN')
    
        # ↗ Top-Right
        pie.operator("modifier_pie.add_bevel_popup",           text="Bevel",        icon='MOD_BEVEL')
  
        # → Right
        pie.operator("modifier_pie.mirror_live_popup",         text="Mirror",       icon='MOD_MIRROR')
   
        # ↘ Bottom-Right
        pie.operator("modifier_pie.curve_bevel_popup",         text="Curve Bevel",  icon='CURVE_DATA') 
   
        # ← Left
        pie.operator("modifier_pie.toggle_display_wire",       text="Toggle Wire",  icon='SHADING_WIRE')

         # ↖ Top-Left
        pie.operator("view3d.toggle_overlay",            text="Toggle Overlay", icon='OVERLAY')
        
        # ↙ Bottom-Left
        pie.operator("modifier_pie.apply_all_common_modifiers", text="Apply All",   icon='FILE_TICK')
        
         # ↓ Bottom
        pie.operator("modifier_pie.add_subsurf_popup",         text="Subsurf",      icon='MOD_SUBSURF')

        

classes = (PIE_MT_modifiers_pie,)

def register():
    bpy.utils.register_class(PIE_MT_modifiers_pie)

def unregister():
    bpy.utils.unregister_class(PIE_MT_modifiers_pie)
