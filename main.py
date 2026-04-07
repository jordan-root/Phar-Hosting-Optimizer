import os
import sys
import shutil
import ctypes
import subprocess
import threading
import customtkinter as ctk
from typing import Callable, Dict

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

def is_admin() -> bool:
    try: return ctypes.windll.shell32.IsUserAnAdmin()
    except: return False

class UltimateEngine:
    def __init__(self):
        appdata = os.environ.get("LOCALAPPDATA", "")
        userprofile = os.environ.get("USERPROFILE", "")
        
        self.targets = {
            "user_temp": os.environ.get("TEMP", ""),
            "win_temp": os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "Temp"),
            "prefetch": os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "Prefetch"),
            "downloads": os.path.join(userprofile, "Downloads"),
            "chrome_cache": os.path.join(appdata, r"Google\Chrome\User Data\Default\Cache"),
            "edge_cache": os.path.join(appdata, r"Microsoft\Edge\User Data\Default\Cache"),
        }
        self.browsers = ["chrome.exe", "msedge.exe", "firefox.exe"]

    def _kill_browsers(self):
        for proc in self.browsers:
            subprocess.run(f"taskkill /F /IM {proc} /T", shell=True, capture_output=True, creationflags=0x08000000)

    def _wipe(self, path: str) -> int:
        if not path or not os.path.exists(path): return 0
        count = 0
        with os.scandir(path) as it:
            for entry in it:
                try:
                    if entry.is_file(follow_symlinks=False):
                        os.chmod(entry.path, 0o777)
                        os.remove(entry.path)
                    else:
                        shutil.rmtree(entry.path, ignore_errors=True)
                    count += 1
                except: continue
        return count

    def run(self, config: Dict[str, bool], progress_cb: Callable, final_cb: Callable):
        try:
            total = 0
            if config.get("kill_proc"): self._kill_browsers()

            tasks = [k for k, v in config.items() if v and k != "kill_proc"]
            for i, key in enumerate(tasks):
                progress_cb((i+1)/len(tasks), f"Traitement : {key.upper()}")
                
                if key in self.targets:
                    total += self._wipe(self.targets[key])
                elif key == "dns_master":
                    # Flush DNS PC + Reset Winsock (Réseau complet)
                    cmds = ["ipconfig /flushdns", "ipconfig /registerdns", "netsh winsock reset"]
                    for c in cmds: subprocess.run(c, shell=True, creationflags=0x08000000)
                elif key == "bin":
                    ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 7)

            progress_cb(1.0, f"Succès : {total} éléments purgés")
            final_cb(True)
        except: final_cb(False)

class PharHostingApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Phar-Hosting Ultimate Optimizer")
        self.geometry("650x650")
        self.resizable(False, False)
        self.engine = UltimateEngine()
        self.vars = {}
        self._setup_ui()

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(self, text="PHAR-HOSTING", font=("Impact", 45), text_color="#1f6aa5").grid(row=0, pady=(20, 0))
        ctk.CTkLabel(self, text="ULTIMATE SYSTEM CLEANER", font=("Segoe UI", 12, "bold"), text_color="white").grid(row=1, pady=(0, 20))

        # Panel Options
        self.frame = ctk.CTkFrame(self, fg_color="#111111", corner_radius=15, border_width=1, border_color="#333")
        self.frame.grid(row=2, padx=30, pady=10, sticky="nsew")
        self.frame.grid_columnconfigure((0, 1), weight=1)

        options = [
            ("user_temp", "Cache Utilisateur"), ("win_temp", "Cache Windows"),
            ("prefetch", "Fichiers Prefetch"), ("downloads", "Téléchargements"),
            ("chrome_cache", "Cache Chrome"), ("edge_cache", "Cache Edge"),
            ("dns_master", "DNS & Network Reset"), ("bin", "Vider Corbeille")
        ]

        for i, (key, label) in enumerate(options):
            v = ctk.BooleanVar(value=True)
            self.vars[key] = v
            ctk.CTkSwitch(self.frame, text=label, variable=v, font=("Segoe UI", 12)).grid(row=i//2, column=i%2, padx=25, pady=18, sticky="w")

        # Force Option
        self.kill_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(self, text="Forcer la fermeture des navigateurs (Recommandé)", 
                        variable=self.kill_var, font=("Segoe UI", 11), text_color="#aaa").grid(row=3, pady=15)

        self.bar = ctk.CTkProgressBar(self, width=500, height=15, corner_radius=10)
        self.bar.grid(row=4, pady=(10, 5))
        self.bar.set(0)

        self.status = ctk.CTkLabel(self, text="Prêt pour le nettoyage complet", font=("Segoe UI", 13), text_color="gray")
        self.status.grid(row=5, pady=(0, 20))

        self.btn = ctk.CTkButton(self, text="LANCER L'OPTIMISATION FINALE", command=self._start,
                                 height=60, width=400, corner_radius=10, font=("Segoe UI", 16, "bold"),
                                 fg_color="#1f6aa5", hover_color="#144d75")
        self.btn.grid(row=6, pady=5)

        ctk.CTkLabel(self, text="Jordan Gréau Edition | Admin Mode: " + str(is_admin()).upper(), 
                    font=("Consolas", 10), text_color="#444").grid(row=7, pady=20)

    def _start(self):
        self.btn.configure(state="disabled", text="NETTOYAGE EN COURS...")
        cfg = {k: v.get() for k, v in self.vars.items()}
        cfg["kill_proc"] = self.kill_var.get()
        threading.Thread(target=self.engine.run, args=(cfg, self._upd, self._done), daemon=True).start()

    def _upd(self, p, m):
        self.after(0, lambda: (self.bar.set(p), self.status.configure(text=m, text_color="white")))

    def _done(self, ok):
        self.after(0, lambda: (self.btn.configure(state="normal", text="RECOMMENCER"),
                               self.status.configure(text_color="#00C851" if ok else "#ff4444")))

if __name__ == "__main__":
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    else:
        PharHostingApp().mainloop()