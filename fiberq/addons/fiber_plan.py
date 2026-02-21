"""
FiberQ Fiber Plan Addon – Splice closure management, splice recording,
and end-to-end fiber path tracing.

Provides three main dialogs:
- SpliceClosureDialog: manage splice closures, trays, and individual splices
- SpliceRecordForm: quick splice entry form (for use in QGIS and QField)
- FiberTraceDialog: trace a fiber end-to-end and visualize the path
"""

from qgis.PyQt.QtCore import Qt, QVariant
from qgis.PyQt.QtGui import QColor, QFont, QIcon
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QFormLayout, QLineEdit, QSpinBox,
    QDoubleSpinBox, QSplitter, QTreeWidget, QTreeWidgetItem,
    QTabWidget, QWidget, QTextEdit, QFileDialog, QApplication
)
from qgis.core import (
    QgsProject, QgsVectorLayer, QgsFeature, QgsGeometry,
    QgsPointXY, QgsWkbTypes, QgsRectangle
)
import os


def _plugin_root_dir():
    return os.path.dirname(os.path.dirname(__file__))


def _get_api_client():
    """Get an authenticated API client instance."""
    from .zitadel_auth import get_auth
    from .api_client import FiberQApiClient

    auth = get_auth()
    token = auth.get_token()
    if not token:
        raise RuntimeError(
            "Not authenticated. Please sign in first (FiberQ → Sign In)."
        )
    client = FiberQApiClient(token=token)
    return client


# ======================================================================
# Splice Closure Dialog
# ======================================================================

class SpliceClosureDialog(QDialog):
    """
    Main fiber plan management dialog.

    Left panel: tree of closures → trays
    Right panel: splice matrix for selected tray
    """

    def __init__(self, iface, parent=None):
        super().__init__(parent or iface.mainWindow(), flags=Qt.Window)
        self.iface = iface
        self.setWindowTitle("FiberQ – Fiber Plan (Splice Closures)")
        self.setMinimumSize(900, 600)
        self._api = None
        self._closures = []
        self._current_tray_id = None

        self._build_ui()
        self._load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        splitter = QSplitter(Qt.Horizontal)

        # --- Left: Closure / Tray tree ---
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)

        lbl = QLabel("Splice Closures")
        lbl.setStyleSheet("font-weight: bold;")
        left_layout.addWidget(lbl)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Name", "Type", "Trays"])
        self.tree.setColumnCount(3)
        self.tree.itemClicked.connect(self._on_tree_item_clicked)
        left_layout.addWidget(self.tree)

        btn_row = QHBoxLayout()
        self.btn_add_closure = QPushButton("+ Closure")
        self.btn_add_closure.clicked.connect(self._add_closure)
        btn_row.addWidget(self.btn_add_closure)

        self.btn_add_tray = QPushButton("+ Tray")
        self.btn_add_tray.clicked.connect(self._add_tray)
        self.btn_add_tray.setEnabled(False)
        btn_row.addWidget(self.btn_add_tray)

        self.btn_zoom = QPushButton("Zoom To")
        self.btn_zoom.clicked.connect(self._zoom_to_closure)
        self.btn_zoom.setEnabled(False)
        btn_row.addWidget(self.btn_zoom)

        left_layout.addLayout(btn_row)
        splitter.addWidget(left)

        # --- Right: Splice table for selected tray ---
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.lbl_tray = QLabel("Select a tray to view splices")
        self.lbl_tray.setStyleSheet("font-weight: bold;")
        right_layout.addWidget(self.lbl_tray)

        self.splice_table = QTableWidget()
        self.splice_table.setColumnCount(11)
        self.splice_table.setHorizontalHeaderLabels([
            "Pos", "Cable A", "Tube A", "Fiber A", "Color A",
            "Cable B", "Tube B", "Fiber B", "Color B",
            "Loss (dB)", "Status"
        ])
        self.splice_table.horizontalHeader().setStretchLastSection(True)
        self.splice_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.splice_table.setAlternatingRowColors(True)
        right_layout.addWidget(self.splice_table)

        btn_row2 = QHBoxLayout()
        self.btn_add_splice = QPushButton("+ Splice")
        self.btn_add_splice.clicked.connect(self._add_splice)
        self.btn_add_splice.setEnabled(False)
        btn_row2.addWidget(self.btn_add_splice)

        self.btn_edit_splice = QPushButton("Edit")
        self.btn_edit_splice.clicked.connect(self._edit_splice)
        self.btn_edit_splice.setEnabled(False)
        btn_row2.addWidget(self.btn_edit_splice)

        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.clicked.connect(self._load_data)
        btn_row2.addWidget(self.btn_refresh)

        right_layout.addLayout(btn_row2)
        splitter.addWidget(right)

        splitter.setSizes([300, 600])
        layout.addWidget(splitter)

    def _ensure_api(self):
        if self._api is None:
            self._api = _get_api_client()
        return self._api

    def _load_data(self):
        try:
            api = self._ensure_api()
            self._closures = api.list_closures()
        except Exception as e:
            QMessageBox.warning(self, "FiberQ", f"Failed to load closures:\n{e}")
            return

        self.tree.clear()
        for cl in self._closures:
            item = QTreeWidgetItem([
                cl.get("closure_type", "Closure") + f" #{cl['id']}",
                cl.get("closure_type", ""),
                str(cl.get("tray_count", 0)),
            ])
            item.setData(0, Qt.UserRole, ("closure", cl))

            # Load trays for this closure
            try:
                trays = self._ensure_api().list_trays(cl["id"])
            except Exception:
                trays = []

            for tray in trays:
                tray_item = QTreeWidgetItem([
                    f"Tray {tray['tray_number']}",
                    tray.get("tray_type", ""),
                    str(tray.get("capacity", 0)) + "F",
                ])
                tray_item.setData(0, Qt.UserRole, ("tray", tray, cl))
                item.addChild(tray_item)

            self.tree.addTopLevelItem(item)

        self.tree.expandAll()

    def _on_tree_item_clicked(self, item, column):
        data = item.data(0, Qt.UserRole)
        if not data:
            return

        if data[0] == "closure":
            cl = data[1]
            self.btn_add_tray.setEnabled(True)
            self.btn_zoom.setEnabled(True)
            self.btn_add_splice.setEnabled(False)
            self.btn_edit_splice.setEnabled(False)
            self._current_tray_id = None
            self.lbl_tray.setText(f"Closure #{cl['id']} – select a tray")
            self.splice_table.setRowCount(0)

        elif data[0] == "tray":
            tray = data[1]
            cl = data[2]
            self.btn_add_tray.setEnabled(True)
            self.btn_zoom.setEnabled(True)
            self.btn_add_splice.setEnabled(True)
            self.btn_edit_splice.setEnabled(True)
            self._current_tray_id = tray["id"]
            self.lbl_tray.setText(
                f"Closure #{cl['id']} → Tray {tray['tray_number']} "
                f"({tray.get('tray_type', '')}, {tray.get('capacity', '')}F)"
            )
            self._load_splices(tray["id"])

    def _load_splices(self, tray_id: int):
        try:
            splices = self._ensure_api().list_splices(tray_id=tray_id)
        except Exception as e:
            QMessageBox.warning(self, "FiberQ", f"Failed to load splices:\n{e}")
            return

        self.splice_table.setRowCount(len(splices))
        for row, sp in enumerate(splices):
            items = [
                str(sp.get("position_in_tray", "")),
                str(sp.get("cable_a_fid", "")),
                f"{sp.get('tube_a_number', '')} ({sp.get('tube_a_color', '')})",
                f"{sp.get('fiber_a_number', '')} ({sp.get('fiber_a_color', '')})",
                sp.get("fiber_a_color", ""),
                str(sp.get("cable_b_fid", "")),
                f"{sp.get('tube_b_number', '')} ({sp.get('tube_b_color', '')})",
                f"{sp.get('fiber_b_number', '')} ({sp.get('fiber_b_color', '')})",
                sp.get("fiber_b_color", ""),
                f"{sp.get('loss_db', 0):.2f}" if sp.get("loss_db") else "",
                sp.get("status", ""),
            ]
            for col, val in enumerate(items):
                cell = QTableWidgetItem(val)
                cell.setData(Qt.UserRole, sp)
                # Color-code the fiber color cells
                if col == 4 and sp.get("fiber_a_color"):
                    self._apply_color_bg(cell, sp["fiber_a_color"])
                if col == 8 and sp.get("fiber_b_color"):
                    self._apply_color_bg(cell, sp["fiber_b_color"])
                # Color-code status
                if col == 10:
                    status = sp.get("status", "")
                    if status == "spliced":
                        cell.setBackground(QColor(200, 255, 200))
                    elif status == "tested":
                        cell.setBackground(QColor(200, 200, 255))
                    elif status == "faulty":
                        cell.setBackground(QColor(255, 200, 200))
                self.splice_table.setItem(row, col, cell)

    def _apply_color_bg(self, cell: QTableWidgetItem, color_name: str):
        color_map = {
            "Blue": "#1f77b4", "Orange": "#ff7f0e", "Green": "#2ca02c",
            "Brown": "#8c564b", "Slate": "#7f7f7f", "White": "#eeeeee",
            "Red": "#d62728", "Black": "#333333", "Yellow": "#bcbd22",
            "Violet": "#9467bd", "Pink": "#e377c2", "Aqua": "#17becf",
        }
        hex_val = color_map.get(color_name)
        if hex_val:
            cell.setBackground(QColor(hex_val))
            # White text on dark backgrounds
            c = QColor(hex_val)
            if c.lightness() < 128:
                cell.setForeground(QColor(255, 255, 255))

    def _add_closure(self):
        dlg = AddClosureDialog(self.iface, self)
        if dlg.exec_() == QDialog.Accepted:
            self._load_data()

    def _add_tray(self):
        # Find selected closure
        item = self.tree.currentItem()
        if not item:
            return
        data = item.data(0, Qt.UserRole)
        if not data:
            return

        if data[0] == "tray":
            cl = data[2]
        else:
            cl = data[1]

        dlg = AddTrayDialog(cl["id"], self)
        if dlg.exec_() == QDialog.Accepted:
            self._load_data()

    def _add_splice(self):
        if self._current_tray_id is None:
            return
        dlg = SpliceRecordForm(self._current_tray_id, iface=self.iface, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self._load_splices(self._current_tray_id)

    def _edit_splice(self):
        row = self.splice_table.currentRow()
        if row < 0:
            return
        cell = self.splice_table.item(row, 0)
        if not cell:
            return
        sp = cell.data(Qt.UserRole)
        if not sp:
            return
        dlg = SpliceRecordForm(
            sp.get("tray_id"), splice_data=sp,
            iface=self.iface, parent=self
        )
        if dlg.exec_() == QDialog.Accepted:
            if self._current_tray_id:
                self._load_splices(self._current_tray_id)

    def _zoom_to_closure(self):
        item = self.tree.currentItem()
        if not item:
            return
        data = item.data(0, Qt.UserRole)
        if not data:
            return
        cl = data[1] if data[0] == "closure" else data[2]
        lon = cl.get("lon")
        lat = cl.get("lat")
        if lon and lat:
            pt = QgsPointXY(float(lon), float(lat))
            rect = QgsRectangle(pt.x() - 0.001, pt.y() - 0.001,
                                pt.x() + 0.001, pt.y() + 0.001)
            self.iface.mapCanvas().setExtent(rect)
            self.iface.mapCanvas().refresh()


# ======================================================================
# Add Closure Dialog
# ======================================================================

class AddClosureDialog(QDialog):
    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.setWindowTitle("Add Splice Closure")
        self.setMinimumWidth(350)

        layout = QFormLayout(self)

        self.cmb_type = QComboBox()
        self.cmb_type.addItems(["dome", "inline", "wall-mount"])
        layout.addRow("Closure type:", self.cmb_type)

        self.spin_trays = QSpinBox()
        self.spin_trays.setRange(1, 20)
        self.spin_trays.setValue(4)
        layout.addRow("Initial trays:", self.spin_trays)

        self.cmb_muf = QComboBox()
        self.cmb_muf.addItem("(None - manual position)", None)
        # Populate from Nastavci layer
        for lyr in QgsProject.instance().mapLayers().values():
            if isinstance(lyr, QgsVectorLayer) and "nastavci" in lyr.name().lower():
                for feat in lyr.getFeatures():
                    fid = feat.id()
                    name = feat.attribute("naziv") or f"Muf #{fid}"
                    self.cmb_muf.addItem(name, fid)
        layout.addRow("Link to Muf (Nastavci):", self.cmb_muf)

        self.cmb_project = QComboBox()
        self.cmb_project.addItem("(No project)", None)
        try:
            api = _get_api_client()
            projects = api.list_projects()
            for p in projects:
                self.cmb_project.addItem(p["name"], p["id"])
        except Exception:
            pass
        layout.addRow("Project:", self.cmb_project)

        btn_row = QHBoxLayout()
        btn_ok = QPushButton("Create")
        btn_ok.clicked.connect(self._create)
        btn_row.addWidget(btn_ok)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)
        layout.addRow(btn_row)

    def _create(self):
        try:
            api = _get_api_client()

            # Get position from selected muf or map center
            muf_fid = self.cmb_muf.currentData()
            lon, lat = None, None
            if muf_fid is not None:
                for lyr in QgsProject.instance().mapLayers().values():
                    if isinstance(lyr, QgsVectorLayer) and "nastavci" in lyr.name().lower():
                        for feat in lyr.getFeatures():
                            if feat.id() == muf_fid:
                                pt = feat.geometry().asPoint()
                                lon, lat = pt.x(), pt.y()
                                break
            if lon is None:
                center = self.iface.mapCanvas().center()
                lon, lat = center.x(), center.y()

            data = {
                "closure_type": self.cmb_type.currentText(),
                "tray_count": self.spin_trays.value(),
                "muf_fid": muf_fid,
                "project_id": self.cmb_project.currentData(),
                "lon": lon,
                "lat": lat,
            }
            api.create_closure(data)
            QMessageBox.information(self, "FiberQ", "Splice closure created.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


# ======================================================================
# Add Tray Dialog
# ======================================================================

class AddTrayDialog(QDialog):
    def __init__(self, closure_id: int, parent=None):
        super().__init__(parent)
        self.closure_id = closure_id
        self.setWindowTitle("Add Splice Tray")
        self.setMinimumWidth(300)

        layout = QFormLayout(self)

        self.spin_num = QSpinBox()
        self.spin_num.setRange(1, 50)
        layout.addRow("Tray number:", self.spin_num)

        self.cmb_type = QComboBox()
        self.cmb_type.addItems(["12F", "24F", "6F", "48F"])
        layout.addRow("Tray type:", self.cmb_type)

        self.spin_cap = QSpinBox()
        self.spin_cap.setRange(1, 96)
        self.spin_cap.setValue(12)
        layout.addRow("Capacity:", self.spin_cap)

        btn_row = QHBoxLayout()
        btn_ok = QPushButton("Create")
        btn_ok.clicked.connect(self._create)
        btn_row.addWidget(btn_ok)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)
        layout.addRow(btn_row)

    def _create(self):
        try:
            api = _get_api_client()
            data = {
                "tray_number": self.spin_num.value(),
                "tray_type": self.cmb_type.currentText(),
                "capacity": self.spin_cap.value(),
            }
            api.create_tray(self.closure_id, data)
            QMessageBox.information(self, "FiberQ", "Tray added.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


# ======================================================================
# Splice Record Form
# ======================================================================

class SpliceRecordForm(QDialog):
    """Form for recording a single splice – used both from QGIS Desktop
    and as the basis for QField .ui form generation."""

    def __init__(self, tray_id: int, splice_data: dict = None,
                 iface=None, parent=None):
        super().__init__(parent)
        self.tray_id = tray_id
        self.splice_data = splice_data or {}
        self.iface = iface
        self._is_edit = bool(splice_data and splice_data.get("id"))
        self.setWindowTitle("Edit Splice" if self._is_edit else "Record Splice")
        self.setMinimumWidth(450)

        self._build_ui()
        if self._is_edit:
            self._populate()

    def _build_ui(self):
        layout = QFormLayout(self)

        self.spin_pos = QSpinBox()
        self.spin_pos.setRange(1, 96)
        layout.addRow("Position in tray:", self.spin_pos)

        # Cable A side
        grp_a = QGroupBox("Side A")
        la = QFormLayout(grp_a)
        self.cmb_cable_a = QComboBox()
        self._populate_cables(self.cmb_cable_a)
        la.addRow("Cable:", self.cmb_cable_a)
        self.spin_tube_a = QSpinBox()
        self.spin_tube_a.setRange(1, 24)
        la.addRow("Tube #:", self.spin_tube_a)
        self.le_tube_a_color = QLineEdit()
        la.addRow("Tube color:", self.le_tube_a_color)
        self.spin_fiber_a = QSpinBox()
        self.spin_fiber_a.setRange(1, 144)
        la.addRow("Fiber #:", self.spin_fiber_a)
        self.le_fiber_a_color = QLineEdit()
        la.addRow("Fiber color:", self.le_fiber_a_color)
        layout.addRow(grp_a)

        # Cable B side
        grp_b = QGroupBox("Side B")
        lb = QFormLayout(grp_b)
        self.cmb_cable_b = QComboBox()
        self._populate_cables(self.cmb_cable_b)
        lb.addRow("Cable:", self.cmb_cable_b)
        self.spin_tube_b = QSpinBox()
        self.spin_tube_b.setRange(1, 24)
        lb.addRow("Tube #:", self.spin_tube_b)
        self.le_tube_b_color = QLineEdit()
        lb.addRow("Tube color:", self.le_tube_b_color)
        self.spin_fiber_b = QSpinBox()
        self.spin_fiber_b.setRange(1, 144)
        lb.addRow("Fiber #:", self.spin_fiber_b)
        self.le_fiber_b_color = QLineEdit()
        lb.addRow("Fiber color:", self.le_fiber_b_color)
        layout.addRow(grp_b)

        # Splice properties
        self.cmb_type = QComboBox()
        self.cmb_type.addItems(["fusion", "mechanical"])
        layout.addRow("Splice type:", self.cmb_type)

        self.spin_loss = QDoubleSpinBox()
        self.spin_loss.setRange(0.0, 10.0)
        self.spin_loss.setDecimals(3)
        self.spin_loss.setSingleStep(0.01)
        self.spin_loss.setSuffix(" dB")
        layout.addRow("Loss:", self.spin_loss)

        self.cmb_status = QComboBox()
        self.cmb_status.addItems(["planned", "spliced", "tested", "faulty"])
        layout.addRow("Status:", self.cmb_status)

        self.le_notes = QLineEdit()
        layout.addRow("Notes:", self.le_notes)

        # Buttons
        btn_row = QHBoxLayout()
        btn_save = QPushButton("Update" if self._is_edit else "Save")
        btn_save.clicked.connect(self._save)
        btn_row.addWidget(btn_save)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)
        layout.addRow(btn_row)

    def _populate_cables(self, cmb: QComboBox):
        cmb.addItem("(Select cable)", None)
        for lyr in QgsProject.instance().mapLayers().values():
            if not isinstance(lyr, QgsVectorLayer):
                continue
            ln = lyr.name().lower()
            if "kabl" in ln or "cable" in ln:
                for feat in lyr.getFeatures():
                    fid = feat.id()
                    name = feat.attribute("naziv") or f"Cable #{fid}"
                    cmb.addItem(f"{lyr.name()}: {name}", (lyr.id(), fid))

    def _populate(self):
        sp = self.splice_data
        self.spin_pos.setValue(sp.get("position_in_tray", 1))
        self.spin_tube_a.setValue(sp.get("tube_a_number", 1))
        self.le_tube_a_color.setText(sp.get("tube_a_color", ""))
        self.spin_fiber_a.setValue(sp.get("fiber_a_number", 1))
        self.le_fiber_a_color.setText(sp.get("fiber_a_color", ""))
        self.spin_tube_b.setValue(sp.get("tube_b_number", 1))
        self.le_tube_b_color.setText(sp.get("tube_b_color", ""))
        self.spin_fiber_b.setValue(sp.get("fiber_b_number", 1))
        self.le_fiber_b_color.setText(sp.get("fiber_b_color", ""))

        idx_type = self.cmb_type.findText(sp.get("splice_type", "fusion"))
        if idx_type >= 0:
            self.cmb_type.setCurrentIndex(idx_type)

        self.spin_loss.setValue(sp.get("loss_db", 0) or 0)

        idx_status = self.cmb_status.findText(sp.get("status", "planned"))
        if idx_status >= 0:
            self.cmb_status.setCurrentIndex(idx_status)

        self.le_notes.setText(sp.get("notes", "") or "")

        # Try to select cable A
        cable_a_key = (sp.get("cable_a_layer_id"), sp.get("cable_a_fid"))
        for i in range(self.cmb_cable_a.count()):
            if self.cmb_cable_a.itemData(i) == cable_a_key:
                self.cmb_cable_a.setCurrentIndex(i)
                break

        cable_b_key = (sp.get("cable_b_layer_id"), sp.get("cable_b_fid"))
        for i in range(self.cmb_cable_b.count()):
            if self.cmb_cable_b.itemData(i) == cable_b_key:
                self.cmb_cable_b.setCurrentIndex(i)
                break

    def _save(self):
        cable_a = self.cmb_cable_a.currentData()
        cable_b = self.cmb_cable_b.currentData()

        data = {
            "tray_id": self.tray_id,
            "position_in_tray": self.spin_pos.value(),
            "cable_a_layer_id": cable_a[0] if cable_a else None,
            "cable_a_fid": cable_a[1] if cable_a else None,
            "fiber_a_number": self.spin_fiber_a.value(),
            "fiber_a_color": self.le_fiber_a_color.text().strip(),
            "tube_a_number": self.spin_tube_a.value(),
            "tube_a_color": self.le_tube_a_color.text().strip(),
            "cable_b_layer_id": cable_b[0] if cable_b else None,
            "cable_b_fid": cable_b[1] if cable_b else None,
            "fiber_b_number": self.spin_fiber_b.value(),
            "fiber_b_color": self.le_fiber_b_color.text().strip(),
            "tube_b_number": self.spin_tube_b.value(),
            "tube_b_color": self.le_tube_b_color.text().strip(),
            "splice_type": self.cmb_type.currentText(),
            "loss_db": self.spin_loss.value(),
            "status": self.cmb_status.currentText(),
            "notes": self.le_notes.text().strip() or None,
        }

        try:
            api = _get_api_client()
            if self._is_edit:
                api.update_splice(self.splice_data["id"], data)
                QMessageBox.information(self, "FiberQ", "Splice updated.")
            else:
                api.create_splice(data)
                QMessageBox.information(self, "FiberQ", "Splice recorded.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


# ======================================================================
# Fiber Trace Dialog
# ======================================================================

class FiberTraceDialog(QDialog):
    """
    Trace a fiber end-to-end from an element port.
    Shows the complete path: OLT → cables → splices → ONU with
    cumulative loss and length.
    """

    def __init__(self, iface, parent=None):
        super().__init__(parent or iface.mainWindow(), flags=Qt.Window)
        self.iface = iface
        self.setWindowTitle("FiberQ – Fiber Trace")
        self.setMinimumSize(700, 500)

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Input section
        input_grp = QGroupBox("Trace Parameters")
        input_layout = QFormLayout(input_grp)

        self.cmb_element = QComboBox()
        self.cmb_element.addItem("(Select element)", None)
        # Populate elements from active project layers
        for lyr in QgsProject.instance().mapLayers().values():
            if not isinstance(lyr, QgsVectorLayer):
                continue
            ln = lyr.name().lower()
            if any(x in ln for x in ["odf", "otb", "tb", "patch", "element",
                                      "olt", "onu", "ont", "splitter"]):
                for feat in lyr.getFeatures():
                    fid = feat.id()
                    name = feat.attribute("naziv") or feat.attribute("oznaka") or f"#{fid}"
                    self.cmb_element.addItem(f"{lyr.name()}: {name} (FID {fid})", fid)
        input_layout.addRow("Element:", self.cmb_element)

        self.spin_port = QSpinBox()
        self.spin_port.setRange(1, 144)
        input_layout.addRow("Port number:", self.spin_port)

        self.btn_trace = QPushButton("Trace Fiber")
        self.btn_trace.clicked.connect(self._do_trace)
        input_layout.addRow(self.btn_trace)

        layout.addWidget(input_grp)

        # Results section
        self.lbl_summary = QLabel("")
        self.lbl_summary.setStyleSheet("font-weight: bold; padding: 5px;")
        layout.addWidget(self.lbl_summary)

        self.path_table = QTableWidget()
        self.path_table.setColumnCount(7)
        self.path_table.setHorizontalHeaderLabels([
            "Segment", "Type", "From", "To",
            "Cable/Fiber", "Loss (dB)", "Length (m)"
        ])
        self.path_table.horizontalHeader().setStretchLastSection(True)
        self.path_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.path_table.setAlternatingRowColors(True)
        layout.addWidget(self.path_table)

        # Highlight path on map button
        btn_row = QHBoxLayout()
        self.btn_highlight = QPushButton("Highlight on Map")
        self.btn_highlight.clicked.connect(self._highlight_path)
        self.btn_highlight.setEnabled(False)
        btn_row.addWidget(self.btn_highlight)

        self.btn_clear = QPushButton("Clear Highlight")
        self.btn_clear.clicked.connect(self._clear_highlight)
        btn_row.addWidget(self.btn_clear)
        layout.addLayout(btn_row)

        self._trace_result = None

    def _do_trace(self):
        element_fid = self.cmb_element.currentData()
        if element_fid is None:
            QMessageBox.warning(self, "FiberQ", "Select an element first.")
            return

        port = self.spin_port.value()

        try:
            api = _get_api_client()
            result = api.trace_fiber(element_fid, port)
        except Exception as e:
            QMessageBox.warning(self, "FiberQ", f"Trace failed:\n{e}")
            return

        self._trace_result = result
        segments = result.get("segments", [])
        total_loss = result.get("total_loss_db", 0)
        total_length = result.get("total_length_m", 0)
        status = result.get("status", "")

        self.lbl_summary.setText(
            f"Path: {len(segments)} segments | "
            f"Total loss: {total_loss:.2f} dB | "
            f"Total length: {total_length:.1f} m | "
            f"Status: {status}"
        )

        self.path_table.setRowCount(len(segments))
        for row, seg in enumerate(segments):
            items = [
                str(row + 1),
                seg.get("type", ""),
                str(seg.get("from_id", "")),
                str(seg.get("to_id", "")),
                f"Cable {seg.get('cable_fid', '')} / Fiber {seg.get('fiber_num', '')}",
                f"{seg.get('loss_db', 0):.2f}",
                f"{seg.get('length_m', 0):.1f}",
            ]
            for col, val in enumerate(items):
                cell = QTableWidgetItem(val)
                # Color-code segment types
                seg_type = seg.get("type", "")
                if seg_type == "splice":
                    cell.setBackground(QColor(255, 255, 200))
                elif seg_type == "cable":
                    cell.setBackground(QColor(200, 230, 255))
                elif seg_type == "patch":
                    cell.setBackground(QColor(220, 255, 220))
                self.path_table.setItem(row, col, cell)

        self.btn_highlight.setEnabled(True)

    def _highlight_path(self):
        if not self._trace_result:
            return

        segments = self._trace_result.get("segments", [])

        # Highlight cables referenced in the trace on the map
        for lyr in QgsProject.instance().mapLayers().values():
            if not isinstance(lyr, QgsVectorLayer):
                continue
            ln = lyr.name().lower()
            if "kabl" not in ln and "cable" not in ln:
                continue

            cable_fids = set()
            for seg in segments:
                if seg.get("type") == "cable" and seg.get("cable_fid"):
                    cable_fids.add(seg["cable_fid"])

            if cable_fids:
                lyr.selectByIds(list(cable_fids))

        self.iface.mapCanvas().refresh()

    def _clear_highlight(self):
        for lyr in QgsProject.instance().mapLayers().values():
            if isinstance(lyr, QgsVectorLayer):
                lyr.removeSelection()
        self.iface.mapCanvas().refresh()


# ======================================================================
# Helper: open dialogs from main plugin
# ======================================================================

def open_splice_closure_dialog(iface):
    try:
        dlg = SpliceClosureDialog(iface)
        dlg.show()
        # Keep reference to prevent GC
        iface._fiberq_splice_dlg = dlg
    except Exception as e:
        QMessageBox.critical(iface.mainWindow(), "FiberQ Fiber Plan", str(e))


def open_fiber_trace_dialog(iface):
    try:
        dlg = FiberTraceDialog(iface)
        dlg.show()
        iface._fiberq_trace_dlg = dlg
    except Exception as e:
        QMessageBox.critical(iface.mainWindow(), "FiberQ Fiber Trace", str(e))
