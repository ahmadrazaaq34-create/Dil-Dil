import math
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRectF, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPainter, QColor, QBrush, QLinearGradient, QPen

class CompactFluidWaveform(QWidget):
    """
    Ultra-compact 5-bar fluid equalizer that dances to microphone volume.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(50, 20)
        self.bar_count = 5
        self.heights = [0.25] * self.bar_count
        self.target_heights = [0.25] * self.bar_count
        self.phase = 0.0

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._step)
        self.timer.start(16)

    def set_active(self, active: bool):
        if active and not self.timer.isActive():
            self.timer.start(16)
        elif not active and self.timer.isActive():
            self.timer.stop()

    def reset_bars(self):
        self.heights = [0.25] * self.bar_count
        self.target_heights = [0.25] * self.bar_count
        self.phase = 0.0
        self.update()

    def update_volume(self, amp: float):
        base_amp = max(0.18, min(1.0, amp))
        for i in range(self.bar_count):
            weight = 1.0 - (abs(i - 2) * 0.2)
            wave = math.sin(self.phase + (i * 1.2)) * 0.15
            self.target_heights[i] = max(0.18, min(1.0, (base_amp * weight) + wave))

    def _step(self):
        self.phase += 0.22
        for i in range(self.bar_count):
            diff = self.target_heights[i] - self.heights[i]
            self.heights[i] += diff * 0.35
            idle = 0.2 + (math.sin(self.phase + i) * 0.08)
            self.target_heights[i] = max(idle, self.target_heights[i] * 0.88)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        bar_w = 3.2
        gap = 4.2
        total_w = (self.bar_count * bar_w) + ((self.bar_count - 1) * gap)
        start_x = (w - total_w) / 2.0

        for i in range(self.bar_count):
            val = self.heights[i]
            bar_h = max(4.0, h * 0.9 * val)
            x = start_x + (i * (bar_w + gap))
            y = (h - bar_h) / 2.0

            grad = QLinearGradient(x, y + bar_h, x, y)
            grad.setColorAt(0.0, QColor(0, 168, 89))     # Vibrant Pakistan Green
            grad.setColorAt(1.0, QColor(255, 255, 255))  # Crisp Pure White

            painter.setBrush(QBrush(grad))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(QRectF(x, y, bar_w, bar_h), 1.6, 1.6)

        painter.end()


class ProcessingDots(QWidget):
    """
    Sleek pulsing 3-dot loading animation in Pakistan green & white.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(50, 20)
        self.phase = 0.0
        self.dot_color = QColor(16, 185, 129) # Emerald Pakistan Green
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._step)
        self.timer.start(24)

    def set_color(self, color: QColor):
        self.dot_color = color
        self.update()

    def set_active(self, active: bool):
        if active and not self.timer.isActive():
            self.timer.start(24)
        elif not active and self.timer.isActive():
            self.timer.stop()

    def _step(self):
        self.phase += 0.22
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        dot_radius = 2.8
        spacing = 9.5
        start_x = (w - (2 * spacing)) / 2.0
        center_y = h / 2.0

        for i in range(3):
            offset_y = math.sin(self.phase + (i * 0.85)) * 3.5
            x = start_x + (i * spacing)
            y = center_y + offset_y

            # Alternate or highlight center dot with white for Pakistani flag motif
            if i == 1:
                painter.setBrush(QBrush(QColor(255, 255, 255)))
            else:
                painter.setBrush(QBrush(self.dot_color))

            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QRectF(x - dot_radius, y - dot_radius, dot_radius * 2, dot_radius * 2))

        painter.end()


class StatusDot(QWidget):
    """
    Single glowing dot indicator for completion (green) or error (red).
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(50, 20)
        self.color = QColor(16, 185, 129) # Emerald Green

    def set_color(self, color: QColor):
        self.color = color
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        radius = 4.0
        center_x = w / 2.0
        center_y = h / 2.0

        # Outer soft glow
        glow_color = QColor(self.color.red(), self.color.green(), self.color.blue(), 80)
        painter.setBrush(QBrush(glow_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(center_x - 7.0, center_y - 7.0, 14.0, 14.0))

        # Core dot
        painter.setBrush(QBrush(self.color))
        painter.drawEllipse(QRectF(center_x - radius, center_y - radius, radius * 2, radius * 2))
        painter.end()


class FloatingPill(QWidget):
    """
    Authentic Wispr Flow Minimalist Pill - DIL DIL Edition.
    Ultra-compact (88x30px), matte black glassmorphism with Pakistan Green & White:
    - Listening: 5-bar fluid equalizer in green & white
    - Processing: 3-dot smooth bouncing loader in green & white
    - Pasted: Glowing emerald green dot pulse, then smooth fade out
    """
    update_state_signal = pyqtSignal(str)
    update_amplitude_signal = pyqtSignal(float)

    def __init__(self):
        super().__init__()
        self._init_flags()
        self._init_ui()
        self._setup_animation()

    def _init_flags(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

    def _init_ui(self):
        self.setFixedSize(88, 30)
        self.current_state = "hidden"

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Dynamic animation widgets
        self.waveform = CompactFluidWaveform()
        self.processing_dots = ProcessingDots()
        self.status_dot = StatusDot()

        self.processing_dots.hide()
        self.status_dot.hide()

        layout.addWidget(self.waveform)
        layout.addWidget(self.processing_dots)
        layout.addWidget(self.status_dot)

        # Drop shadow for soft floating depth
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(18)
        shadow.setColor(QColor(0, 0, 0, 220))
        shadow.setOffset(0, 3)
        self.setGraphicsEffect(shadow)

        # Auto-hide timer for completion state
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self._fade_out)

        # Connect signals
        self.update_state_signal.connect(self._handle_state)
        self.update_amplitude_signal.connect(self.waveform.update_volume)

        self._position_on_screen()

    def _setup_animation(self):
        self.fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_anim.setDuration(160)
        self.fade_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.fade_anim.finished.connect(self._on_fade_finished)

        self.appear_anim = QPropertyAnimation(self, b"windowOpacity")
        self.appear_anim.setDuration(120)
        self.appear_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def _position_on_screen(self):
        screen = self.screen().geometry()
        x = (screen.width() - self.width()) // 2
        y = screen.height() - self.height() - 75
        self.move(x, y)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(1.0, 1.0, self.width() - 2.0, self.height() - 2.0)
        # Deep matte obsidian black
        bg_brush = QBrush(QColor(7, 11, 16, 245))
        painter.setBrush(bg_brush)

        # Dynamic state border in green & white
        if self.current_state in ("thinking", "live", "processing", "pasting"):
            painter.setPen(QPen(QColor(52, 211, 153, 190), 1.3))
        elif self.current_state == "listening":
            painter.setPen(QPen(QColor(16, 185, 129, 210), 1.3))
        elif self.current_state == "success":
            painter.setPen(QPen(QColor(16, 185, 129, 240), 1.4))
        elif self.current_state == "error":
            painter.setPen(QPen(QColor(244, 63, 94, 180), 1.2))
        else:
            painter.setPen(QPen(QColor(255, 255, 255, 50), 1.0))

        painter.drawRoundedRect(rect, 14.0, 14.0)
        painter.end()


    def _handle_state(self, state: str):
        self.current_state = state
        self.hide_timer.stop()

        if state == "listening":
            self.fade_anim.stop()
            self.appear_anim.stop()
            self.setWindowOpacity(1.0)
            self.processing_dots.hide()
            self.status_dot.hide()
            self.waveform.reset_bars()
            self.waveform.show()
            self._position_on_screen()
            self.show()

        elif state in ("thinking", "live", "processing", "pasting"):
            self.fade_anim.stop()
            self.setWindowOpacity(1.0)
            self.waveform.hide()
            self.status_dot.hide()
            self.processing_dots.set_color(QColor(56, 189, 248))
            self.processing_dots.show()
            self._position_on_screen()
            self.show()

        elif state == "success":
            self.waveform.hide()
            self.processing_dots.hide()
            self.status_dot.set_color(QColor(34, 197, 94))
            self.status_dot.show()
            self.show()
            self.hide_timer.start(380)

        elif state == "error":
            self.waveform.hide()
            self.processing_dots.hide()
            self.status_dot.set_color(QColor(244, 63, 94))
            self.status_dot.show()
            self.show()
            self.hide_timer.start(800)

        elif state == "hidden":
            self._fade_out()

        self.update()

    def _fade_out(self):
        if self.current_state == "listening":
            return
        self.fade_anim.stop()
        self.fade_anim.setStartValue(self.windowOpacity())
        self.fade_anim.setEndValue(0.0)
        self.fade_anim.start()

    def _on_fade_finished(self):
        if self.windowOpacity() == 0.0 and self.current_state != "listening":
            self.hide()

    def show_welcome(self):
        self.update_state_signal.emit("processing")
        self.hide_timer.start(500)

    def show_listening(self, target_lang: str = ""):
        self.update_state_signal.emit("listening")

    def show_thinking(self):
        self.update_state_signal.emit("processing")

    def show_transcribing(self, pasted_count: int = 0):
        self.update_state_signal.emit("processing")

    def show_pasting(self):
        self.update_state_signal.emit("processing")

    def show_success(self, pasted_count: int = 0):
        self.update_state_signal.emit("success")

    def show_error(self, err_msg: str = ""):
        self.update_state_signal.emit("error")

    def hide_pill(self):
        self.update_state_signal.emit("hidden")

