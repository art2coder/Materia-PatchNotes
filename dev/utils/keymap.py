import bpy

addon_keymaps = []

def register_keymaps():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if not kc:
        return

    # 1) Object Mode: Ctrl+G / Alt+G (Grouping / Ungrouping)
    km_obj = kc.keymaps.new(name='Object Mode', space_type='EMPTY')
    # --- remove existing conflicts ---
    for kmi in list(km_obj.keymap_items):
        if kmi.type == 'G' and kmi.ctrl and not kmi.alt:
            km_obj.keymap_items.remove(kmi)
        if kmi.type == 'G' and kmi.alt and not kmi.ctrl:
            km_obj.keymap_items.remove(kmi)
    # --- new mappings ---
    kmi = km_obj.keymap_items.new(
        'object.group_by_empty', type='G', value='PRESS', ctrl=True, alt=False
    )
    addon_keymaps.append((km_obj, kmi))
    kmi = km_obj.keymap_items.new(
        'object.ungroup_empty', type='G', value='PRESS', ctrl=False, alt=True
    )
    addon_keymaps.append((km_obj, kmi))

    # 2) Global Window: Q → Pie Menu
    km_win = kc.keymaps.new(name='Window', space_type='EMPTY')
    kmi = km_win.keymap_items.new(
        'wm.call_menu_pie', type='Q', value='PRESS'
    )
    kmi.properties.name = "PIE_MT_modifiers_pie"
    addon_keymaps.append((km_win, kmi))


def unregister_keymaps():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
