import os
import time
import ctypes
from ctypes import wintypes
import pyperclip

# Windows API constants
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

VK_CONTROL = 0x11
VK_SHIFT = 0x10
VK_MENU = 0x12  # Alt key
VK_C = 0x43     # 'C' key
VK_V = 0x56     # 'V' key
KEYEVENTF_KEYUP = 0x0002

# Register Windows 10/11 Clipboard History exclusion formats
CF_CAN_INCLUDE_IN_HISTORY = user32.RegisterClipboardFormatW("CanIncludeInClipboardHistory")
CF_EXCLUDE_FROM_MONITOR = user32.RegisterClipboardFormatW("ExcludeClipboardContentFromMonitorProcessing")


class ClipboardSessionGuard:
    """
    Session-level guard that records the user's existing clipboard data
    before dictation starts, and ensures it is completely restored when
    dictation finishes. Prevents DIL DIL from ever corrupting or wiping
    out user clipboard data.
    """
    def __init__(self):
        self.original_text = Typer.get_clipboard_text()

    def restore(self):
        Typer.restore_clipboard(self.original_text)


class Typer:
    @staticmethod
    def get_clipboard_text():
        """Safely captures whatever text is currently on the Windows clipboard."""
        try:
            return pyperclip.paste()
        except Exception:
            return None

    @staticmethod
    def get_selected_text():
        """
        Attempts to copy the currently highlighted text to the clipboard by simulating Ctrl+C.
        Temporarily saves the clipboard state to restore it afterwards.
        """
        # Save current clipboard
        original_clipboard = Typer.get_clipboard_text()

        # Clear clipboard so we can tell if Ctrl+C actually did anything
        Typer.restore_clipboard("")

        # Release any modifiers
        user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
        user32.keybd_event(VK_SHIFT, 0, KEYEVENTF_KEYUP, 0)
        user32.keybd_event(VK_MENU, 0, KEYEVENTF_KEYUP, 0)
        time.sleep(0.008)

        # Simulate Ctrl+C
        user32.keybd_event(VK_CONTROL, 0, 0, 0)
        time.sleep(0.008)
        user32.keybd_event(VK_C, 0, 0, 0)
        time.sleep(0.008)
        user32.keybd_event(VK_C, 0, KEYEVENTF_KEYUP, 0)
        time.sleep(0.008)
        user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)

        # Wait for clipboard to populate
        time.sleep(0.05)

        selected_text = Typer.get_clipboard_text()

        # Restore clipboard
        Typer.restore_clipboard(original_clipboard)

        return selected_text if selected_text else ""

    @staticmethod
    def restore_clipboard(text):
        """Restores previously saved clipboard text, or clears it if it was empty."""
        try:
            if text is not None and text != "":
                pyperclip.copy(text)
            else:
                if user32.OpenClipboard(None):
                    user32.EmptyClipboard()
                    user32.CloseClipboard()
        except Exception:
            pass

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
    def paste_text(text: str, fallback_hwnd=None, preserve_clipboard: bool = True):
        """
        Pastes text directly at the user's active cursor.
        1. Backs up user's existing clipboard so it is NEVER lost.
        2. Sets Windows Clipboard History exclusion flags so Win+V is not polluted.
        3. Simulates Ctrl+V into the active target application.
        4. Restores the user's original clipboard immediately after pasting.
        """
        if not text:
            return

        original_clipboard = Typer.get_clipboard_text() if preserve_clipboard else None

        current_hwnd = Typer.get_foreground_window()
        my_pid = os.getpid()
        current_pid = Typer.get_window_pid(current_hwnd) if current_hwnd else None

        # Only switch focus if current foreground window is invalid or belongs to our own app
        if (not current_hwnd or current_pid == my_pid) and fallback_hwnd:
            fallback_pid = Typer.get_window_pid(fallback_hwnd)
            if fallback_pid and fallback_pid != my_pid:
                Typer.restore_focus(fallback_hwnd)
                time.sleep(0.04)

        # Copy text to clipboard with retries in case clipboard is momentarily locked
        for _ in range(3):
            try:
                pyperclip.copy(text)
                break
            except Exception:
                time.sleep(0.01)
        time.sleep(0.015)

        # Flag clipboard content so Windows 10/11 Clipboard History (Win+V) ignores temporary paste
        if CF_CAN_INCLUDE_IN_HISTORY:
            try:
                if user32.OpenClipboard(None):
                    kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
                    kernel32.GlobalLock.restype = ctypes.c_void_p
                    h_mem = kernel32.GlobalAlloc(0x0002, 4)  # GMEM_MOVEABLE, sizeof(DWORD)
                    if h_mem:
                        ptr = kernel32.GlobalLock(h_mem)
                        ctypes.memset(ptr, 0, 4)  # Set 0 (Do not include in history)
                        kernel32.GlobalUnlock(h_mem)
                        user32.SetClipboardData(CF_CAN_INCLUDE_IN_HISTORY, h_mem)
                    user32.CloseClipboard()
            except Exception:
                pass

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

        # Allow the receiving application to consume the clipboard data before restoring
        if preserve_clipboard:
            time.sleep(0.075)
            Typer.restore_clipboard(original_clipboard)
