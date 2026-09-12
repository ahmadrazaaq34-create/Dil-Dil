import os
import sys
import ctypes

def update_desktop_shortcut():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ico_path = os.path.join(base_dir, "assets", "app_icon.ico")
    main_py = os.path.join(base_dir, "main.py")
    pythonw_exe = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    if not os.path.exists(pythonw_exe):
        pythonw_exe = sys.executable

    import win32com.client
    shell = win32com.client.Dispatch('WScript.Shell')
    desktop = shell.SpecialFolders('Desktop')
    shortcut_path = os.path.join(desktop, 'DIL DIL.lnk')
    shortcut = shell.CreateShortcut(shortcut_path)
    shortcut.TargetPath = pythonw_exe
    shortcut.Arguments = f'"{main_py}"'
    shortcut.WorkingDirectory = base_dir
    shortcut.IconLocation = f"{ico_path},0"
    shortcut.Description = "DIL DIL Voice Assistant (Pakistani Flag Edition)"
    shortcut.Save()
    print("Updated desktop shortcut:", shortcut_path)

    # Notify Windows Shell
    ctypes.windll.shell32.SHChangeNotify(0x08000000, 0, None, None)
    print("Notified Windows shell of icon update.")

if __name__ == "__main__":
    update_desktop_shortcut()
