import bpy

addon_keymaps = []

def register_keymaps():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if not kc:
        return

    # 1) Object Mode 공통 키맵
    km_obj = kc.keymaps.new(name='Object Mode', space_type='EMPTY')

    # --- 그룹핑 관련 키맵 ---
    for kmi in list(km_obj.keymap_items):
        if kmi.type == 'G' and kmi.ctrl and not kmi.alt:
            km_obj.keymap_items.remove(kmi)
        if kmi.type == 'G' and kmi.alt and not kmi.ctrl:
            km_obj.keymap_items.remove(kmi)

    kmi = km_obj.keymap_items.new(
        'object.group_by_empty', type='G', value='PRESS', ctrl=True, alt=False
    )
    addon_keymaps.append((km_obj, kmi))

    kmi = km_obj.keymap_items.new(
        'object.ungroup_empty', type='G', value='PRESS', ctrl=False, alt=True
    )
    addon_keymaps.append((km_obj, kmi))

    # --- Pivot Pie (W) ---
    kmi = km_obj.keymap_items.new(
        'wm.call_menu_pie', type='W', value='PRESS'
    )
    kmi.properties.name = 'PIE_MT_pivot_pie'
    addon_keymaps.append((km_obj, kmi))

    # 2) Window 키맵: Modifier Pie (Q)
    km_win = kc.keymaps.new(name='Window', space_type='EMPTY')
    kmi = km_win.keymap_items.new(
        'wm.call_menu_pie', type='Q', value='PRESS'
    )
    kmi.properties.name = "PIE_MT_modifiers_pie"
    addon_keymaps.append((km_win, kmi))

    # 3) W → Pivot Pie Menu
    km_obj = kc.keymaps.new(name='Object Mode', space_type='EMPTY')
    kmi = km_obj.keymap_items.new('wm.call_menu_pie', type='W', value='PRESS')
    kmi.properties.name = 'PIE_MT_pivot_pie'
    addon_keymaps.append((km_obj, kmi))

    # Edit Mode (Mesh 모드)에도 동일한 W 키 등록
    km_edit = kc.keymaps.new(name='Mesh', space_type='EMPTY')
    kmi = km_edit.keymap_items.new('wm.call_menu_pie', type='W', value='PRESS')
    kmi.properties.name = 'PIE_MT_pivot_pie'
    addon_keymaps.append((km_edit, kmi))




def unregister_keymaps():
    for km, kmi in addon_keymaps:
        try:
            km.keymap_items.remove(kmi)
        except Exception:
            pass
    addon_keymaps.clear()


