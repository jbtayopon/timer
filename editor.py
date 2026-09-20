import json
import os
from pathlib import Path

from PySide6.QtCore import Qt, QRectF, QPointF, Signal
from PySide6.QtGui import (
    QColor,
    QBrush,
    QPen,
    QFont,
    QPixmap,
    QImage,
    QTextOption,
    QFontDatabase,
)
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QVBoxLayout,
    QFormLayout,
    QPushButton,
    QLabel,
    QComboBox,
    QSpinBox,
    QColorDialog,
    QFileDialog,
    QMessageBox,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsRectItem,
    QGraphicsTextItem,
    QGraphicsPixmapItem,
    QGraphicsItem,
    QFrame,
    QGroupBox,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QCheckBox,
    QDialogButtonBox,
    QScrollArea,
    QWidget,
)


APP_NAME = "TPX"
CANVAS_WIDTH = 1280
CANVAS_HEIGHT = 720


def get_data_folder():
    public_dir = os.environ.get("PUBLIC")
    if public_dir:
        folder = Path(public_dir) / "Documents" / APP_NAME
    else:
        folder = Path.home() / "Documents" / APP_NAME
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def get_layout_folder():
    folder = get_data_folder() / "layouts"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def safe_event_name(name):
    result = "".join(
        c if c.isalnum() or c in " _-" else "_"
        for c in name
    ).strip()
    return result or "Untitled Event"


def get_layout_path(event_name):
    return get_layout_folder() / f"{safe_event_name(event_name)}.json"


class EditorMessageDialog(QDialog):
    """Message editor used directly inside the Visual Editor."""

    def __init__(self, message=None, parent=None, theme="dark"):
        super().__init__(parent)
        self.theme = theme
        self.setWindowTitle("TPX Message")
        self.resize(560, 390)

        message = message or {
            "name": "New Message",
            "trigger_seconds": 0,
            "message": "NEW MESSAGE",
            "color": "#FFFFFF",
            "beep": False,
            "beep_seconds": 5,
        }

        self.name_edit = QLineEdit(str(message.get("name", "New Message")))
        self.trigger_spin = QSpinBox()
        self.trigger_spin.setRange(-1, 86400)
        self.trigger_spin.setValue(int(message.get("trigger_seconds", 0)))

        self.message_edit = QLineEdit(
            str(message.get("message", "NEW MESSAGE"))
        )

        self.color_edit = QLineEdit(
            str(message.get("color", "#FFFFFF"))
        )

        self.beep_check = QCheckBox("Enable Beep")
        self.beep_check.setChecked(bool(message.get("beep", False)))

        self.beep_seconds = QSpinBox()
        self.beep_seconds.setRange(1, 60)
        self.beep_seconds.setValue(
            max(1, int(message.get("beep_seconds", 5) or 5))
        )

        color_button = QPushButton("Choose Message Color")
        color_button.clicked.connect(self.choose_color)

        form = QFormLayout()
        form.addRow("Name", self.name_edit)
        form.addRow("Trigger Seconds", self.trigger_spin)
        form.addRow("Message", self.message_edit)
        form.addRow("Color", self.color_edit)
        form.addRow("", color_button)
        form.addRow("", self.beep_check)
        form.addRow("Beep Seconds", self.beep_seconds)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

        self.apply_theme()

    def apply_theme(self):
        if self.theme == "light":
            self.setStyleSheet("""
                QDialog { background:#F3F5F7; }
                QLabel,QCheckBox { color:#20252B; }

                QWidget#editorSidebar {
                    background:#F3F5F7;
                }

                QFrame#collapsibleSection {
                    background:#F3F5F7;
                    border:1px solid #C7CDD4;
                    border-radius:7px;
                }
                QFrame#collapsibleSection QPushButton#collapseButton {
                    background:transparent;
                    color:#20252B;
                    border:none;
                    text-align:left;
                    font-weight:bold;
                    padding:7px 8px;
                    margin:0px;
                }
                QFrame#collapsibleSection QWidget#sectionContent {
                    background:transparent;
                    border:none;
                    margin:0px;
                    padding:0px;
                }
                QFrame#collapsibleSection QWidget#propertyForm {
                    background:transparent;
                    border:none;
                }

                QLineEdit,QSpinBox,QComboBox {
                    background:white;
                    color:#20252B;
                    border:1px solid #BFC6CE;
                    border-radius:5px;
                    padding:7px;
                }

                QPushButton {
                    background:#E9EDF2;
                    color:#20252B;
                    border:1px solid #C5CBD2;
                    border-radius:6px;
                    padding:8px;
                }
                QPushButton:hover { background:#DDE3E9; }
            """)
        else:
            self.setStyleSheet("""
                QDialog { background:#11171E; }
                QLabel,QCheckBox { color:#F5F7FA; }

                QWidget#editorSidebar {
                    background:#11171E;
                }

                QFrame#collapsibleSection {
                    background:#11171E;
                    border:1px solid #303B47;
                    border-radius:7px;
                }
                QFrame#collapsibleSection QPushButton#collapseButton {
                    background:transparent;
                    color:#F5F7FA;
                    border:none;
                    text-align:left;
                    font-weight:bold;
                    padding:7px 8px;
                    margin:0px;
                }
                QFrame#collapsibleSection QWidget#sectionContent {
                    background:transparent;
                    border:none;
                    margin:0px;
                    padding:0px;
                }
                QFrame#collapsibleSection QWidget#propertyForm {
                    background:transparent;
                    border:none;
                }

                QLineEdit,QSpinBox,QComboBox {
                    background:#18212B;
                    color:#F5F7FA;
                    border:1px solid #3D4C5B;
                    border-radius:5px;
                    padding:7px;
                }

                QPushButton {
                    background:#242E39;
                    color:#F5F7FA;
                    border:1px solid #40505F;
                    border-radius:6px;
                    padding:8px;
                }
                QPushButton:hover { background:#2C3947; }
            """)

    def choose_color(self):
        color = QColorDialog.getColor(
            QColor(self.color_edit.text()),
            self,
            "Message Color",
        )
        if color.isValid():
            self.color_edit.setText(color.name())

    def get_message(self):
        return {
            "name": self.name_edit.text().strip() or "New Message",
            "trigger_seconds": self.trigger_spin.value(),
            "message": self.message_edit.text(),
            "color": self.color_edit.text().strip() or "#FFFFFF",
            "beep": self.beep_check.isChecked(),
            "beep_seconds": self.beep_seconds.value(),
        }


class EditableTextItem(QGraphicsTextItem):
    HANDLE_SIZE = 12

    def __init__(
        self,
        text="Text",
        item_type="text",
        message_name="",
        dynamic=False,
    ):
        super().__init__(text)

        self.item_type = item_type
        self.message_name = message_name
        self.dynamic = dynamic

        self.resizing = False
        self.resize_start_pos = QPointF()
        self.resize_start_width = 500

        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
        )
        self.setAcceptHoverEvents(True)
        self.setDefaultTextColor(QColor("#FFFFFF"))

        font = QFont("Arial")
        font.setPointSize(48)
        self.setFont(font)
        self.setTextWidth(500)

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)

        if not self.isSelected():
            return

        rect = self.boundingRect()
        pen = QPen(QColor("#FFD21F"))
        pen.setWidth(2)
        pen.setStyle(Qt.PenStyle.DashLine)

        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(rect)

        handle = QRectF(
            rect.right() - self.HANDLE_SIZE,
            rect.bottom() - self.HANDLE_SIZE,
            self.HANDLE_SIZE,
            self.HANDLE_SIZE,
        )
        painter.setPen(QPen(QColor("#FFD21F")))
        painter.setBrush(QBrush(QColor("#FFD21F")))
        painter.drawRect(handle)

    def hoverMoveEvent(self, event):
        if self.isSelected():
            rect = self.boundingRect()
            handle = QRectF(
                rect.right() - self.HANDLE_SIZE * 2,
                rect.bottom() - self.HANDLE_SIZE * 2,
                self.HANDLE_SIZE * 3,
                self.HANDLE_SIZE * 3,
            )

            if handle.contains(event.pos()):
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            else:
                self.setCursor(Qt.CursorShape.OpenHandCursor)
        else:
            self.setCursor(Qt.CursorShape.OpenHandCursor)

        super().hoverMoveEvent(event)

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            return

        rect = self.boundingRect()
        handle = QRectF(
            rect.right() - self.HANDLE_SIZE * 2,
            rect.bottom() - self.HANDLE_SIZE * 2,
            self.HANDLE_SIZE * 3,
            self.HANDLE_SIZE * 3,
        )

        if self.isSelected() and handle.contains(event.pos()):
            self.resizing = True
            self.resize_start_pos = event.scenePos()
            self.resize_start_width = self.textWidth()
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            event.accept()
            return

        self.resizing = False
        self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.resizing:
            delta = event.scenePos().x() - self.resize_start_pos.x()
            new_width = max(
                80,
                min(5000, self.resize_start_width + delta),
            )
            self.setTextWidth(new_width)
            self.update()
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.resizing:
            self.resizing = False
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            self.update()
            event.accept()
            return

        self.setCursor(Qt.CursorShape.OpenHandCursor)
        super().mouseReleaseEvent(event)


class BackgroundItem(QGraphicsRectItem):
    def __init__(self):
        super().__init__(
            QRectF(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT)
        )
        self.setBrush(QBrush(QColor("#000000")))
        self.setPen(QPen(Qt.PenStyle.NoPen))
        self.setZValue(-1000)


class CollapsibleSection(QFrame):
    """Compact collapsible sidebar section used by the TPX editor."""

    def __init__(self, title, content_widget, parent=None, expanded=True):
        super().__init__(parent)
        self.content_widget = content_widget
        self.setObjectName("collapsibleSection")
        self.toggle_button = QPushButton()
        self.toggle_button.setObjectName("collapseButton")
        self.toggle_button.setText(
            f"▾  {title}" if expanded else f"▸  {title}"
        )
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(expanded)
        self.toggle_button.setFlat(True)
        self.toggle_button.clicked.connect(self.toggle)

        layout = QVBoxLayout(self)
        # Header and content are intentionally flush together.
        # No extra gap underneath a collapsible section.
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.toggle_button)
        layout.addWidget(content_widget)

        content_widget.setVisible(expanded)

    def toggle(self, checked):
        self.content_widget.setVisible(checked)
        title = self.toggle_button.text().lstrip("▾▸ ").strip()
        self.toggle_button.setText(
            f"▾  {title}" if checked else f"▸  {title}"
        )


class VisualEditor(QDialog):
    """
    The original TPX editor structure is retained:
    QDialog + 1280x720 canvas + RubberBandDrag + manual resize.

    The upgrade adds:
    - Messages panel inside the editor.
    - Every message gets its own canvas text object.
    - Each message object can be positioned, resized, colored,
      aligned, and font-sized independently.
    - New normal Text objects remain static.
    """

    def __init__(
        self,
        event_name,
        parent=None,
        theme="dark",
        messages=None,
        on_messages_changed=None,
    ):
        super().__init__(parent)

        self.event_name = event_name
        self.theme = theme

        self.messages = messages if messages is not None else []
        self.on_messages_changed = on_messages_changed

        self.background_item = None
        self.background_pixmap = None
        self.background_image_path = ""

        self._loading = False
        self._syncing_message_selection = False

        self.setWindowTitle(f"TPX Editor — {event_name}")
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowSystemMenuHint
            | Qt.WindowType.WindowMinimizeButtonHint
            | Qt.WindowType.WindowMaximizeButtonHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        self.resize(1500, 880)
        self.setMinimumSize(1050, 650)

        self.build_ui()
        self.apply_theme()
        self.load_layout()

    # ---------------------------------------------------------
    # UI
    # ---------------------------------------------------------

    def build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(12)

        # -----------------------------------------------------
        # Scrollable sidebar
        # -----------------------------------------------------
        sidebar = QWidget()
        sidebar.setObjectName("editorSidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(2, 2, 2, 2)
        # Sections should sit directly against each other.
        sidebar_layout.setSpacing(10)

        title = QLabel("TPX VISUAL EDITOR")
        title.setStyleSheet("font-size:20px;font-weight:bold;")
        sidebar_layout.addWidget(title)

        event_label = QLabel(f"Event\n{self.event_name}")
        sidebar_layout.addWidget(event_label)

        # -----------------------------------------------------
        # Messages
        # -----------------------------------------------------
        message_group = QWidget()
        message_group.setObjectName("sectionContent")
        message_layout = QVBoxLayout(message_group)
        message_layout.setContentsMargins(10, 2, 10, 10)

        message_hint = QLabel(
            "Select a message, then position it on the canvas."
        )
        message_hint.setWordWrap(True)
        message_layout.addWidget(message_hint)

        self.message_combo = QComboBox()
        self.message_combo.currentIndexChanged.connect(
            self.select_message_from_combo
        )
        message_layout.addWidget(self.message_combo)

        message_buttons = QHBoxLayout()
        add_message_button = QPushButton("＋ Add")
        edit_message_button = QPushButton("✎ Edit")
        delete_message_button = QPushButton("🗑 Delete")

        add_message_button.clicked.connect(self.add_message)
        edit_message_button.clicked.connect(self.edit_message)
        delete_message_button.clicked.connect(self.delete_message)

        message_buttons.addWidget(add_message_button)
        message_buttons.addWidget(edit_message_button)
        message_buttons.addWidget(delete_message_button)
        message_layout.addLayout(message_buttons)

        sidebar_layout.addWidget(
            CollapsibleSection("Messages", message_group, expanded=True)
        )

        # -----------------------------------------------------
        # Objects - side by side
        # -----------------------------------------------------
        object_group = QWidget()
        object_group.setObjectName("sectionContent")
        object_layout = QHBoxLayout(object_group)
        object_layout.setContentsMargins(10, 4, 10, 10)
        object_layout.setSpacing(8)

        timer_btn = QPushButton("⏱ Timer")
        text_btn = QPushButton("📝 Text")

        timer_btn.clicked.connect(self.add_timer)
        text_btn.clicked.connect(self.add_text)

        object_layout.addWidget(timer_btn)
        object_layout.addWidget(text_btn)

        sidebar_layout.addWidget(
            CollapsibleSection("Objects", object_group, expanded=True)
        )

        # -----------------------------------------------------
        # Background - side by side
        # -----------------------------------------------------
        background_group = QWidget()
        background_group.setObjectName("sectionContent")
        background_layout = QHBoxLayout(background_group)
        background_layout.setContentsMargins(10, 4, 10, 10)
        background_layout.setSpacing(8)

        bg_color_btn = QPushButton("🎨 Color")
        bg_image_btn = QPushButton("🖼 Image")

        bg_color_btn.clicked.connect(self.choose_background_color)
        bg_image_btn.clicked.connect(self.choose_background_image)

        background_layout.addWidget(bg_color_btn)
        background_layout.addWidget(bg_image_btn)

        sidebar_layout.addWidget(
            CollapsibleSection(
                "Background",
                background_group,
                expanded=True,
            )
        )

        # -----------------------------------------------------
        # Selected Object
        # -----------------------------------------------------
        property_group = QWidget()
        property_group.setObjectName("propertyForm")
        property_layout = QFormLayout(property_group)
        property_layout.setContentsMargins(10, 4, 10, 8)

        self.text_edit = QLineEdit()

        self.x_spin = QSpinBox()
        self.y_spin = QSpinBox()
        self.width_spin = QSpinBox()
        self.font_spin = QSpinBox()

        self.x_spin.setRange(-2000, 5000)
        self.y_spin.setRange(-2000, 5000)
        self.width_spin.setRange(20, 5000)
        self.font_spin.setRange(8, 500)

        # Font family
        self.font_combo = QComboBox()
        families = QFontDatabase.families()
        preferred = [
            "Arial",
            "Aptos",
            "Segoe UI",
            "Tahoma",
            "Verdana",
            "Times New Roman",
            "Georgia",
            "Courier New",
        ]
        ordered = []
        for family in preferred:
            if family in families and family not in ordered:
                ordered.append(family)
        for family in families:
            if family not in ordered:
                ordered.append(family)
        self.font_combo.addItems(ordered)

        self.alignment_combo = QComboBox()
        self.alignment_combo.addItems(
            ["Left", "Center", "Right"]
        )

        self.text_edit.textChanged.connect(
            self.auto_apply_properties
        )
        self.x_spin.valueChanged.connect(
            self.auto_apply_properties
        )
        self.y_spin.valueChanged.connect(
            self.auto_apply_properties
        )
        self.width_spin.valueChanged.connect(
            self.auto_apply_properties
        )
        self.font_spin.valueChanged.connect(
            self.auto_apply_properties
        )
        self.font_combo.currentTextChanged.connect(
            self.auto_apply_properties
        )
        self.alignment_combo.currentTextChanged.connect(
            self.auto_apply_properties
        )

        color_button = QPushButton("Choose Text Color")
        color_button.clicked.connect(self.choose_text_color)

        property_layout.addRow("Text", self.text_edit)
        property_layout.addRow("X", self.x_spin)
        property_layout.addRow("Y", self.y_spin)
        property_layout.addRow("Width", self.width_spin)
        property_layout.addRow("Font Family", self.font_combo)
        property_layout.addRow("Font Size", self.font_spin)
        property_layout.addRow("Alignment", self.alignment_combo)
        property_layout.addRow(color_button)

        delete_button = QPushButton("🗑 Delete Selected")
        delete_button.clicked.connect(self.delete_selected)

        property_container = QWidget()
        property_container_layout = QVBoxLayout(property_container)
        property_container_layout.setContentsMargins(0, 0, 0, 0)
        property_container_layout.setSpacing(4)
        property_container_layout.addWidget(property_group)
        property_container_layout.addWidget(delete_button)

        sidebar_layout.addWidget(
            CollapsibleSection(
                "Selected Object",
                property_container,
                expanded=True,
            )
        )

        sidebar_layout.addStretch()

        save_button = QPushButton("💾 Save Layout")
        close_button = QPushButton("Close")

        save_button.clicked.connect(self.save_layout)
        close_button.clicked.connect(self.accept)

        sidebar_layout.addWidget(save_button)
        sidebar_layout.addWidget(close_button)

        sidebar_scroll = QScrollArea()
        sidebar_scroll.setObjectName("sidebarScroll")
        sidebar_scroll.setWidgetResizable(True)
        sidebar_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        sidebar_scroll.setWidget(sidebar)
        sidebar_scroll.setMinimumWidth(315)
        sidebar_scroll.setMaximumWidth(370)

        # -----------------------------------------------------
        # Canvas
        # -----------------------------------------------------
        self.scene = QGraphicsScene(
            0,
            0,
            CANVAS_WIDTH,
            CANVAS_HEIGHT,
        )

        self.view = QGraphicsView(self.scene)

        # PRESERVED from original editor:
        self.view.setDragMode(
            QGraphicsView.DragMode.RubberBandDrag
        )

        self.view.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.view.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.view.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        self.scene.selectionChanged.connect(
            self.update_properties
        )

        root.addWidget(sidebar_scroll, 0)
        root.addWidget(self.view, 1)

    # ---------------------------------------------------------
    # Theme
    # ---------------------------------------------------------

    def apply_theme(self):
        if self.theme == "light":
            self.setStyleSheet("""
                QDialog { background:#F3F5F7; color:#20252B; }
                QScrollArea#sidebarScroll { background:#F3F5F7; border:none; }
                QScrollArea#sidebarScroll > QWidget > QWidget#editorSidebar { background:#F3F5F7; }
                QScrollArea#sidebarScroll QWidget { background:#F3F5F7; }
                QLabel { color:#20252B; }

                QGroupBox {
                    color:#20252B;
                    border:1px solid #C7CDD4;
                    border-radius:7px;
                    margin-top:0px;
                    padding:10px;
                }

                QGroupBox::title {
                    subcontrol-origin:margin;
                    left:10px;
                    padding:0 5px;
                }

                QWidget#collapsibleSection {
                    background:#F3F5F7;
                    border:1px solid #C7CDD4;
                    border-radius:7px;
                }

                QWidget#collapsibleSection QPushButton#collapseButton {
                    background:#F3F5F7;
                    color:#20252B;
                    border:none;
                    border-radius:6px;
                    text-align:left;
                    padding:5px 8px;
                    margin:0px;
                }

                QGroupBox#sectionContent {
                    background:#F3F5F7;
                    border:none;
                    border-radius:0px;
                    margin:0px;
                    padding:6px 10px 10px 10px;
                }

                QListWidget {
                    background:white;
                    color:#20252B;
                    border:1px solid #BFC6CE;
                    border-radius:5px;
                }

                QListWidget::item:selected {
                    background:#DDE3E9;
                    color:#20252B;
                }

                QPushButton {
                    background:#E9EDF2;
                    color:#20252B;
                    border:1px solid #C5CBD2;
                    border-radius:6px;
                    padding:8px 12px;
                }

                QPushButton:hover {
                    background:#DDE3E9;
                }

                QLineEdit,QSpinBox,QComboBox {
                    background:white;
                    color:#20252B;
                    border:1px solid #BFC6CE;
                    border-radius:5px;
                    padding:6px;
                }

                QGraphicsView {
                    background:#D9DDE2;
                    border:1px solid #B9C0C8;
                    border-radius:6px;
                }
            """)
        else:
            self.setStyleSheet("""
                QDialog { background:#11171E; color:#F5F7FA; }
                QScrollArea#sidebarScroll { background:#11171E; border:none; }
                QScrollArea#sidebarScroll > QWidget > QWidget#editorSidebar { background:#11171E; }
                QScrollArea#sidebarScroll QWidget { background:#11171E; }
                QLabel { color:#F5F7FA; }

                QGroupBox {
                    color:#F5F7FA;
                    border:1px solid #303B47;
                    border-radius:7px;
                    margin-top:0px;
                    padding:10px;
                }

                QGroupBox::title {
                    subcontrol-origin:margin;
                    left:10px;
                    padding:0 5px;
                }

                QWidget#collapsibleSection {
                    background:#11171E;
                    border:1px solid #303B47;
                    border-radius:7px;
                }

                QWidget#collapsibleSection QPushButton#collapseButton {
                    background:#11171E;
                    color:#F5F7FA;
                    border:none;
                    border-radius:6px;
                    text-align:left;
                    padding:5px 8px;
                    margin:0px;
                }

                QGroupBox#sectionContent {
                    background:#11171E;
                    border:none;
                    border-radius:0px;
                    margin:0px;
                    padding:6px 10px 10px 10px;
                }

                QListWidget {
                    background:#18212B;
                    color:#F5F7FA;
                    border:1px solid #3D4C5B;
                    border-radius:5px;
                }

                QListWidget::item:selected {
                    background:#303C49;
                    color:#FFFFFF;
                }

                QPushButton {
                    background:#242E39;
                    color:#F5F7FA;
                    border:1px solid #40505F;
                    border-radius:6px;
                    padding:8px 12px;
                }

                QPushButton:hover {
                    background:#303C49;
                }

                QLineEdit,QSpinBox,QComboBox {
                    background:#18212B;
                    color:#F5F7FA;
                    border:1px solid #3D4C5B;
                    border-radius:5px;
                    padding:6px;
                }

                QGraphicsView {
                    background:#29323B;
                    border:1px solid #3D4C5B;
                    border-radius:6px;
                }
            """)

    # ---------------------------------------------------------
    # Messages
    # ---------------------------------------------------------

    def normalize_messages(self):
        normalized = []

        for message in self.messages:
            if not isinstance(message, dict):
                continue

            normalized.append({
                "name": str(message.get("name", "New Message")),
                "trigger_seconds": int(
                    message.get("trigger_seconds", 0)
                ),
                "message": str(
                    message.get("message", "")
                ),
                "color": str(
                    message.get("color", "#FFFFFF")
                ),
                "beep": bool(message.get("beep", False)),
                "beep_seconds": int(
                    message.get("beep_seconds", 0)
                ),
            })

        self.messages[:] = normalized

    def select_message_from_combo(self, index):
        if self._loading or index < 0:
            return

        name = self.message_combo.itemData(index)
        if not name:
            return

        self.set_message_visibility(name)

        item = self.get_message_object(name)
        if item is None:
            item = self.create_message_object(name, select=True)
            self.save_layout(silent=True)
            return

        self.scene.clearSelection()
        item.setVisible(True)
        item.setSelected(True)
        self.view.ensureVisible(item)
        self.update_properties()

    def refresh_message_list(self, select_name=None):
        self.normalize_messages()

        self.message_combo.blockSignals(True)
        self.message_combo.clear()

        selected_index = -1

        for index, message in enumerate(self.messages):
            name = message["name"]

            if name == "__DEFAULT__":
                label = f"DEFAULT  •  {message['message']}"
            else:
                label = (
                    f"{name}  •  "
                    f"{message['trigger_seconds']}s"
                )

            self.message_combo.addItem(label, name)

            if select_name == name:
                selected_index = index

        self.message_combo.blockSignals(False)

        if selected_index >= 0:
            self.message_combo.setCurrentIndex(selected_index)

    def get_message_by_name(self, name):
        return next(
            (
                message
                for message in self.messages
                if message.get("name") == name
            ),
            None,
        )

    def get_message_object(self, message_name):
        for item in self.scene.items():
            if (
                isinstance(item, EditableTextItem)
                and item.dynamic
                and item.message_name == message_name
            ):
                return item
        return None

    def set_message_visibility(self, selected_name):
        """Show only the selected dynamic message on the editor canvas.

        Timer and normal/static text objects stay visible. This lets the
        user position every message independently without all message
        strings piling up on top of each other.
        """
        for item in self.scene.items():
            if not isinstance(item, EditableTextItem):
                continue
            if not item.dynamic:
                continue

            item.setVisible(
                bool(selected_name)
                and item.message_name == selected_name
            )

    def current_message_name(self):
        if not hasattr(self, "message_combo"):
            return None
        index = self.message_combo.currentIndex()
        if index < 0:
            return None
        return self.message_combo.itemData(index)

    def add_message(self):
        dialog = EditorMessageDialog(
            parent=self,
            theme=self.theme,
        )

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        message = dialog.get_message()

        if self.get_message_by_name(message["name"]):
            QMessageBox.warning(
                self,
                "TPX",
                "A message with this name already exists.",
            )
            return

        self.messages.append(message)

        # Every new message automatically gets its own canvas object.
        self.create_message_object(
            message["name"],
            select=True,
        )

        self.refresh_message_list(message["name"])
        self.notify_messages_changed()
        self.save_layout(silent=True)

    def edit_message(self):
        old_name = self.current_message_name()

        if not old_name:
            return
        message = self.get_message_by_name(old_name)

        if message is None:
            return

        dialog = EditorMessageDialog(
            message,
            self,
            self.theme,
        )

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        edited = dialog.get_message()

        # Keep default message identity fixed.
        if old_name == "__DEFAULT__":
            edited["name"] = "__DEFAULT__"
            edited["trigger_seconds"] = -1

        elif (
            edited["name"] != old_name
            and self.get_message_by_name(edited["name"])
        ):
            QMessageBox.warning(
                self,
                "TPX",
                "A message with that name already exists.",
            )
            return

        index = self.messages.index(message)
        self.messages[index] = edited

        # Rename the canvas object together with the message.
        if edited["name"] != old_name:
            obj = self.get_message_object(old_name)
            if obj:
                obj.message_name = edited["name"]

        # Update text/color immediately.
        obj = self.get_message_object(edited["name"])
        if obj:
            obj.setPlainText(edited["message"])
            obj.setDefaultTextColor(
                QColor(edited["color"])
            )
            obj.update()

        self.refresh_message_list(edited["name"])
        self.notify_messages_changed()
        self.save_layout(silent=True)

    def delete_message(self):
        name = self.current_message_name()

        if not name:
            return

        if name == "__DEFAULT__":
            QMessageBox.information(
                self,
                "TPX",
                "Default Message cannot be deleted.",
            )
            return

        message = self.get_message_by_name(name)

        if message is None:
            return

        answer = QMessageBox.question(
            self,
            "Delete Message",
            (
                f"Delete message '{name}'?\n\n"
                "Its message object will also be removed from the canvas."
            ),
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        self.messages.remove(message)

        obj = self.get_message_object(name)
        if obj:
            self.scene.removeItem(obj)

        self.refresh_message_list()
        self.notify_messages_changed()
        self.save_layout(silent=True)

    def add_selected_message_to_canvas(self):
        name = self.current_message_name()

        if not name:
            return

        if self.get_message_object(name):
            obj = self.get_message_object(name)
            self.scene.clearSelection()
            obj.setSelected(True)
            self.view.ensureVisible(obj)
            return

        self.create_message_object(name, select=True)
        self.save_layout(silent=True)

    def create_message_object(self, message_name, select=False):
        message = self.get_message_by_name(message_name)

        if message is None:
            return None

        existing = self.get_message_object(message_name)
        if existing:
            return existing

        # Find a reasonable free position. The user can then drag it
        # anywhere they want.
        existing_dynamic = [
            item
            for item in self.scene.items()
            if (
                isinstance(item, EditableTextItem)
                and item.dynamic
            )
        ]

        offset = len(existing_dynamic) * 30

        item = EditableTextItem(
            message.get("message", "NEW MESSAGE"),
            "text",
            message_name=message_name,
            dynamic=True,
        )

        item.setPos(
            290 + (offset % 180),
            390 + (offset % 120),
        )
        item.setTextWidth(700)

        font = item.font()
        font.setPointSize(35)
        font.setBold(True)
        item.setFont(font)

        item.setDefaultTextColor(
            QColor(message.get("color", "#FFFFFF"))
        )

        option = QTextOption()
        option.setAlignment(Qt.AlignmentFlag.AlignCenter)
        item.document().setDefaultTextOption(option)

        self.scene.addItem(item)

        if select:
            self.scene.clearSelection()
            self.set_message_visibility(message_name)
            item.setVisible(True)
            item.setSelected(True)
            self.view.ensureVisible(item)

        return item

    def notify_messages_changed(self):
        if callable(self.on_messages_changed):
            self.on_messages_changed(self.messages)

    # ---------------------------------------------------------
    # Background
    # ---------------------------------------------------------

    def ensure_background(self):
        if self.background_item is None:
            self.background_item = BackgroundItem()
            self.scene.addItem(self.background_item)

    def choose_background_color(self):
        self.ensure_background()

        color = QColorDialog.getColor(
            self.background_item.brush().color(),
            self,
            "Background Color",
        )

        if not color.isValid():
            return

        self.background_item.setBrush(QBrush(color))
        self.background_image_path = ""

        if self.background_pixmap:
            self.scene.removeItem(self.background_pixmap)
            self.background_pixmap = None

        self.save_layout(silent=True)

    def choose_background_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Background Image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.webp)",
        )

        if not path:
            return

        image = QImage(path)

        if image.isNull():
            QMessageBox.warning(
                self,
                "TPX",
                "Unable to load image.",
            )
            return

        self.ensure_background()

        if self.background_pixmap:
            self.scene.removeItem(
                self.background_pixmap
            )

        pixmap = QPixmap.fromImage(image).scaled(
            CANVAS_WIDTH,
            CANVAS_HEIGHT,
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        self.background_pixmap = QGraphicsPixmapItem(pixmap)
        self.background_pixmap.setPos(0, 0)
        self.background_pixmap.setZValue(-999)
        self.scene.addItem(self.background_pixmap)

        self.background_image_path = path
        self.save_layout(silent=True)

    # ---------------------------------------------------------
    # Objects
    # ---------------------------------------------------------

    def add_timer(self):
        timer = EditableTextItem(
            "00:05:00",
            "timer",
        )

        timer.setPos(350, 230)
        timer.setTextWidth(600)

        font = timer.font()
        font.setPointSize(100)
        font.setBold(True)
        timer.setFont(font)

        timer.setDefaultTextColor(
            QColor("#FFD21F")
        )

        option = QTextOption()
        option.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        timer.document().setDefaultTextOption(option)

        self.scene.addItem(timer)
        timer.setSelected(True)

        self.update_properties()
        self.save_layout(silent=True)

    def add_text(self):
        item = EditableTextItem(
            "New Text",
            "text",
            dynamic=False,
        )

        item.setPos(400, 400)
        item.setTextWidth(500)

        self.scene.addItem(item)
        item.setSelected(True)

        self.update_properties()
        self.save_layout(silent=True)

    def selected_item(self):
        # QGraphicsScene can emit selectionChanged while/after items
        # are being destroyed (especially during scene.clear()).
        try:
            scene = self.scene
            selected = scene.selectedItems()
        except (RuntimeError, AttributeError):
            return None

        if not selected:
            return None

        try:
            item = selected[0]

            if (
                item is self.background_item
                or item is self.background_pixmap
            ):
                return None

            return item
        except RuntimeError:
            return None

    # ---------------------------------------------------------
    # Properties
    # ---------------------------------------------------------

    def update_properties(self):
        try:
            item = self.selected_item()

            if item is None or not isinstance(
                item,
                QGraphicsTextItem,
            ):
                return

            widgets = (
                self.text_edit,
                self.x_spin,
                self.y_spin,
                self.width_spin,
                self.font_spin,
                self.font_combo,
                self.alignment_combo,
            )

            for widget in widgets:
                widget.blockSignals(True)

            try:
                self.text_edit.setText(item.toPlainText())
                self.x_spin.setValue(int(item.x()))
                self.y_spin.setValue(int(item.y()))
                self.width_spin.setValue(
                    max(20, int(item.textWidth()))
                )
                self.font_spin.setValue(
                    max(8, item.font().pointSize())
                )

                family = item.font().family()
                family_index = self.font_combo.findText(family)
                if family_index >= 0:
                    self.font_combo.setCurrentIndex(family_index)

                alignment = (
                    item.document()
                    .defaultTextOption()
                    .alignment()
                )

                if alignment & Qt.AlignmentFlag.AlignCenter:
                    self.alignment_combo.setCurrentText("Center")
                elif alignment & Qt.AlignmentFlag.AlignRight:
                    self.alignment_combo.setCurrentText("Right")
                else:
                    self.alignment_combo.setCurrentText("Left")
            finally:
                for widget in widgets:
                    widget.blockSignals(False)

        except RuntimeError:
            # Qt can deliver a late selectionChanged signal after the
            # underlying C++ graphics object has already been destroyed.
            return

    def auto_apply_properties(self):
        if self._loading:
            return

        item = self.selected_item()

        if item is None or not isinstance(
            item,
            QGraphicsTextItem,
        ):
            return

        if item.toPlainText() != self.text_edit.text():
            item.setPlainText(
                self.text_edit.text()
            )

        item.setPos(
            self.x_spin.value(),
            self.y_spin.value(),
        )

        item.setTextWidth(
            self.width_spin.value()
        )

        font = item.font()
        font.setFamily(self.font_combo.currentText())
        font.setPointSize(
            self.font_spin.value()
        )
        item.setFont(font)

        option = QTextOption()
        alignment = (
            self.alignment_combo.currentText()
        )

        if alignment == "Center":
            option.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )
        elif alignment == "Right":
            option.setAlignment(
                Qt.AlignmentFlag.AlignRight
            )
        else:
            option.setAlignment(
                Qt.AlignmentFlag.AlignLeft
            )

        item.document().setDefaultTextOption(
            option
        )

        # If this is a message object, keep the
        # message's actual content/color synchronized.
        if (
            isinstance(item, EditableTextItem)
            and item.dynamic
            and item.message_name
        ):
            message = self.get_message_by_name(
                item.message_name
            )

            if message:
                message["message"] = (
                    item.toPlainText()
                )
                message["color"] = (
                    item.defaultTextColor().name()
                )

                self.refresh_message_list(
                    item.message_name
                )
                self.notify_messages_changed()

        item.update()
        self.scene.update()

        self.save_layout(silent=True)

    def choose_text_color(self):
        item = self.selected_item()

        if item is None or not isinstance(
            item,
            QGraphicsTextItem,
        ):
            return

        color = QColorDialog.getColor(
            item.defaultTextColor(),
            self,
            "Text Color",
        )

        if not color.isValid():
            return

        item.setDefaultTextColor(color)
        item.update()

        if (
            isinstance(item, EditableTextItem)
            and item.dynamic
            and item.message_name
        ):
            message = self.get_message_by_name(
                item.message_name
            )

            if message:
                message["color"] = color.name()
                self.notify_messages_changed()
                self.refresh_message_list(
                    item.message_name
                )

        self.save_layout(silent=True)

    def delete_selected(self):
        try:
            item = self.selected_item()
        except RuntimeError:
            return

        if item is None:
            return

        # Deleting a message canvas object does not delete the
        # message configuration. Re-selecting that message will
        # recreate its canvas object automatically.
        self.scene.removeItem(item)

        if (
            isinstance(item, EditableTextItem)
            and item.dynamic
            and item.message_name
        ):
            self.set_message_visibility(item.message_name)

        self.save_layout(silent=True)

    # ---------------------------------------------------------
    # Save / Load
    # ---------------------------------------------------------

    def save_layout(self, silent=False):
        self.ensure_background()

        objects = []

        for item in reversed(self.scene.items()):
            if (
                item is self.background_item
                or item is self.background_pixmap
            ):
                continue

            if not isinstance(
                item,
                QGraphicsTextItem,
            ):
                continue

            alignment_value = (
                item.document()
                .defaultTextOption()
                .alignment()
            )

            if alignment_value & Qt.AlignmentFlag.AlignCenter:
                alignment = "center"
            elif alignment_value & Qt.AlignmentFlag.AlignRight:
                alignment = "right"
            else:
                alignment = "left"

            object_data = {
                "type": getattr(
                    item,
                    "item_type",
                    "text",
                ),
                "text": item.toPlainText(),
                "x": item.x(),
                "y": item.y(),
                "width": item.textWidth(),
                "font_family": item.font().family(),
                "font_size": item.font().pointSize(),
                "bold": item.font().bold(),
                "color": item.defaultTextColor().name(),
                "alignment": alignment,
            }

            # New optional fields. Old layout files remain
            # compatible because these fields are only added.
            if (
                isinstance(item, EditableTextItem)
                and item.dynamic
            ):
                object_data["dynamic"] = True
                object_data["message_name"] = (
                    item.message_name
                )
            else:
                object_data["dynamic"] = False

            objects.append(object_data)

        background_color = (
            self.background_item
            .brush()
            .color()
            .name()
        )

        data = {
            "event": self.event_name,
            "canvas": {
                "width": CANVAS_WIDTH,
                "height": CANVAS_HEIGHT,
            },
            "background": {
                "color": background_color,
                "image": self.background_image_path,
            },
            "objects": objects,
        }

        path = get_layout_path(
            self.event_name
        )

        try:
            with open(
                path,
                "w",
                encoding="utf-8",
            ) as file:
                json.dump(
                    data,
                    file,
                    indent=4,
                    ensure_ascii=False,
                )

            if not silent:
                box = QMessageBox(self)
                box.setIcon(QMessageBox.Icon.Information)
                box.setWindowTitle("TPX")
                box.setText("Layout saved successfully.")
                box.setStandardButtons(
                    QMessageBox.StandardButton.Ok
                )
                box.exec()

                # After the user confirms the successful save,
                # close the Visual Editor. Silent/automatic saves
                # never close the editor.
                self.accept()

        except OSError as error:
            if not silent:
                QMessageBox.critical(
                    self,
                    "TPX",
                    f"Unable to save layout:\n{error}",
                )

    def load_layout(self):
        path = get_layout_path(
            self.event_name
        )

        if not path.exists():
            self.create_default_layout()
            self.refresh_message_list()
            self.save_layout(silent=True)
            return

        try:
            with open(
                path,
                "r",
                encoding="utf-8",
            ) as file:
                data = json.load(file)
        except (
            OSError,
            json.JSONDecodeError,
        ):
            self.create_default_layout()
            self.refresh_message_list()
            self.save_layout(silent=True)
            return

        self._loading = True

        # QGraphicsScene.clear() destroys C++ graphics objects and can
        # emit selectionChanged during that process. Block the signal
        # until the scene is rebuilt.
        self.scene.blockSignals(True)
        try:
            self.scene.clear()
        finally:
            self.scene.blockSignals(False)

        self.background_item = None
        self.background_pixmap = None
        self.background_image_path = ""

        background = data.get(
            "background",
            {},
        )

        self.ensure_background()

        self.background_item.setBrush(
            QBrush(
                QColor(
                    background.get(
                        "color",
                        "#000000",
                    )
                )
            )
        )

        image_path = background.get(
            "image",
            "",
        )

        if image_path and os.path.exists(
            image_path
        ):
            image = QImage(image_path)

            if not image.isNull():
                pixmap = (
                    QPixmap.fromImage(image)
                    .scaled(
                        CANVAS_WIDTH,
                        CANVAS_HEIGHT,
                        Qt.AspectRatioMode.IgnoreAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )

                self.background_pixmap = (
                    QGraphicsPixmapItem(
                        pixmap
                    )
                )

                self.background_pixmap.setPos(
                    0,
                    0,
                )
                self.background_pixmap.setZValue(
                    -999
                )

                self.scene.addItem(
                    self.background_pixmap
                )

                self.background_image_path = (
                    image_path
                )

        raw_objects = data.get(
            "objects",
            [],
        )

        # Legacy migration:
        # Old editor files had no dynamic/message_name fields.
        # The first non-timer text becomes the message object.
        legacy_message_assigned = False

        non_default_messages = [
            m for m in self.messages
            if m.get("name") != "__DEFAULT__"
        ]

        for obj_index, obj in enumerate(
            raw_objects
        ):
            object_type = obj.get(
                "type",
                "text",
            )

            dynamic = bool(
                obj.get(
                    "dynamic",
                    False,
                )
            )

            message_name = str(
                obj.get(
                    "message_name",
                    "",
                )
            )

            # Migrate old layout:
            if (
                object_type != "timer"
                and not dynamic
                and not message_name
                and not legacy_message_assigned
            ):
                # Prefer a message whose configured text matches.
                configured_match = next(
                    (
                        m for m in self.messages
                        if (
                            m.get("message")
                            == obj.get("text", "")
                            and m.get("name")
                            != "__DEFAULT__"
                        )
                    ),
                    None,
                )

                if configured_match:
                    message_name = configured_match[
                        "name"
                    ]
                elif non_default_messages:
                    message_name = (
                        non_default_messages[0]
                        .get("name", "")
                    )

                if message_name:
                    dynamic = True
                    legacy_message_assigned = True

            item = EditableTextItem(
                obj.get(
                    "text",
                    "Text",
                ),
                object_type,
                message_name=message_name,
                dynamic=dynamic,
            )

            item.setPos(
                float(
                    obj.get(
                        "x",
                        100,
                    )
                ),
                float(
                    obj.get(
                        "y",
                        100,
                    )
                ),
            )

            item.setTextWidth(
                float(
                    obj.get(
                        "width",
                        500,
                    )
                )
            )

            font = item.font()
            font.setFamily(
                str(obj.get("font_family", font.family()))
            )
            font.setPointSize(
                int(
                    obj.get(
                        "font_size",
                        48,
                    )
                )
            )
            font.setBold(
                bool(
                    obj.get(
                        "bold",
                        False,
                    )
                )
            )
            item.setFont(font)

            item.setDefaultTextColor(
                QColor(
                    obj.get(
                        "color",
                        "#FFFFFF",
                    )
                )
            )

            option = QTextOption()
            alignment = obj.get(
                "alignment",
                "left",
            )

            if alignment == "center":
                option.setAlignment(
                    Qt.AlignmentFlag.AlignCenter
                )
            elif alignment == "right":
                option.setAlignment(
                    Qt.AlignmentFlag.AlignRight
                )
            else:
                option.setAlignment(
                    Qt.AlignmentFlag.AlignLeft
                )

            item.document().setDefaultTextOption(
                option
            )

            self.scene.addItem(item)

        self._loading = False

        self.ensure_message_objects()

        # Only one message is shown at a time in the editor.
        # Start with the first configured message so the canvas
        # is immediately usable and never shows stacked messages.
        first_message_name = None
        if self.messages:
            first_message_name = self.messages[0].get("name")

        if first_message_name:
            self.set_message_visibility(first_message_name)

        self.refresh_message_list(first_message_name)
        self.update_properties()

        # Save the migration once so old files gain the new
        # message_name/dynamic fields.
        self.save_layout(silent=True)

    def ensure_message_objects(self):
        """
        Make sure every configured message has a canvas object.
        This is what makes adding a message from the editor
        immediately positionable.
        """
        for message in self.messages:
            name = message.get("name", "")

            if not name:
                continue

            if not self.get_message_object(name):
                self.create_message_object(
                    name,
                    select=False,
                )

    def create_default_layout(self):
        self.ensure_background()

        self.background_item.setBrush(
            QBrush(QColor("#000000"))
        )

        timer = EditableTextItem(
            "00:05:00",
            "timer",
        )

        timer.setPos(
            330,
            240,
        )
        timer.setTextWidth(
            620
        )

        font = timer.font()
        font.setPointSize(
            100
        )
        font.setBold(
            True
        )
        timer.setFont(font)

        timer.setDefaultTextColor(
            QColor("#FFD21F")
        )

        option = QTextOption()
        option.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        timer.document().setDefaultTextOption(
            option
        )

        self.scene.addItem(
            timer
        )

        # Prefer the existing 5-minute message for the
        # initial message object, matching the old TPX design.
        target_message = next(
            (
                m for m in self.messages
                if m.get("name")
                == "5 Minutes Left"
            ),
            None,
        )

        if target_message is None:
            target_message = next(
                (
                    m for m in self.messages
                    if m.get("name")
                    != "__DEFAULT__"
                ),
                None,
            )

        if target_message:
            message = EditableTextItem(
                target_message.get(
                    "message",
                    "PLEASE PREPARE TO WRAP UP YOUR TALK.",
                ),
                "text",
                message_name=target_message.get(
                    "name",
                    "",
                ),
                dynamic=True,
            )
            message.setPos(
                290,
                390,
            )
            message.setTextWidth(
                700
            )

            font = message.font()
            font.setPointSize(
                35
            )
            font.setBold(
                True
            )
            message.setFont(
                font
            )

            message.setDefaultTextColor(
                QColor(
                    target_message.get(
                        "color",
                        "#FFD21F",
                    )
                )
            )

            option = QTextOption()
            option.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )
            message.document().setDefaultTextOption(
                option
            )

            self.scene.addItem(
                message
            )

        self.ensure_message_objects()

        first_message = next(
            (
                m for m in self.messages
                if m.get("name") != "__DEFAULT__"
            ),
            None,
        )
        if first_message:
            self.set_message_visibility(
                first_message.get("name")
            )

    def closeEvent(self, event):
        self.save_layout(
            silent=True
        )
        self.notify_messages_changed()
        event.accept()


if __name__ == "__main__":
    app = QApplication([])
    editor = VisualEditor(
        "Test Event",
        theme="dark",
        messages=[],
    )
    editor.show()
    app.exec()
