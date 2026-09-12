import os
import sys
import json
import time
import threading
import ctypes
import gc

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

def trim_memory():
    """Trims inactive memory pages on Windows to keep DIL DIL ultra-lightweight (<30 MB)."""
    try:
        gc.collect()
        kernel32 = ctypes.windll.kernel32
        psapi = ctypes.windll.psapi
        kernel32.GetCurrentProcess.restype = ctypes.c_void_p
        psapi.EmptyWorkingSet.argtypes = [ctypes.c_void_p]
        psapi.EmptyWorkingSet.restype = ctypes.c_int
        psapi.EmptyWorkingSet(kernel32.GetCurrentProcess())
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
class TeeLogger:
    def __init__(self, filepath, stream=None):
        self.filepath = filepath
        self.stream = stream
        self._file = open(filepath, "a", encoding="utf-8")

    def write(self, msg):
        if self.stream:
            try:
                self.stream.write(msg)
                self.stream.flush()
            except Exception:
                pass
        try:
            self._file.write(msg)
            self._file.flush()
        except Exception:
            pass

    def flush(self):
        if self.stream:
            try:
                self.stream.flush()
            except Exception:
                pass
        try:
            self._file.flush()
        except Exception:
            pass

LOG_PATH = os.path.join(BASE_DIR, "app_runtime.log")
sys.stdout = TeeLogger(LOG_PATH, sys.stdout)
sys.stderr = TeeLogger(LOG_PATH, sys.stderr)

# Windows Taskbar AppUserModelID registration so custom icon is used instead of Python's snake icon
try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("dildil.pakistan.voice.assistant.v1")
except Exception:
    pass

from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtNetwork import QLocalServer, QLocalSocket

from core.recorder import AudioRecorder
from core.hotkey import HotkeyManager
from core.gemini_engine import GeminiEngine
from core.typer import Typer, ClipboardSessionGuard
from ui.floating_pill import FloatingPill
from ui.main_window import MainWindow

IPC_SERVER_NAME = "DIL_DIL_SINGLE_INSTANCE_IPC"

def try_activate_existing_instance() -> bool:
    """
    Attempts to connect to an already-running DIL DIL instance via local IPC socket.
    If running, tells it to restore and show its dashboard, and returns True.
    """
    socket = QLocalSocket()
    socket.connectToServer(IPC_SERVER_NAME)
    if socket.waitForConnected(600):
        try:
            ctypes.windll.user32.AllowSetForegroundWindow(-1)
        except Exception:
            pass
        socket.disconnectFromServer()
        print("[DIL DIL] Existing instance active. Triggered restore signal.")
        return True
    return False

CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
ICON_FILE = os.path.join(BASE_DIR, "assets", "app_icon.ico")
EMBLEM_ICO_FILE = os.path.join(BASE_DIR, "assets", "dil_dil_v2.ico")
PNG_ICON_FILE = os.path.join(BASE_DIR, "assets", "icon.png")
VOICE_PROFILE_FILE = os.path.join(BASE_DIR, "assets", "user_voice_profile.wav")

class DilDilApp:
    def __init__(self, qapp: QApplication):
        self.qapp = qapp
        self.config = self._load_config()

        self.target_hwnd = None
        self.is_recording_active = False
        self.session_id = 0

        # Set multi-resolution application icon for Windows
        self.app_icon = QIcon()
        if os.path.exists(EMBLEM_ICO_FILE):
            self.app_icon.addFile(EMBLEM_ICO_FILE)
        if os.path.exists(ICON_FILE):
            self.app_icon.addFile(ICON_FILE)
        if os.path.exists(PNG_ICON_FILE):
            self.app_icon.addFile(PNG_ICON_FILE)
        self.qapp.setWindowIcon(self.app_icon)

        # Initialize Main Dashboard Window
        self.main_window = MainWindow(
            CONFIG_FILE,
            on_config_updated=self._on_config_updated,
            on_quit=self._exit_app,
            on_tray_notify=self._notify_tray
        )
        self.main_window.setWindowIcon(self.app_icon)
        self.main_window.show()
        self.qapp.processEvents()

        # Initialize Floating Pill UI (Minimal Wispr Flow design)
        self.pill = FloatingPill()

        # Initialize Gemini Engine with dynamic model auto-discovery
        api_key = self.config.get("gemini_api_key", "")
        active_model = self.config.get("active_model", "gemini-flash-lite-latest")
        self.gemini = GeminiEngine(
            api_key=api_key,
            model_name=active_model,
            on_model_changed=self._on_model_upgraded
        )

        # Initialize Audio Recorder
        self.recorder = AudioRecorder(
            sample_rate=self.config.get("audio_sample_rate", 16000),
            on_amplitude_callback=self._on_audio_amplitude
        )

        # Initialize Hotkey Manager
        hotkey_str = self.config.get("hotkey", "ctrl+shift")
        self.hotkey = HotkeyManager(
            hotkey_str=hotkey_str,
            on_press_callback=self._on_hotkey_press,
            on_release_callback=self._on_hotkey_release
        )

        # Initialize System Tray
        self._init_tray()

        # Initialize Local IPC Server for instant single instance restoration
        self._init_ipc_server()

        # Start hotkey listener
        self.hotkey.start()

        # Optimize working set memory for ultra-lightweight RAM footprint (<30 MB)
        trim_memory()

    def _load_config(self) -> dict:
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "app_name": "DIL DIL",
            "gemini_api_key": "",
            "active_model": "gemini-flash-lite-latest",
            "hotkey": "ctrl+shift",
            "target_language": "english",
            "audio_sample_rate": 16000,
            "minimize_to_tray": True
        }

    def _on_model_upgraded(self, new_model_name: str):
        """Called automatically when GeminiEngine discovers and validates a newer model."""
        self.config["active_model"] = new_model_name
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2)
        except Exception:
            pass
        print(f"[DIL DIL] Model auto-upgraded to: {new_model_name}")
        try:
            QTimer.singleShot(0, lambda: self.main_window.update_active_model_badge(new_model_name))
        except Exception:
            pass

    def _init_tray(self):
        self.tray_icon = QSystemTrayIcon(self.app_icon, self.qapp)
        hk = self.config.get("hotkey", "ctrl+shift").upper()
        self.tray_icon.setToolTip(f"DIL DIL (Hold {hk})")

        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #070a0e;
                color: #ffffff;
                border: 1px solid #1a2f24;
                padding: 6px;
                font-family: 'Segoe UI', sans-serif;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #059669;
            }
        """)

        open_action = QAction("Open DIL DIL", menu)
        open_action.triggered.connect(self._show_main_window)
        menu.addAction(open_action)

        menu.addSeparator()
        quit_action = QAction("Exit DIL DIL", menu)
        quit_action.triggered.connect(self._exit_app)
        menu.addAction(quit_action)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def _on_tray_activated(self, reason):
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            self._show_main_window()

    def _notify_tray(self, title: str, message: str):
        if self.tray_icon.isVisible():
            self.tray_icon.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 2500)

    def _init_ipc_server(self):
        self.ipc_server = QLocalServer(self.qapp)
        QLocalServer.removeServer(IPC_SERVER_NAME)
        self.ipc_server.listen(IPC_SERVER_NAME)
        self.ipc_server.newConnection.connect(self._on_ipc_connection)

    def _on_ipc_connection(self):
        while self.ipc_server.hasPendingConnections():
            client = self.ipc_server.nextPendingConnection()
            if client:
                client.disconnectFromServer()
        print("[DIL DIL] Single instance activation request received -> Showing window.")
        QTimer.singleShot(0, self._show_main_window)

    def _show_main_window(self):
        print("[DIL DIL] Restoring main window...")
        self.main_window.setWindowState(Qt.WindowState.WindowNoState)
        self.main_window.showNormal()
        self.main_window.show()
        self.main_window.raise_()
        self.main_window.activateWindow()
        self.main_window.update()

        try:
            hwnd = int(self.main_window.winId())
            user32.ShowWindow(hwnd, 9)  # SW_RESTORE
            fg_hwnd = user32.GetForegroundWindow()
            if fg_hwnd and fg_hwnd != hwnd:
                fg_thread = user32.GetWindowThreadProcessId(fg_hwnd, None)
                cur_thread = user32.GetCurrentThreadId()
                if fg_thread != cur_thread:
                    user32.AttachThreadInput(cur_thread, fg_thread, True)
                    user32.SetForegroundWindow(hwnd)
                    user32.BringWindowToTop(hwnd)
                    user32.AttachThreadInput(cur_thread, fg_thread, False)
                else:
                    user32.SetForegroundWindow(hwnd)
                    user32.BringWindowToTop(hwnd)
            else:
                user32.SetForegroundWindow(hwnd)
                user32.BringWindowToTop(hwnd)
        except Exception as e:
            print(f"[DIL DIL] Window restore note: {e}")

    def _on_config_updated(self, new_config: dict):
        self.config = new_config
        self.gemini.set_api_key(new_config.get("gemini_api_key", ""))
        new_hk = new_config.get("hotkey", "ctrl+shift")
        self.hotkey.set_hotkey(new_hk)
        self.tray_icon.setToolTip(f"DIL DIL (Hold {new_hk.upper()})")
        print(f"[DIL DIL] Configuration updated: Hotkey={new_hk}, Lang={new_config.get('target_language')}")

    def _on_audio_amplitude(self, amp: float):
        self.pill.update_amplitude_signal.emit(amp)

    def _on_hotkey_press(self):
        """Fires when user holds down the configured push-to-talk hotkey."""
        if not self.gemini.is_configured():
            return

        self.session_id += 1
        self.is_recording_active = True

        # Capture active foreground window handle at keypress
        self.target_hwnd = Typer.get_foreground_window()
        print(f"[DIL DIL] Hotkey Pressed! Session: {self.session_id}, Window: {self.target_hwnd}")

        target_lang = self.config.get("target_language", "english")
        self.pill.show_listening(target_lang)

        try:
            self.recorder.start()
        except Exception as e:
            print(f"[DIL DIL Error] Recorder start failed: {e}")
            self.pill.show_error(str(e))
            self.is_recording_active = False

    def _on_hotkey_release(self):
        """Fires when user releases the hotkey."""
        if not self.gemini.is_configured():
            return

        if not self.is_recording_active:
            return
        self.is_recording_active = False

        # Update target window if valid
        active_hwnd = Typer.get_foreground_window()
        if active_hwnd:
            self.target_hwnd = active_hwnd

        try:
            wav_bytes = self.recorder.stop()
        except Exception as e:
            print(f"[DIL DIL Error] Recorder stop error: {e}")
            wav_bytes = b""

        print(f"[DIL DIL] Hotkey Released. Audio length: {len(wav_bytes)} bytes")

        if not wav_bytes or len(wav_bytes) < 6000:
            print("[DIL DIL] Silence detected (<0.18s or silence VAD), dismissing without pasting.")
            self.pill.hide_pill()
            trim_memory()
            return

        # Switch pill to processing animation
        self.pill.show_thinking()

        # Launch streaming transcription in background
        curr_session = self.session_id
        target_hwnd = self.target_hwnd
        threading.Thread(
            target=self._process_session,
            args=(curr_session, wav_bytes, target_hwnd),
            daemon=True
        ).start()

    def _process_session(self, session_id: int, wav_bytes: bytes, target_hwnd):
        """
        Transcribes audio with Gemini via generate_content_stream.
        Pastes each sentence progressively at the user's cursor as soon as it arrives!
        Safeguards and restores the user's original clipboard with 100% fidelity.
        """
        clipboard_guard = ClipboardSessionGuard()
        sentence_count = 0
        target_lang = self.config.get("target_language", "english")

        def _on_sentence(sentence_text: str):
            nonlocal sentence_count
            if session_id != self.session_id:
                return

            if not sentence_text or not sentence_text.strip():
                return

            prefix = "" if sentence_count == 0 else " "
            sentence_count += 1

            print(f"[DIL DIL] Pasting Sentence {sentence_count}: \"{sentence_text}\"")
            Typer.paste_text(prefix + sentence_text, fallback_hwnd=target_hwnd, preserve_clipboard=True)

        try:
            full_text = self.gemini.process_audio_stream(
                wav_bytes,
                target_lang=target_lang,
                on_sentence=_on_sentence
            )

            if session_id == self.session_id:
                if sentence_count > 0 or (full_text and len(full_text.strip()) > 0):
                    self.pill.show_success(sentence_count)
                    print(f"[DIL DIL] Dictation complete. {sentence_count} sentence(s) pasted.")
                else:
                    self.pill.hide_pill()
        except Exception as e:
            if session_id == self.session_id:
                print(f"[DIL DIL Error] Session {session_id} failed: {e}")
                self.pill.show_error(str(e))
        finally:
            try:
                clipboard_guard.restore()
            except Exception:
                pass
            trim_memory()

    def _exit_app(self):
        """Completely terminates the application."""
        print("[DIL DIL] Terminating application...")
        self.hotkey.stop()
        self.tray_icon.hide()
        self.main_window.close()
        self.pill.close()
        self.qapp.quit()

def main():
    # If an existing instance is already running, activate it via IPC and exit immediately
    if try_activate_existing_instance():
        sys.exit(0)

    qapp = QApplication(sys.argv)
    qapp.setQuitOnLastWindowClosed(False)

    app = DilDilApp(qapp)
    sys.exit(qapp.exec())

if __name__ == "__main__":
    main()
