from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QKeySequence
from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout, QLabel, QDialogButtonBox, QShortcut

def show_hotkeys_help(iface):
    dlg = QDialog(iface.mainWindow())
    dlg.setWindowTitle("Prečice")
    lay = QVBoxLayout(dlg)
    info = QLabel(
        "<b>Standardne prečice</b><br>"
        "Ctrl+B – BOM izveštaj<br>"
        "Ctrl+G – Razgrani kablove (offset)<br>"
        "Ctrl+P – Publish to PostGIS<br>"
        "Ctrl+F – Prekid vlakna (klik na trasu)<br>"
        "R – Rezerve (završna)<br>"
    )
    info.setTextFormat(Qt.RichText)
    lay.addWidget(info)
    lay.addWidget(QDialogButtonBox(QDialogButtonBox.Close))
    dlg.exec_()

def register_hotkeys(plugin):
    """Povezuje globalne prečice sa akcijama plugina. Kreira shortcut-e i na glavnom prozoru i na mapi."""
    try:
        win = plugin.iface.mainWindow()
        canvas = plugin.iface.mapCanvas()
        if not hasattr(plugin, '_hk_shortcuts'):
            plugin._hk_shortcuts = []
        def add(seq, slot):
            for parent in (win, canvas):
                sc = QShortcut(QKeySequence(seq), parent)
                sc.setContext(Qt.ApplicationShortcut)
                sc.activated.connect(slot)
                plugin._hk_shortcuts.append(sc)
        if hasattr(plugin, 'razgrani_kablove_offset'): add('Ctrl+G', plugin.razgrani_kablove_offset)
        if hasattr(plugin, 'open_bom_dialog'): add('Ctrl+B', plugin.open_bom_dialog)
        if hasattr(plugin, 'activate_fiber_break_tool'): add('Ctrl+F', plugin.activate_fiber_break_tool)
        pub = getattr(plugin, 'open_publish_dialog', None) or getattr(plugin, 'publish_to_postgis', None)
        if callable(pub): add('Ctrl+P', pub)
        if hasattr(plugin, '_start_rezerva_interaktivno'): add('R', lambda: plugin._start_rezerva_interaktivno('zavrsna'))
        # pomoćni: Shift+R → prolazna
        if hasattr(plugin, '_start_rezerva_interaktivno'): add('Shift+R', lambda: plugin._start_rezerva_interaktivno('prolazna'))
    except Exception:
        pass
