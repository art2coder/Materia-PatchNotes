# utils/keymap.py
import bpy

addon_keymaps = []

def register_keymaps():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if not kc:
        return
    km = kc.keymaps.new(name='Object Mode', space_type='EMPTY')
    # 기존 Ctrl+G, Alt+G 제거 및 새 매핑 추가
    for kmi in list(km.keymap_items):
        if kmi.type == 'G' and kmi.ctrl and not kmi.alt:
            km.keymap_items.remove(kmi)
        if kmi.type == 'G' and kmi.alt and not kmi.ctrl:
            km.keymap_items.remove(kmi)
    kmi = km.keymap_items.new('object.group_by_empty','G','PRESS',ctrl=True)
    addon_keymaps.append((km, kmi))
    kmi = km.keymap_items.new('object.ungroup_empty','G','PRESS',alt=True)
    addon_keymaps.append((km, kmi))

def unregister_keymaps():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
