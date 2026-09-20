import sys
import os
import json
import threading
import time
from pathlib import Path
from dataclasses import dataclass

if sys.platform == "win32":
    try:
        import ctypes
    except ImportError:
        ctypes = None
else:
    ctypes = None

from storage import save_events, load_events
from editor import VisualEditor, CANVAS_WIDTH, CANVAS_HEIGHT

from PySide6.QtCore import Qt, QTimer, QEventLoop
from PySide6.QtGui import (
    QColor,
    QFont,
    QIcon,
    QBrush,
    QPixmap,
    QImage,
    QTextOption,
)
from PySide6.QtWidgets import (
    QApplication,
    QSplashScreen,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QInputDialog,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
    QColorDialog,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsTextItem,
    QGraphicsPixmapItem,
)

try:
    import winsound
except ImportError:
    winsound = None


APP_NAME = "TPX"
APP_DISPLAY_NAME = "TPX — Timer Pro X"


def resource_path(*parts):
    if getattr(sys, "frozen", False):
        base = getattr(
            sys,
            "_MEIPASS",
            os.path.dirname(sys.executable),
        )
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, *parts)


def set_windows_app_id():
    if sys.platform != "win32" or ctypes is None:
        return

    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "TPX.TimerProX"
        )
    except Exception:
        pass


@dataclass
class TimerMessage:
    name: str
    trigger_seconds: int
    message: str
    color: str
    beep: bool = False
    beep_seconds: int = 0


DEFAULT_MESSAGES = [
    TimerMessage(
        "__DEFAULT__", -1, "Time Remaining",
        "#FFFFFF", False, 0
    ),
    TimerMessage(
        "5 Minutes Left", 300,
        "PLEASE PREPARE TO WRAP UP YOUR TALK.",
        "#FFD21F", True, 5
    ),
    TimerMessage(
        "3 Minutes Left", 180,
        "YOU HAVE 3 MINUTES LEFT.",
        "#FFA500", True, 5
    ),
    TimerMessage(
        "2 Minutes Left", 120,
        "PLEASE WRAP UP YOUR TALK.",
        "#FF7043", True, 5
    ),
    TimerMessage(
        "Time's Up", 0,
        "THANK YOU, UP NEXT.",
        "#FF3B30", True, 5
    ),
]


def beep_sequence(seconds):
    if winsound is None:
        return

    def worker():
        for _ in range(max(0, seconds)):
            try:
                winsound.Beep(1000, 350)
            except Exception:
                pass
            time.sleep(1)

    threading.Thread(target=worker, daemon=True).start()


class MessageEditorDialog(QDialog):
    def __init__(self, message=None, parent=None, theme="dark"):
        super().__init__(parent)
        self.theme = theme
        self.setWindowTitle("Timer Message")
        self.resize(580, 350)

        if message is None:
            message = TimerMessage(
                "New Message", 0, "", "#FFFFFF", False, 0
            )

        self.message = message

        self.name_edit = QLineEdit(message.name)
        self.trigger_spin = QSpinBox()
        self.trigger_spin.setRange(-1, 86400)
        self.trigger_spin.setValue(message.trigger_seconds)

        self.message_edit = QLineEdit(message.message)
        self.color_edit = QLineEdit(message.color)

        self.beep_check = QCheckBox("Enable Beep")
        self.beep_check.setChecked(message.beep)

        self.beep_seconds = QSpinBox()
        self.beep_seconds.setRange(1, 60)
        self.beep_seconds.setValue(max(1, message.beep_seconds or 5))

        color_button = QPushButton("Choose Color")
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
                QLabel { color:#20252B; }
                QCheckBox { color:#20252B; }
                QLineEdit,QSpinBox {
                    background:white;
                    color:#20252B;
                    border:1px solid #BFC6CE;
                    padding:7px;
                }
                QPushButton {
                    background:#E9EDF2;
                    color:#20252B;
                    padding:8px;
                }
            """)
        else:
            self.setStyleSheet("""
                QDialog { background:#11171E; }
                QLabel,QCheckBox { color:white; }
                QLineEdit,QSpinBox {
                    background:#18212B;
                    color:white;
                    border:1px solid #3D4C5B;
                    padding:7px;
                }
                QPushButton {
                    background:#242E39;
                    color:white;
                    padding:8px;
                }
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
        name = self.name_edit.text().strip() or "New Message"
        return TimerMessage(
            name,
            self.trigger_spin.value(),
            self.message_edit.text(),
            self.color_edit.text().strip() or "#FFFFFF",
            self.beep_check.isChecked(),
            self.beep_seconds.value(),
        )


class MessageSettingsDialog(QDialog):
    def __init__(self, messages, parent=None, theme="dark"):
        super().__init__(parent)
        self.messages = messages
        self.theme = theme
        self.setWindowTitle("Message Settings")
        self.resize(720, 520)

        self.list = QListWidget()
        self.refresh()

        add_button = QPushButton("＋ Add")
        edit_button = QPushButton("✎ Edit")
        delete_button = QPushButton("🗑 Delete")
        default_button = QPushButton("Default Message")

        add_button.clicked.connect(self.add_message)
        edit_button.clicked.connect(self.edit_message)
        delete_button.clicked.connect(self.delete_message)
        default_button.clicked.connect(self.edit_default)

        buttons = QHBoxLayout()
        buttons.addWidget(add_button)
        buttons.addWidget(edit_button)
        buttons.addWidget(delete_button)
        buttons.addWidget(default_button)

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        buttons.addWidget(close_button)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Messages for this event"))
        layout.addWidget(self.list)
        layout.addLayout(buttons)

        self.apply_theme()

    def apply_theme(self):
        if self.theme == "light":
            self.setStyleSheet("""
                QDialog { background:#F3F5F7; }
                QLabel { color:#20252B; }
                QListWidget {
                    background:white;
                    color:#20252B;
                    border:1px solid #C7CDD4;
                }
                QPushButton {
                    background:#E9EDF2;
                    color:#20252B;
                    border:1px solid #C5CBD2;
                    padding:8px;
                }
            """)
        else:
            self.setStyleSheet("""
                QDialog { background:#11171E; }
                QLabel { color:white; }
                QListWidget {
                    background:#18212B;
                    color:white;
                    border:1px solid #3D4C5B;
                }
                QPushButton {
                    background:#242E39;
                    color:white;
                    border:1px solid #40505F;
                    padding:8px;
                }
            """)

    def refresh(self):
        self.list.clear()
        for message in self.messages:
            if message.name == "__DEFAULT__":
                text = f"DEFAULT  |  {message.message}"
            else:
                text = (
                    f"{message.name}  |  "
                    f"{message.trigger_seconds}s  |  "
                    f"{message.message}"
                )

            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, message)
            self.list.addItem(item)

    def add_message(self):
        dialog = MessageEditorDialog(parent=self, theme=self.theme)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        self.messages.append(dialog.get_message())
        self.refresh()
        self.parent().message_settings_changed()

    def edit_message(self):
        item = self.list.currentItem()
        if item is None:
            return

        message = item.data(Qt.ItemDataRole.UserRole)

        if message.name == "__DEFAULT__":
            self.edit_default()
            return

        dialog = MessageEditorDialog(message, self, self.theme)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        index = self.messages.index(message)
        self.messages[index] = dialog.get_message()
        self.refresh()
        self.parent().message_settings_changed()

    def edit_default(self):
        default = next(
            (m for m in self.messages if m.name == "__DEFAULT__"),
            None,
        )

        if default is None:
            default = TimerMessage(
                "__DEFAULT__", -1, "Time Remaining",
                "#FFFFFF", False, 0
            )
            self.messages.insert(0, default)

        dialog = MessageEditorDialog(default, self, self.theme)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        edited = dialog.get_message()
        edited.name = "__DEFAULT__"
        edited.trigger_seconds = -1

        index = self.messages.index(default)
        self.messages[index] = edited
        self.refresh()
        self.parent().message_settings_changed()

    def delete_message(self):
        item = self.list.currentItem()
        if item is None:
            return

        message = item.data(Qt.ItemDataRole.UserRole)

        if message.name == "__DEFAULT__":
            QMessageBox.information(
                self,
                "TPX",
                "Default Message cannot be deleted.",
            )
            return

        answer = QMessageBox.question(
            self,
            "Delete Message",
            "Delete this message?",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        self.messages.remove(message)
        self.refresh()
        self.parent().message_settings_changed()


class DisplayWindow(QWidget):
    CANVAS_WIDTH = CANVAS_WIDTH
    CANVAS_HEIGHT = CANVAS_HEIGHT

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("TPX — Output Display")
        self.theme = "dark"

        self.scene = QGraphicsScene(
            0, 0, self.CANVAS_WIDTH, self.CANVAS_HEIGHT
        )

        self.view = QGraphicsView(self.scene, self)
        self.view.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.view.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.view.setFrameShape(QGraphicsView.Shape.NoFrame)
        self.view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.view.setInteractive(False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.view)

        self.timer_items = []
        self.text_items = []
        self.message_items = {}
        self.dynamic_message_item = None

        self.background_pixmap = None
        self.layout_loaded = False
        self.current_layout_path = None

        self.current_timer_text = "00:00:00"
        self.current_message_text = ""

    def configure(
        self,
        theme,
        timer_color=None,
        message_color=None,
        use_theme_colors=True,
        timer_size=None,
        message_size=None,
    ):
        self.theme = theme

        # Editor is the presentation source of truth.
        # Display Settings does not overwrite editor object
        # positions, sizes, fonts, or colors.
        if theme == "light":
            self.setStyleSheet("QWidget { background:#F4F6F8; }")
        else:
            self.setStyleSheet("QWidget { background:#000000; }")

        self.fit_scene()

    def get_layout_path(self, event_name):
        public_dir = os.environ.get("PUBLIC")
        if public_dir:
            folder = (
                Path(public_dir)
                / "Documents"
                / "TPX"
                / "layouts"
            )
        else:
            folder = (
                Path.home()
                / "Documents"
                / "TPX"
                / "layouts"
            )

        folder.mkdir(parents=True, exist_ok=True)

        safe_name = "".join(
            c if c.isalnum() or c in " _-" else "_"
            for c in event_name
        ).strip()

        if not safe_name:
            safe_name = "Untitled Event"

        return folder / f"{safe_name}.json"

    def load_event_layout(self, event_name):
        path = self.get_layout_path(event_name)
        self.current_layout_path = path

        self.scene.clear()
        self.timer_items = []
        self.text_items = []
        self.message_items = {}
        self.dynamic_message_item = None
        self.background_pixmap = None
        self.layout_loaded = False

        if not path.exists():
            self.create_fallback_layout()
            self.fit_scene()
            return

        try:
            with open(path, "r", encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, json.JSONDecodeError):
            self.create_fallback_layout()
            self.fit_scene()
            return

        canvas = data.get("canvas", {})
        # Keep the master coordinate system from the editor.
        # Old files without canvas metadata remain 1280x720.
        source_width = int(canvas.get("width", CANVAS_WIDTH))
        source_height = int(canvas.get("height", CANVAS_HEIGHT))

        self.scene.setSceneRect(
            0, 0, CANVAS_WIDTH, CANVAS_HEIGHT
        )

        background = data.get("background", {})
        background_color = background.get("color", "#000000")

        self.scene.setBackgroundBrush(
            QBrush(QColor(background_color))
        )

        image_path = background.get("image", "")
        if image_path and os.path.exists(image_path):
            image = QImage(image_path)
            if not image.isNull():
                pixmap = QPixmap.fromImage(image).scaled(
                    CANVAS_WIDTH,
                    CANVAS_HEIGHT,
                    Qt.AspectRatioMode.IgnoreAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )

                self.background_pixmap = QGraphicsPixmapItem(pixmap)
                self.background_pixmap.setPos(0, 0)
                self.background_pixmap.setZValue(-1000)
                self.scene.addItem(self.background_pixmap)

        objects = data.get("objects", [])

        # Existing layouts: first non-timer text is the dynamic
        # message object. New layouts use the same convention.
        first_text = None

        for obj in objects:
            object_type = obj.get("type", "text")

            x = float(obj.get("x", 0))
            y = float(obj.get("y", 0))
            width = float(obj.get("width", 500))
            font_size = int(obj.get("font_size", 48))
            color = obj.get("color", "#FFFFFF")
            bold = bool(obj.get("bold", False))
            alignment = obj.get("alignment", "left")
            text = obj.get("text", "")

            # If an old layout was saved using another canvas size,
            # normalize its coordinates into the editor's master
            # 1280x720 space instead of changing the visual design.
            if source_width != CANVAS_WIDTH:
                x *= CANVAS_WIDTH / source_width
                width *= CANVAS_WIDTH / source_width

            if source_height != CANVAS_HEIGHT:
                y *= CANVAS_HEIGHT / source_height

            item = QGraphicsTextItem(text)
            item.setPos(x, y)
            item.setTextWidth(width)

            font = QFont(
                str(obj.get("font_family", "Arial"))
            )
            font.setPointSize(font_size)
            font.setBold(bold)
            item.setFont(font)
            item.setDefaultTextColor(QColor(color))

            option = QTextOption()
            if alignment == "center":
                option.setAlignment(Qt.AlignmentFlag.AlignCenter)
            elif alignment == "right":
                option.setAlignment(Qt.AlignmentFlag.AlignRight)
            else:
                option.setAlignment(Qt.AlignmentFlag.AlignLeft)

            item.document().setDefaultTextOption(option)
            item.setZValue(10)

            if object_type == "timer":
                item.setData(0, "timer")
                self.timer_items.append(item)
            else:
                item.setData(0, "text")
                self.text_items.append(item)

                is_dynamic = bool(
                    obj.get("dynamic", False)
                )
                message_name = str(
                    obj.get("message_name", "")
                )

                # New layouts: every message object has its
                # own message_name.
                if is_dynamic and message_name:
                    self.message_items[message_name] = item

                # Legacy layouts: first non-timer text is the
                # dynamic message object.
                if first_text is None:
                    first_text = item

            self.scene.addItem(item)

        # If this is an old layout with no dynamic/message_name
        # fields, preserve the previous behavior.
        if not self.message_items and first_text is not None:
            self.dynamic_message_item = first_text

        self.layout_loaded = True
        self.fit_scene()

    def create_fallback_layout(self):
        self.scene.setBackgroundBrush(QBrush(QColor("#000000")))

        timer = QGraphicsTextItem("00:00:00")
        timer.setTextWidth(620)
        timer.setPos(330, 240)

        font = QFont("Arial")
        font.setPointSize(100)
        font.setBold(True)
        timer.setFont(font)
        timer.setDefaultTextColor(QColor("#FFD21F"))

        option = QTextOption()
        option.setAlignment(Qt.AlignmentFlag.AlignCenter)
        timer.document().setDefaultTextOption(option)

        self.scene.addItem(timer)
        self.timer_items.append(timer)

        message = QGraphicsTextItem("Time Remaining")
        message.setTextWidth(700)
        message.setPos(290, 390)

        font = QFont("Arial")
        font.setPointSize(35)
        font.setBold(True)
        message.setFont(font)
        message.setDefaultTextColor(QColor("#FFD21F"))

        option = QTextOption()
        option.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message.document().setDefaultTextOption(option)

        self.scene.addItem(message)
        self.text_items.append(message)
        self.dynamic_message_item = message

    def update_output(
        self,
        timer_text,
        message_text,
        message_color=None,
        message_name=None,
    ):
        self.current_timer_text = timer_text
        self.current_message_text = message_text

        for item in self.timer_items:
            item.setPlainText(timer_text)

        # New layout behavior:
        # only the selected/active message object is visible.
        if self.message_items:
            for name, item in self.message_items.items():
                item.setVisible(
                    name == message_name
                )

            active_item = self.message_items.get(
                message_name
            )

            if active_item is None:
                # Safety fallback if a message object is missing.
                active_item = self.message_items.get(
                    "__DEFAULT__"
                )

            if active_item is not None:
                active_item.setPlainText(message_text)

                if message_color:
                    active_item.setDefaultTextColor(
                        QColor(message_color)
                    )
        else:
            # Legacy layout behavior.
            if self.dynamic_message_item is not None:
                self.dynamic_message_item.setPlainText(
                    message_text
                )

                if message_color:
                    self.dynamic_message_item.setDefaultTextColor(
                        QColor(message_color)
                    )

        self.view.viewport().update()

    def fit_scene(self):
        self.view.fitInView(
            self.scene.sceneRect(),
            Qt.AspectRatioMode.KeepAspectRatio
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fit_scene()

    def move_to_screen(self, screen, fullscreen):
        if fullscreen:
            self.setWindowFlags(
                Qt.WindowType.FramelessWindowHint
                | Qt.WindowType.WindowStaysOnTopHint
            )
            self.setGeometry(screen.geometry())
            self.showFullScreen()
        else:
            self.setWindowFlags(Qt.WindowType.Window)
            self.resize(1280, 720)

            geometry = screen.geometry()
            self.move(
                geometry.x() + 50,
                geometry.y() + 50,
            )
            self.show()

        self.fit_scene()
        self.raise_()

    def closeEvent(self, event):
        self.hide()
        event.ignore()


class DisplaySettingsDialog(QDialog):
    def __init__(self, settings, theme, parent=None):
        super().__init__(parent)

        self.settings = settings
        self.theme = theme

        self.setWindowTitle("Display Settings")
        self.resize(650, 500)

        self.monitor_combo = QComboBox()

        screens = QApplication.screens()
        for index, screen in enumerate(screens):
            geometry = screen.geometry()
            self.monitor_combo.addItem(
                f"Monitor {index + 1} — "
                f"{geometry.width()} × {geometry.height()}",
                index,
            )

        self.monitor_combo.setCurrentIndex(
            min(
                settings.get("monitor", 0),
                max(0, len(screens) - 1),
            )
        )

        self.fullscreen_check = QCheckBox("Fullscreen Output")
        self.fullscreen_check.setChecked(
            settings.get("fullscreen", False)
        )

        self.use_theme_check = QCheckBox("Use Theme Font Colors")
        self.use_theme_check.setChecked(
            settings.get("use_theme_colors", True)
        )

        self.timer_color_edit = QLineEdit(
            settings.get("timer_color", "#FFFFFF")
        )
        self.message_color_edit = QLineEdit(
            settings.get("message_color", "#FFFFFF")
        )

        timer_color_button = QPushButton("Choose Timer Color")
        message_color_button = QPushButton("Choose Message Color")

        timer_color_button.clicked.connect(
            lambda: self.choose_color(self.timer_color_edit)
        )
        message_color_button.clicked.connect(
            lambda: self.choose_color(self.message_color_edit)
        )

        # Kept for compatibility with existing events/settings.
        self.timer_size = QSpinBox()
        self.timer_size.setRange(20, 300)
        self.timer_size.setValue(
            settings.get("timer_font_size", 100)
        )

        self.message_size = QSpinBox()
        self.message_size.setRange(10, 150)
        self.message_size.setValue(
            settings.get("message_font_size", 40)
        )

        form = QFormLayout()
        form.addRow("Monitor", self.monitor_combo)
        form.addRow("", self.fullscreen_check)
        form.addRow("", self.use_theme_check)
        form.addRow("Timer Font Size", self.timer_size)
        form.addRow("Message Font Size", self.message_size)
        form.addRow("Timer Color", self.timer_color_edit)
        form.addRow("", timer_color_button)
        form.addRow("Message Color", self.message_color_edit)
        form.addRow("", message_color_button)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.save)
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
                QLineEdit,QSpinBox,QComboBox {
                    background:white;
                    color:#20252B;
                    border:1px solid #BFC6CE;
                    padding:7px;
                }
                QPushButton {
                    background:#E9EDF2;
                    color:#20252B;
                    padding:8px;
                }
            """)
        else:
            self.setStyleSheet("""
                QDialog { background:#11171E; }
                QLabel,QCheckBox { color:white; }
                QLineEdit,QSpinBox,QComboBox {
                    background:#18212B;
                    color:white;
                    border:1px solid #3D4C5B;
                    padding:7px;
                }
                QPushButton {
                    background:#242E39;
                    color:white;
                    padding:8px;
                }
            """)

    def choose_color(self, target):
        color = QColorDialog.getColor(
            QColor(target.text()),
            self,
        )
        if color.isValid():
            target.setText(color.name())

    def save(self):
        self.settings["monitor"] = self.monitor_combo.currentData()
        self.settings["fullscreen"] = self.fullscreen_check.isChecked()
        self.settings["use_theme_colors"] = (
            self.use_theme_check.isChecked()
        )
        self.settings["timer_font_size"] = self.timer_size.value()
        self.settings["message_font_size"] = self.message_size.value()
        self.settings["timer_color"] = self.timer_color_edit.text()
        self.settings["message_color"] = self.message_color_edit.text()
        self.accept()


class CountdownApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(APP_DISPLAY_NAME)
        self.resize(1020, 700)

        icon_path = resource_path("assets", "tpx-icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.theme = "dark"
        self.time_left = 0
        self.running = False
        self.paused = False
        self.triggered = set()

        self.current_event_name = None
        self.messages = []

        self.editor_window = None
        self.display_window = None

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.countdown_tick)

        self.events = load_events()
        if not isinstance(self.events, list):
            self.events = []

        if not self.events:
            self.events = [self.create_default_event()]
            save_events(self.events)

        self.build_ui()
        self.refresh_event_combo()
        self.load_event(self.events[0]["name"])
        self.apply_theme()

    def create_default_event(self):
        return {
            "name": "RIEX",
            "messages": [
                self.message_to_dict(m)
                for m in DEFAULT_MESSAGES
            ],
            "display": {
                "monitor": 0,
                "fullscreen": False,
                "use_theme_colors": True,
                "timer_color": "#FFFFFF",
                "message_color": "#FFFFFF",
                "timer_font_size": 100,
                "message_font_size": 40,
            },
        }

    def build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(22, 18, 22, 12)
        root.setSpacing(12)

        header = QHBoxLayout()

        logo = QLabel()
        icon_path = resource_path("assets", "tpx-icon.png")
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path).scaled(
                46,
                46,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            logo.setPixmap(pixmap)
            logo.setFixedSize(50, 50)
        else:
            logo.setText("TPX")
            logo.setStyleSheet(
                "font-size:28px;font-weight:bold;color:#FFD21F;"
            )
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.addWidget(logo)

        title_layout = QVBoxLayout()

        title = QLabel("TPX — Timer Pro X")
        title.setStyleSheet("font-size:25px;font-weight:bold;")

        subtitle = QLabel(
            "S I M P L E   T O O L S   F O R   A   M O R E   F O C U S E D   E V E N T"
        )
        subtitle.setStyleSheet("font-size:9px;")

        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        header.addLayout(title_layout)
        header.addStretch()

        self.theme_button = QPushButton("☼  Light Mode")
        self.theme_button.clicked.connect(self.toggle_theme)
        header.addWidget(self.theme_button)

        status_dot = QLabel("●  Ready")
        status_dot.setStyleSheet("color:#55D66B;")
        header.addWidget(status_dot)

        root.addLayout(header)

        event_group = QGroupBox()
        event_layout = QVBoxLayout(event_group)

        event_title = QLabel("▤   Event")
        event_title.setStyleSheet(
            "font-size:15px;font-weight:bold;"
        )
        event_subtitle = QLabel("Select or manage your event")

        event_layout.addWidget(event_title)
        event_layout.addWidget(event_subtitle)

        event_row = QHBoxLayout()

        self.event_combo = QComboBox()
        self.event_combo.currentTextChanged.connect(self.change_event)

        new_button = QPushButton("＋  New Event")
        rename_button = QPushButton("✎  Rename")
        delete_button = QPushButton("🗑  Delete")

        new_button.clicked.connect(self.new_event)
        rename_button.clicked.connect(self.rename_event)
        delete_button.clicked.connect(self.delete_event)

        event_row.addWidget(self.event_combo, 1)
        event_row.addWidget(new_button)
        event_row.addWidget(rename_button)
        event_row.addWidget(delete_button)

        event_layout.addLayout(event_row)
        root.addWidget(event_group)

        timer_group = QGroupBox()
        timer_layout = QVBoxLayout(timer_group)

        timer_title = QLabel("◷   Set Timer")
        timer_title.setStyleSheet(
            "font-size:15px;font-weight:bold;"
        )
        timer_subtitle = QLabel(
            "Configure the countdown duration"
        )

        timer_layout.addWidget(timer_title)
        timer_layout.addWidget(timer_subtitle)

        timer_row = QHBoxLayout()

        self.hours = QSpinBox()
        self.hours.setRange(0, 99)

        self.minutes = QSpinBox()
        self.minutes.setRange(0, 59)

        self.seconds = QSpinBox()
        self.seconds.setRange(0, 59)

        for widget in (self.hours, self.minutes, self.seconds):
            widget.valueChanged.connect(self.update_preview)

        timer_row.addWidget(self.create_timer_field("Hours", self.hours))
        timer_row.addWidget(self.create_timer_field("Minutes", self.minutes))
        timer_row.addWidget(self.create_timer_field("Seconds", self.seconds))

        timer_layout.addLayout(timer_row)
        root.addWidget(timer_group)

        display_group = QGroupBox()
        display_layout = QVBoxLayout(display_group)

        self.countdown_label = QLabel("00:05:00")
        self.countdown_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.message_label = QLabel(
            "PLEASE PREPARE TO WRAP UP YOUR TALK."
        )
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_label.setMinimumHeight(58)

        display_layout.addWidget(self.countdown_label)
        display_layout.addWidget(self.message_label)

        controls = QHBoxLayout()

        self.start_button = QPushButton("▶  Start")
        self.reset_button = QPushButton("↻  Reset")

        self.start_button.clicked.connect(
            self.handle_start_pause_resume
        )
        self.reset_button.clicked.connect(self.reset_countdown)

        controls.addWidget(self.start_button)
        controls.addWidget(self.reset_button)

        display_layout.addLayout(controls)

        settings_row = QHBoxLayout()

        # Message configuration and message positioning are both
        # handled inside the Visual Editor.
        editor_button = QPushButton("▦  Edit Layout   ›")
        display_settings_button = QPushButton(
            "▣  Display Settings   ›"
        )
        open_display_button = QPushButton("▣  Open Display")

        editor_button.clicked.connect(self.open_editor)
        display_settings_button.clicked.connect(
            self.open_display_settings
        )
        open_display_button.clicked.connect(self.open_display)

        settings_row.addWidget(editor_button)
        settings_row.addWidget(display_settings_button)
        settings_row.addWidget(open_display_button)

        display_layout.addLayout(settings_row)
        root.addWidget(display_group)

        footer = QHBoxLayout()
        footer.addWidget(QLabel("TPX — Timer Pro X  |  v1.0.0"))
        footer.addStretch()
        footer.addWidget(
            QLabel("F O C U S   •   D E L I V E R   •   I M P A C T")
        )
        root.addLayout(footer)

    def create_timer_field(self, label, widget):
        box = QVBoxLayout()
        box.addWidget(QLabel(label))
        box.addWidget(widget)

        container = QWidget()
        container.setLayout(box)
        return container

    def apply_theme(self):
        if self.theme == "light":
            self.setStyleSheet("""
                QMainWindow { background:#F4F6F8; }
                QWidget { color:#20252B; }
                QGroupBox {
                    background:#F8FAFC;
                    border:1px solid #D5DBE1;
                    border-radius:10px;
                    margin-top:4px;
                    padding:12px;
                }
                QComboBox,QSpinBox {
                    background:white;
                    color:#20252B;
                    border:1px solid #BFC7D0;
                    border-radius:6px;
                    padding:8px;
                }
                QPushButton {
                    background:#E8EDF2;
                    color:#20252B;
                    border:1px solid #C6CED7;
                    border-radius:6px;
                    padding:9px 14px;
                }
                QPushButton:hover { background:#DDE3E9; }
            """)
            self.theme_button.setText("☼  Dark Mode")
        else:
            self.setStyleSheet("""
                QMainWindow { background:#0D141B; }
                QWidget { color:#F4F7FA; }
                QGroupBox {
                    background:#111A23;
                    border:1px solid #273441;
                    border-radius:10px;
                    margin-top:4px;
                    padding:12px;
                }
                QComboBox,QSpinBox {
                    background:#17212B;
                    color:#F4F7FA;
                    border:1px solid #40505F;
                    border-radius:6px;
                    padding:8px;
                }
                QPushButton {
                    background:#222D39;
                    color:#F4F7FA;
                    border:1px solid #3E4D5C;
                    border-radius:6px;
                    padding:9px 14px;
                }
                QPushButton:hover { background:#2C3947; }
            """)
            self.theme_button.setText("☼  Light Mode")

        self.update_message_preview()

        if self.editor_window and self.editor_window.isVisible():
            self.editor_window.theme = self.theme
            self.editor_window.apply_theme()

        if self.display_window:
            self.apply_display_settings()

    def toggle_theme(self):
        self.theme = "light" if self.theme == "dark" else "dark"
        self.apply_theme()

    def refresh_event_combo(self, selected=None):
        self.event_combo.blockSignals(True)
        self.event_combo.clear()

        for event in self.events:
            self.event_combo.addItem(
                event.get("name", "Unnamed Event")
            )

        if selected:
            index = self.event_combo.findText(selected)
            if index >= 0:
                self.event_combo.setCurrentIndex(index)

        self.event_combo.blockSignals(False)

    def change_event(self, name):
        if not name or name == self.current_event_name:
            return

        self.save_current_event()
        self.load_event(name)

    def show_warning(self, title, message):
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle(title)
        box.setText(message)

        if self.theme == "light":
            box.setStyleSheet("""
                QMessageBox { background:#F3F5F7; }
                QMessageBox QLabel {
                    color:#20252B;
                    font-size:14px;
                }
                QMessageBox QPushButton {
                    background:#E9EDF2;
                    color:#20252B;
                    border:1px solid #C5CBD2;
                    border-radius:6px;
                    padding:7px 18px;
                    min-width:60px;
                }
            """)
        else:
            box.setStyleSheet("""
                QMessageBox { background:#11171E; }
                QMessageBox QLabel {
                    color:#F4F7FA;
                    font-size:14px;
                }
                QMessageBox QPushButton {
                    background:#242E39;
                    color:#F4F7FA;
                    border:1px solid #40505F;
                    border-radius:6px;
                    padding:7px 18px;
                    min-width:60px;
                }
            """)

        box.exec()

    def load_event(self, name):
        event = next(
            (item for item in self.events if item.get("name") == name),
            None,
        )
        if event is None:
            return

        self.current_event_name = name
        self.messages = [
            self.dict_to_message(data)
            for data in event.get("messages", [])
        ]

        if not any(m.name == "__DEFAULT__" for m in self.messages):
            self.messages.insert(
                0,
                TimerMessage(
                    "__DEFAULT__", -1, "Time Remaining",
                    "#FFFFFF", False, 0
                ),
            )

        if "display" not in event:
            event["display"] = {
                "monitor": 0,
                "fullscreen": False,
                "use_theme_colors": True,
                "timer_color": "#FFFFFF",
                "message_color": "#FFFFFF",
                "timer_font_size": 100,
                "message_font_size": 40,
            }

        self.refresh_event_combo(name)
        self.reset_countdown()

        # Refresh an already-open output with the new event layout.
        if self.display_window:
            self.display_window.load_event_layout(name)
            self.update_message_preview()

    def save_current_event(self):
        if not self.current_event_name:
            return

        for event in self.events:
            if event.get("name") == self.current_event_name:
                event["messages"] = [
                    self.message_to_dict(message)
                    for message in self.messages
                ]
                break

        save_events(self.events)

    def new_event(self):
        name, ok = QInputDialog.getText(
            self,
            "New Event",
            "Event name:",
        )
        if not ok:
            return

        name = name.strip()
        if not name:
            return

        if any(e.get("name") == name for e in self.events):
            QMessageBox.warning(
                self,
                "TPX",
                "Event already exists.",
            )
            return

        self.save_current_event()

        event = self.create_default_event()
        event["name"] = name
        self.events.append(event)

        save_events(self.events)
        self.load_event(name)

    def rename_event(self):
        old_name = self.current_event_name

        new_name, ok = QInputDialog.getText(
            self,
            "Rename Event",
            "New event name:",
            text=old_name,
        )
        if not ok:
            return

        new_name = new_name.strip()
        if not new_name:
            return

        if any(
            e.get("name") == new_name and e.get("name") != old_name
            for e in self.events
        ):
            QMessageBox.warning(
                self,
                "TPX",
                "Event already exists.",
            )
            return

        for event in self.events:
            if event.get("name") == old_name:
                event["name"] = new_name
                break

        self.current_event_name = new_name
        save_events(self.events)
        self.refresh_event_combo(new_name)

    def delete_event(self):
        if len(self.events) <= 1:
            QMessageBox.information(
                self,
                "TPX",
                "At least one event is required.",
            )
            return

        answer = QMessageBox.question(
            self,
            "Delete Event",
            f"Delete '{self.current_event_name}'?",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        name = self.current_event_name

        self.events = [
            e for e in self.events
            if e.get("name") != name
        ]

        save_events(self.events)
        self.load_event(self.events[0]["name"])

    @staticmethod
    def message_to_dict(message):
        return {
            "name": message.name,
            "trigger_seconds": message.trigger_seconds,
            "message": message.message,
            "color": message.color,
            "beep": message.beep,
            "beep_seconds": message.beep_seconds,
        }

    @staticmethod
    def dict_to_message(data):
        return TimerMessage(
            data.get("name", "Message"),
            int(data.get("trigger_seconds", 0)),
            data.get("message", ""),
            data.get("color", "#FFFFFF"),
            bool(data.get("beep", False)),
            int(data.get("beep_seconds", 0)),
        )

    def get_seconds(self):
        return (
            self.hours.value() * 3600
            + self.minutes.value() * 60
            + self.seconds.value()
        )

    def format_time(self, seconds):
        seconds = max(0, seconds)
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{h:02d}:{m:02d}:{s:02d}"

    def update_preview(self):
        if self.running:
            return

        self.time_left = self.get_seconds()
        self.update_message_preview()

    def get_default_message(self):
        return next(
            (
                message for message in self.messages
                if message.name == "__DEFAULT__"
            ),
            TimerMessage(
                "__DEFAULT__", -1, "Time Remaining",
                "#FFFFFF", False, 0
            ),
        )

    def get_active_message(self):
        default = self.get_default_message()

        # IMPORTANT:
        # Threshold means "show this message when remaining time
        # is at or below this trigger". The closest lower/equal
        # threshold wins.
        eligible = [
            message
            for message in self.messages
            if (
                message.name != "__DEFAULT__"
                and self.time_left <= message.trigger_seconds
            )
        ]

        if not eligible:
            return default

        return min(
            eligible,
            key=lambda m: m.trigger_seconds,
        )

    def update_message_preview(self):
        message = self.get_active_message()

        self.countdown_label.setText(
            self.format_time(self.time_left)
        )
        self.message_label.setText(message.message)

        if message.name == "__DEFAULT__":
            color = "#20252B" if self.theme == "light" else "#FFFFFF"
        else:
            color = message.color

        self.countdown_label.setStyleSheet(
            f"""
            font-size:92px;
            font-weight:bold;
            color:{color};
            """
        )

        self.message_label.setStyleSheet(
            f"""
            font-size:21px;
            font-weight:bold;
            color:{color};
            border:1px solid {color};
            border-radius:10px;
            padding:12px;
            """
        )

        if self.display_window:
            self.display_window.update_output(
                self.format_time(self.time_left),
                message.message,
                message.color if message.name != "__DEFAULT__" else color,
                message.name,
            )

    def handle_start_pause_resume(self):
        if self.running:
            self.timer.stop()
            self.running = False
            self.paused = True
            self.start_button.setText("▶  Resume")
            return

        if self.paused:
            self.running = True
            self.paused = False
            self.timer.start()
            self.start_button.setText("Ⅱ  Pause")
            return

        self.start_countdown()

    def start_countdown(self):
        if self.running:
            return

        total = self.get_seconds()

        if total <= 0:
            self.show_warning("TPX", "Set a timer first.")
            return

        self.time_left = total
        self.triggered.clear()
        self.running = True
        self.paused = False
        self.start_button.setText("Ⅱ  Pause")
        self.timer.start()
        self.update_message_preview()

    def reset_countdown(self):
        self.timer.stop()
        self.running = False
        self.paused = False
        self.triggered.clear()
        self.time_left = self.get_seconds()
        self.start_button.setText("▶  Start")
        self.update_message_preview()

    def countdown_tick(self):
        if not self.running or self.paused:
            return

        self.time_left -= 1
        if self.time_left < 0:
            self.time_left = 0

        self.update_message_preview()

        active = self.get_active_message()

        if (
            active.name != "__DEFAULT__"
            and active.trigger_seconds == self.time_left
        ):
            trigger_key = (
                active.name,
                active.trigger_seconds,
            )

            if trigger_key not in self.triggered:
                self.triggered.add(trigger_key)
                if active.beep:
                    beep_sequence(active.beep_seconds)

        if self.time_left <= 0:
            self.timer.stop()
            self.running = False
            self.paused = False
            self.start_button.setText("▶  Start")

    def message_settings_changed(self):
        self.save_current_event()
        self.update_message_preview()

    def get_editor_messages(self):
        return [
            self.message_to_dict(message)
            for message in self.messages
        ]

    def apply_editor_messages(self, message_dicts):
        self.messages = [
            self.dict_to_message(data)
            for data in message_dicts
        ]

        if not any(
            message.name == "__DEFAULT__"
            for message in self.messages
        ):
            self.messages.insert(
                0,
                TimerMessage(
                    "__DEFAULT__",
                    -1,
                    "Time Remaining",
                    "#FFFFFF",
                    False,
                    0,
                ),
            )

        self.save_current_event()
        self.update_message_preview()

    def open_editor(self):
        self.save_current_event()

        if self.editor_window and self.editor_window.isVisible():
            self.editor_window.theme = self.theme
            self.editor_window.apply_theme()
            self.editor_window.show()
            self.editor_window.raise_()
            self.editor_window.activateWindow()
            return

        self.editor_window = VisualEditor(
            self.current_event_name,
            self,
            theme=self.theme,
            messages=self.get_editor_messages(),
            on_messages_changed=self.apply_editor_messages,
        )
        self.editor_window.setModal(False)
        self.editor_window.show()
        self.editor_window.raise_()
        self.editor_window.activateWindow()

    def get_current_event(self):
        return next(
            (
                event for event in self.events
                if event.get("name") == self.current_event_name
            ),
            None,
        )

    def get_display_settings(self):
        event = self.get_current_event()

        default = {
            "monitor": 0,
            "fullscreen": False,
            "use_theme_colors": True,
            "timer_color": "#FFFFFF",
            "message_color": "#FFFFFF",
            "timer_font_size": 100,
            "message_font_size": 40,
        }

        if event is None:
            return default

        if "display" not in event:
            event["display"] = default.copy()

        return event["display"]

    def open_display_settings(self):
        settings = self.get_display_settings()

        dialog = DisplaySettingsDialog(
            settings,
            self.theme,
            self,
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            save_events(self.events)
            self.apply_display_settings()

    def apply_display_settings(self):
        if self.display_window is None:
            return

        settings = self.get_display_settings()

        self.display_window.configure(
            self.theme,
            settings.get("timer_color", "#FFFFFF"),
            settings.get("message_color", "#FFFFFF"),
            settings.get("use_theme_colors", True),
            settings.get("timer_font_size", 100),
            settings.get("message_font_size", 40),
        )

    def open_display(self):
        # If editor is open, silently save its latest changes first.
        if self.editor_window and self.editor_window.isVisible():
            self.editor_window.save_layout(silent=True)

        if self.display_window is None:
            self.display_window = DisplayWindow()

        # IMPORTANT: Output always loads the exact layout JSON
        # belonging to the selected event.
        self.display_window.load_event_layout(
            self.current_event_name
        )

        settings = self.get_display_settings()
        screens = QApplication.screens()

        if not screens:
            return

        monitor = settings.get("monitor", 0)
        monitor = max(0, min(monitor, len(screens) - 1))

        self.display_window.move_to_screen(
            screens[monitor],
            settings.get("fullscreen", False),
        )

        self.display_window.show()
        self.display_window.raise_()
        self.display_window.activateWindow()

        message = self.get_active_message()

        self.display_window.update_output(
            self.format_time(self.time_left),
            message.message,
            (
                message.color
                if message.name != "__DEFAULT__"
                else (
                    "#20252B"
                    if self.theme == "light"
                    else "#FFFFFF"
                )
            ),
            message.name,
        )

    def closeEvent(self, event):
        self.save_current_event()

        if self.editor_window:
            self.editor_window.close()

        if self.display_window:
            self.display_window.hide()

        event.accept()


def show_tpx_splash(app):
    splash_path = resource_path("assets", "splash.png")

    if not os.path.exists(splash_path):
        return None

    pixmap = QPixmap(splash_path)

    if pixmap.isNull():
        return None

    # Scale splash to a reasonable window size
    pixmap = pixmap.scaled(
        900,
        600,
        Qt.KeepAspectRatio,
        Qt.SmoothTransformation
    )

    splash = QSplashScreen(
        pixmap,
        Qt.WindowStaysOnTopHint
    )

    splash.setWindowFlag(Qt.FramelessWindowHint)
    splash.show()

    app.processEvents()

    return splash


def main():
    set_windows_app_id()

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_DISPLAY_NAME)

    icon_path = resource_path("assets", "tpx-icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # Show splash first
    splash = show_tpx_splash(app)

    # Let the splash render
    app.processEvents()

    # Wait 3.5 seconds BEFORE opening the main window
    if splash is not None:
        QTimer.singleShot(2000, splash.close)

        # Keep splash visible while waiting
        loop = QEventLoop()
        QTimer.singleShot(2000, loop.quit)
        loop.exec()

    # NOW create and show the main application
    window = CountdownApp()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
