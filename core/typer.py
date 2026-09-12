import os
import time
import ctypes
from ctypes import wintypes
import pyperclip

# Windows API constants
user32 = ctypes.windll.user32
VK_CONTROL = 0x11
VK_SHIFT = 0x10
VK_MENU = 0x12  # Alt key
VK_V = 0x56
KEYEVENTF_KEYUP = 0x0002

class Typer:
    @staticmethod
    def get_foreground_window():
        """Returns the handle of the currently focused window."""
        try:
            return user32.GetForegroundWindow()
        except Exception:
            return None

    @staticmethod
    def get_window_pid(hwnd):
        """Returns the process ID that owns the given window handle."""
        if not hwnd:
            return None
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        return pid.value

    @staticmethod
    def restore_focus(hwnd):
        """Restores focus to the given window handle."""
        if hwnd:
            try:
                current_thread = user32.GetCurrentThreadId()
                target_thread = user32.GetWindowThreadProcessId(hwnd, None)
                if current_thread != target_thread:
                    user32.AttachThreadInput(current_thread, target_thread, True)
                    user32.SetForegroundWindow(hwnd)
                    user32.AttachThreadInput(current_thread, target_thread, False)
                else:
                    user32.SetForegroundWindow(hwnd)
            except Exception:
                try:
                    user32.SetForegroundWindow(hwnd)
                except Exception:
                    pass

    @staticmethod
    def paste_text(text: str, fallback_hwnd=None):
        """
        Pastes text directly at the user's active cursor.
        Crucial: Never yanks focus away from the active foreground window
        where the user has their cursor. Only restores fallback_hwnd if the
        current foreground window is invalid or belongs to Wispr Flow itself.
        """
        if not text:
            return

        current_hwnd = Typer.get_foreground_window()
        my_pid = os.getpid()
        current_pid = Typer.get_window_pid(current_hwnd) if current_hwnd else None

        # Only switch focus if current foreground window is invalid or belongs to our own app
        if (not current_hwnd or current_pid == my_pid) and fallback_hwnd:
            fallback_pid = Typer.get_window_pid(fallback_hwnd)
            if fallback_pid and fallback_pid != my_pid:
                Typer.restore_focus(fallback_hwnd)
                time.sleep(0.05)

        # Copy text to clipboard with retries in case clipboard is momentarily locked
        for _ in range(3):
            try:
                pyperclip.copy(text)
                break
            except Exception:
                time.sleep(0.01)
        time.sleep(0.015)

        # Release any lingering modifier keys (Ctrl, Shift, Alt) so Ctrl+V is clean
        user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
        user32.keybd_event(VK_SHIFT, 0, KEYEVENTF_KEYUP, 0)
        user32.keybd_event(VK_MENU, 0, KEYEVENTF_KEYUP, 0)
        time.sleep(0.008)

        # Simulate Ctrl + V key press using Windows API
        user32.keybd_event(VK_CONTROL, 0, 0, 0)
        time.sleep(0.008)
        user32.keybd_event(VK_V, 0, 0, 0)
        time.sleep(0.008)
        user32.keybd_event(VK_V, 0, KEYEVENTF_KEYUP, 0)
        time.sleep(0.008)
        user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)


