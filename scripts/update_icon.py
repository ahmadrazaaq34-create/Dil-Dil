import os
import sys
import ctypes
from PIL import Image

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    png_path = os.path.join(base_dir, "assets", "icon.png")
    v2_ico = os.path.join(base_dir, "assets", "dil_dil_v2.ico")
    emblem_ico = os.path.join(base_dir, "assets", "dil_dil_emblem.ico")
    app_ico = os.path.join(base_dir, "assets", "app_icon.ico")

    img = Image.open(png_path).convert("RGBA")
    icon_sizes = [(16, 16), (20, 20), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(v2_ico, format="ICO", sizes=icon_sizes)
    img.save(emblem_ico, format="ICO", sizes=icon_sizes)
    img.save(app_ico, format="ICO", sizes=icon_sizes)
    print("Generated multi-res ICOs:", v2_ico)

    import win32com.client
    shell = win32com.client.Dispatch('WScript.Shell')
    desktop = shell.SpecialFolders('Desktop')
    shortcut_path = os.path.join(desktop, 'DIL DIL.lnk')

    if os.path.exists(shortcut_path):
        try:
            os.remove(shortcut_path)
        except Exception:
            pass

    shortcut = shell.CreateShortcut(shortcut_path)
    pythonw_exe = sys.executable.replace('python.exe', 'pythonw.exe')
    main_py = os.path.join(base_dir, 'main.py')
    shortcut.TargetPath = pythonw_exe
    shortcut.Arguments = f'"{main_py}"'
    shortcut.WorkingDirectory = base_dir
    shortcut.IconLocation = f"{v2_ico},0"
    shortcut.Description = "DIL DIL Voice Assistant (Pakistani Flag Edition)"
    shortcut.Save()
    print("Updated Desktop shortcut to point to dil_dil_v2.ico:", shortcut_path)

    ctypes.windll.shell32.SHChangeNotify(0x08000000, 0x1000, None, None)
    print("Flushed Windows Explorer icon cache.")

if __name__ == "__main__":
    main()
