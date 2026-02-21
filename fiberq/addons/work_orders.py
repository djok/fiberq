"""
FiberQ Work Orders Addon – Task assignment, execution tracking,
and SMR (construction activity) reporting.

Provides three main dialogs:
- WorkOrderListDialog: browse, filter, manage work orders
- WorkOrderDialog: create/edit a single work order
- SMRReportViewDialog: view SMR reports with photos
"""

from qgis.PyQt.QtCore import Qt, QDate
from qgis.PyQt.QtGui import QColor, QIcon, QPixmap
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QFormLayout, QLineEdit, QSpinBox,
    QDoubleSpinBox, QSplitter, QTextEdit, QDateEdit,
    QTabWidget, QWidget, QFileDialog, QListWidget, QListWidgetItem
)
from qgis.core import (
    QgsProject, QgsVectorLayer, QgsFeature, QgsGeometry,
    QgsPointXY, QgsRectangle
)
import os


def _get_api_client():
    from .zitadel_auth import get_auth
    from .api_client import FiberQApiClient

    auth = get_auth()
    token = auth.get_token()
    if not token:
        raise RuntimeError(
            "Not authenticated. Please sign in first (FiberQ → Sign In)."
        )
    return FiberQApiClient(token=token)


# ======================================================================
# Work Order List Dialog
# ======================================================================

class WorkOrderListDialog(QDialog):
    """Browse and manage work orders."""

    def __init__(self, iface, parent=None):
        super().__init__(parent or iface.mainWindow(), flags=Qt.Window)
        self.iface = iface
        self.setWindowTitle("FiberQ – Work Orders")
        self.setMinimumSize(850, 500)
        self._orders = []

        self._build_ui()
        self._load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Filters row
        filter_row = QHBoxLayout()

        filter_row.addWidget(QLabel("Status:"))
        self.cmb_status = QComboBox()
        self.cmb_status.addItems([
            "(All)", "created", "assigned", "in_progress",
            "completed", "verified", "rejected"
        ])
        self.cmb_status.currentIndexChanged.connect(self._load_data)
        filter_row.addWidget(self.cmb_status)

        filter_row.addWidget(QLabel("Project:"))
        self.cmb_project = QComboBox()
        self.cmb_project.addItem("(All)", None)
        try:
            api = _get_api_client()
            for p in api.list_projects():
                self.cmb_project.addItem(p["name"], p["id"])
        except Exception:
            pass
        self.cmb_project.currentIndexChanged.connect(self._load_data)
        filter_row.addWidget(self.cmb_project)

        filter_row.addStretch()

        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.clicked.connect(self._load_data)
        filter_row.addWidget(self.btn_refresh)

        self.btn_new = QPushButton("+ New Work Order")
        self.btn_new.clicked.connect(self._create_new)
        filter_row.addWidget(self.btn_new)

        layout.addLayout(filter_row)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "Title", "Type", "Priority", "Status",
            "Assigned To", "Due Date", "Created"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.doubleClicked.connect(self._on_double_click)
        layout.addWidget(self.table)

        # Action buttons
        btn_row = QHBoxLayout()

        self.btn_edit = QPushButton("Edit")
        self.btn_edit.clicked.connect(self._edit_selected)
        btn_row.addWidget(self.btn_edit)

        self.btn_assign = QPushButton("Assign")
        self.btn_assign.clicked.connect(self._assign_selected)
        btn_row.addWidget(self.btn_assign)

        self.btn_status = QPushButton("Change Status")
        self.btn_status.clicked.connect(self._change_status)
        btn_row.addWidget(self.btn_status)

        self.btn_smr = QPushButton("View SMR Reports")
        self.btn_smr.clicked.connect(self._view_smr)
        btn_row.addWidget(self.btn_smr)

        self.btn_zoom = QPushButton("Zoom To")
        self.btn_zoom.clicked.connect(self._zoom_to)
        btn_row.addWidget(self.btn_zoom)

        layout.addLayout(btn_row)

    def _load_data(self):
        status_filter = self.cmb_status.currentText()
        if status_filter == "(All)":
            status_filter = None
        project_id = self.cmb_project.currentData()

        try:
            api = _get_api_client()
            self._orders = api.list_work_orders(
                project_id=project_id, status=status_filter
            )
        except Exception as e:
            QMessageBox.warning(self, "FiberQ", f"Failed to load work orders:\n{e}")
            return

        self.table.setRowCount(len(self._orders))
        for row, wo in enumerate(self._orders):
            items = [
                str(wo.get("id", "")),
                wo.get("title", ""),
                wo.get("order_type", ""),
                wo.get("priority", ""),
                wo.get("status", ""),
                wo.get("assigned_to_sub", "") or "(unassigned)",
                wo.get("due_date", "") or "",
                (wo.get("created_at", "") or "")[:10],
            ]
            for col, val in enumerate(items):
                cell = QTableWidgetItem(val)
                cell.setData(Qt.UserRole, wo)

                # Color-code priority
                if col == 3:
                    prio = wo.get("priority", "")
                    if prio == "urgent":
                        cell.setBackground(QColor(255, 180, 180))
                    elif prio == "high":
                        cell.setBackground(QColor(255, 220, 180))
                    elif prio == "medium":
                        cell.setBackground(QColor(255, 255, 200))

                # Color-code status
                if col == 4:
                    st = wo.get("status", "")
                    status_colors = {
                        "created": QColor(230, 230, 230),
                        "assigned": QColor(200, 220, 255),
                        "in_progress": QColor(255, 255, 200),
                        "completed": QColor(200, 255, 200),
                        "verified": QColor(180, 255, 180),
                        "rejected": QColor(255, 200, 200),
                    }
                    if st in status_colors:
                        cell.setBackground(status_colors[st])

                self.table.setItem(row, col, cell)

    def _get_selected_wo(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "FiberQ", "Select a work order first.")
            return None
        cell = self.table.item(row, 0)
        return cell.data(Qt.UserRole) if cell else None

    def _on_double_click(self, index):
        self._edit_selected()

    def _create_new(self):
        dlg = WorkOrderDialog(iface=self.iface, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self._load_data()

    def _edit_selected(self):
        wo = self._get_selected_wo()
        if not wo:
            return
        dlg = WorkOrderDialog(wo_data=wo, iface=self.iface, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self._load_data()

    def _assign_selected(self):
        wo = self._get_selected_wo()
        if not wo:
            return
        from qgis.PyQt.QtWidgets import QInputDialog
        sub, ok = QInputDialog.getText(
            self, "Assign Work Order",
            "Enter the Zitadel user subject ID (or email):",
            text=wo.get("assigned_to_sub", "")
        )
        if not ok or not sub.strip():
            return
        try:
            api = _get_api_client()
            api.assign_work_order(wo["id"], sub.strip())
            QMessageBox.information(self, "FiberQ", "Work order assigned.")
            self._load_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _change_status(self):
        wo = self._get_selected_wo()
        if not wo:
            return

        statuses = ["created", "assigned", "in_progress",
                     "completed", "verified", "rejected"]
        from qgis.PyQt.QtWidgets import QInputDialog
        new_status, ok = QInputDialog.getItem(
            self, "Change Status",
            f"Current status: {wo.get('status', '')}\nNew status:",
            statuses, statuses.index(wo.get("status", "created")), False
        )
        if not ok:
            return
        try:
            api = _get_api_client()
            api.change_work_order_status(wo["id"], new_status)
            QMessageBox.information(self, "FiberQ", f"Status changed to '{new_status}'.")
            self._load_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _view_smr(self):
        wo = self._get_selected_wo()
        if not wo:
            return
        dlg = SMRReportViewDialog(wo["id"], iface=self.iface, parent=self)
        dlg.exec_()

    def _zoom_to(self):
        wo = self._get_selected_wo()
        if not wo:
            return
        # If the work order has area_geom bounds, use those
        # For now just show a message
        QMessageBox.information(
            self, "FiberQ",
            f"Work order #{wo['id']}: {wo.get('title', '')}\n"
            f"Status: {wo.get('status', '')}"
        )


# ======================================================================
# Work Order Dialog (Create / Edit)
# ======================================================================

class WorkOrderDialog(QDialog):
    """Create or edit a single work order."""

    def __init__(self, wo_data: dict = None, iface=None, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.wo_data = wo_data or {}
        self._is_edit = bool(wo_data and wo_data.get("id"))
        self.setWindowTitle("Edit Work Order" if self._is_edit else "New Work Order")
        self.setMinimumWidth(500)

        self._build_ui()
        if self._is_edit:
            self._populate()

    def _build_ui(self):
        layout = QFormLayout(self)

        self.le_title = QLineEdit()
        layout.addRow("Title:", self.le_title)

        self.te_desc = QTextEdit()
        self.te_desc.setMaximumHeight(80)
        layout.addRow("Description:", self.te_desc)

        self.cmb_type = QComboBox()
        self.cmb_type.addItems([
            "installation", "splice", "repair", "survey", "maintenance"
        ])
        layout.addRow("Type:", self.cmb_type)

        self.cmb_priority = QComboBox()
        self.cmb_priority.addItems(["low", "medium", "high", "urgent"])
        self.cmb_priority.setCurrentIndex(1)  # medium default
        layout.addRow("Priority:", self.cmb_priority)

        self.cmb_project = QComboBox()
        self.cmb_project.addItem("(No project)", None)
        try:
            api = _get_api_client()
            for p in api.list_projects():
                self.cmb_project.addItem(p["name"], p["id"])
        except Exception:
            pass
        layout.addRow("Project:", self.cmb_project)

        self.de_due = QDateEdit()
        self.de_due.setCalendarPopup(True)
        self.de_due.setDate(QDate.currentDate().addDays(7))
        layout.addRow("Due date:", self.de_due)

        self.le_assigned = QLineEdit()
        self.le_assigned.setPlaceholderText("Zitadel user subject ID")
        layout.addRow("Assign to:", self.le_assigned)

        # Work order items
        items_grp = QGroupBox("Work Items")
        items_layout = QVBoxLayout(items_grp)

        self.items_table = QTableWidget()
        self.items_table.setColumnCount(4)
        self.items_table.setHorizontalHeaderLabels([
            "Description", "Type", "Quantity", "Unit"
        ])
        self.items_table.horizontalHeader().setStretchLastSection(True)
        items_layout.addWidget(self.items_table)

        item_btns = QHBoxLayout()
        btn_add_item = QPushButton("+ Item")
        btn_add_item.clicked.connect(self._add_item_row)
        item_btns.addWidget(btn_add_item)
        btn_rm_item = QPushButton("- Remove")
        btn_rm_item.clicked.connect(self._remove_item_row)
        item_btns.addWidget(btn_rm_item)
        items_layout.addLayout(item_btns)

        layout.addRow(items_grp)

        # Buttons
        btn_row = QHBoxLayout()
        btn_save = QPushButton("Update" if self._is_edit else "Create")
        btn_save.clicked.connect(self._save)
        btn_row.addWidget(btn_save)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)
        layout.addRow(btn_row)

    def _add_item_row(self):
        row = self.items_table.rowCount()
        self.items_table.insertRow(row)
        self.items_table.setItem(row, 0, QTableWidgetItem(""))
        # Type combo
        cmb = QComboBox()
        cmb.addItems(["cable_laying", "splice", "pole_install",
                       "manhole_install", "duct_install", "other"])
        self.items_table.setCellWidget(row, 1, cmb)
        self.items_table.setItem(row, 2, QTableWidgetItem("1"))
        self.items_table.setItem(row, 3, QTableWidgetItem("pcs"))

    def _remove_item_row(self):
        row = self.items_table.currentRow()
        if row >= 0:
            self.items_table.removeRow(row)

    def _populate(self):
        wo = self.wo_data
        self.le_title.setText(wo.get("title", ""))
        self.te_desc.setPlainText(wo.get("description", "") or "")

        idx = self.cmb_type.findText(wo.get("order_type", ""))
        if idx >= 0:
            self.cmb_type.setCurrentIndex(idx)

        idx = self.cmb_priority.findText(wo.get("priority", ""))
        if idx >= 0:
            self.cmb_priority.setCurrentIndex(idx)

        # Project
        pid = wo.get("project_id")
        if pid:
            for i in range(self.cmb_project.count()):
                if self.cmb_project.itemData(i) == pid:
                    self.cmb_project.setCurrentIndex(i)
                    break

        if wo.get("due_date"):
            self.de_due.setDate(QDate.fromString(wo["due_date"][:10], "yyyy-MM-dd"))

        self.le_assigned.setText(wo.get("assigned_to_sub", "") or "")

        # Load existing items
        try:
            api = _get_api_client()
            items = api.list_work_order_items(wo["id"])
            for item_data in items:
                self._add_item_row()
                row = self.items_table.rowCount() - 1
                self.items_table.item(row, 0).setText(item_data.get("description", ""))
                cmb = self.items_table.cellWidget(row, 1)
                if cmb:
                    idx2 = cmb.findText(item_data.get("item_type", ""))
                    if idx2 >= 0:
                        cmb.setCurrentIndex(idx2)
                self.items_table.item(row, 2).setText(str(item_data.get("quantity", 1)))
                self.items_table.item(row, 3).setText(item_data.get("unit", "pcs"))
        except Exception:
            pass

    def _save(self):
        title = self.le_title.text().strip()
        if not title:
            QMessageBox.warning(self, "FiberQ", "Title is required.")
            return

        data = {
            "title": title,
            "description": self.te_desc.toPlainText().strip() or None,
            "order_type": self.cmb_type.currentText(),
            "priority": self.cmb_priority.currentText(),
            "project_id": self.cmb_project.currentData(),
            "due_date": self.de_due.date().toString("yyyy-MM-dd"),
            "assigned_to_sub": self.le_assigned.text().strip() or None,
        }

        try:
            api = _get_api_client()
            if self._is_edit:
                api.update_work_order(self.wo_data["id"], data)
                wo_id = self.wo_data["id"]
            else:
                result = api.create_work_order(data)
                wo_id = result.get("id")

            # Create work order items
            if wo_id:
                for row in range(self.items_table.rowCount()):
                    desc_item = self.items_table.item(row, 0)
                    desc = desc_item.text().strip() if desc_item else ""
                    if not desc:
                        continue
                    cmb = self.items_table.cellWidget(row, 1)
                    item_type = cmb.currentText() if cmb else "other"
                    qty_item = self.items_table.item(row, 2)
                    qty = float(qty_item.text()) if qty_item else 1
                    unit_item = self.items_table.item(row, 3)
                    unit = unit_item.text() if unit_item else "pcs"

                    api.create_work_order_item(wo_id, {
                        "description": desc,
                        "item_type": item_type,
                        "quantity": qty,
                        "unit": unit,
                    })

            QMessageBox.information(
                self, "FiberQ",
                "Work order updated." if self._is_edit else "Work order created."
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


# ======================================================================
# SMR Report View Dialog
# ======================================================================

class SMRReportViewDialog(QDialog):
    """View SMR reports for a work order."""

    def __init__(self, work_order_id: int, iface=None, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.wo_id = work_order_id
        self.setWindowTitle(f"FiberQ – SMR Reports (WO #{work_order_id})")
        self.setMinimumSize(650, 450)

        self._build_ui()
        self._load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Reports table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID", "Date", "Reporter", "Crew", "Hours", "Weather"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.itemSelectionChanged.connect(self._on_select)
        layout.addWidget(self.table)

        # Detail area
        detail_grp = QGroupBox("Report Details")
        detail_layout = QVBoxLayout(detail_grp)

        self.lbl_activities = QLabel("Activities: -")
        self.lbl_activities.setWordWrap(True)
        detail_layout.addWidget(self.lbl_activities)

        self.lbl_materials = QLabel("Materials: -")
        self.lbl_materials.setWordWrap(True)
        detail_layout.addWidget(self.lbl_materials)

        self.lbl_issues = QLabel("Issues: -")
        self.lbl_issues.setWordWrap(True)
        detail_layout.addWidget(self.lbl_issues)

        layout.addWidget(detail_grp)

        # Buttons
        btn_row = QHBoxLayout()
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

    def _load_data(self):
        try:
            api = _get_api_client()
            reports = api.list_smr_reports(self.wo_id)
        except Exception as e:
            QMessageBox.warning(self, "FiberQ", f"Failed to load SMR reports:\n{e}")
            return

        self.table.setRowCount(len(reports))
        for row, rpt in enumerate(reports):
            items = [
                str(rpt.get("id", "")),
                rpt.get("report_date", ""),
                rpt.get("reported_by_sub", ""),
                str(rpt.get("crew_size", "")),
                str(rpt.get("hours_worked", "")),
                rpt.get("weather", ""),
            ]
            for col, val in enumerate(items):
                cell = QTableWidgetItem(val)
                cell.setData(Qt.UserRole, rpt)
                self.table.setItem(row, col, cell)

    def _on_select(self):
        row = self.table.currentRow()
        if row < 0:
            return
        cell = self.table.item(row, 0)
        if not cell:
            return
        rpt = cell.data(Qt.UserRole)
        if not rpt:
            return

        import json

        activities = rpt.get("activities")
        if isinstance(activities, str):
            try:
                activities = json.loads(activities)
            except Exception:
                pass
        if isinstance(activities, list):
            self.lbl_activities.setText("Activities: " + ", ".join(str(a) for a in activities))
        elif activities:
            self.lbl_activities.setText(f"Activities: {activities}")
        else:
            self.lbl_activities.setText("Activities: -")

        materials = rpt.get("materials_used")
        if isinstance(materials, str):
            try:
                materials = json.loads(materials)
            except Exception:
                pass
        if isinstance(materials, list):
            self.lbl_materials.setText("Materials: " + ", ".join(str(m) for m in materials))
        elif materials:
            self.lbl_materials.setText(f"Materials: {materials}")
        else:
            self.lbl_materials.setText("Materials: -")

        self.lbl_issues.setText(f"Issues: {rpt.get('issues', '-') or '-'}")


# ======================================================================
# Helper: open dialogs from main plugin
# ======================================================================

def open_work_order_list(iface):
    try:
        dlg = WorkOrderListDialog(iface)
        dlg.show()
        iface._fiberq_wo_dlg = dlg
    except Exception as e:
        QMessageBox.critical(iface.mainWindow(), "FiberQ Work Orders", str(e))


def open_new_work_order(iface):
    try:
        dlg = WorkOrderDialog(iface=iface, parent=iface.mainWindow())
        dlg.exec_()
    except Exception as e:
        QMessageBox.critical(iface.mainWindow(), "FiberQ Work Orders", str(e))
