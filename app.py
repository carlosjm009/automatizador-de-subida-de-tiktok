import json
import os
import shutil
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

ROOT = Path(__file__).resolve().parent
CHANNELS_FILE = ROOT / "data" / "channels.txt"
OUTPUT_DIR = ROOT / "assets" / "output"
GAMEPLAY_DIR = ROOT / "assets" / "gameplay"
USED_GAMEPLAY_DIR = ROOT / "assets" / "used_gameplays"
STATUS_FILE = ROOT / "data" / "run_status.json"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class RedditBotGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Reddit Story Bot Dashboard")
        self.geometry("1100x750")
        self.minsize(1000, 700)

        self.process = None
        self.log_buffer = []
        self.generation_running = False

        self.create_ui()
        self.refresh_status()

    def create_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self)
        header.grid(row=0, column=0, padx=16, pady=16, sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        title_label = ctk.CTkLabel(header, text="Reddit Story Bot", font=ctk.CTkFont(size=24, weight="bold"))
        title_label.grid(row=0, column=0, padx=16, pady=16, sticky="w")

        self.generate_btn = ctk.CTkButton(header, text="Generar Nuevo Vídeo", command=self.start_generation, height=40)
        self.generate_btn.grid(row=0, column=1, padx=16, pady=16, sticky="e")

        status_frame = ctk.CTkFrame(header)
        status_frame.grid(row=1, column=0, columnspan=2, padx=16, pady=(0, 16), sticky="ew")
        status_frame.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(status_frame, text="Estado: listo", anchor="w")
        self.status_label.grid(row=0, column=0, padx=12, pady=(10, 4), sticky="w")

        self.progress_bar = ctk.CTkProgressBar(status_frame, width=300)
        self.progress_bar.grid(row=1, column=0, padx=12, pady=(0, 10), sticky="w")
        self.progress_bar.set(0)

        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="nsew")
        self.tabview.add("Dashboard")
        self.tabview.add("Canales")
        self.tabview.add("Biblioteca")

        self.build_dashboard_tab()
        self.build_channels_tab()
        self.build_library_tab()

    def build_dashboard_tab(self):
        frame = self.tabview.tab("Dashboard")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(2, weight=1)

        status_frame = ctk.CTkFrame(frame)
        status_frame.grid(row=0, column=0, padx=16, pady=16, sticky="ew")
        status_frame.grid_columnconfigure(0, weight=1)
        status_frame.grid_columnconfigure(1, weight=1)

        self.status_gameplays = ctk.CTkLabel(status_frame, text="🎮 Gameplays disponibles: 0", font=ctk.CTkFont(size=14, weight="bold"))
        self.status_gameplays.grid(row=0, column=0, padx=12, pady=10, sticky="w")

        self.status_histories = ctk.CTkLabel(status_frame, text="📚 Historias procesadas: 0", font=ctk.CTkFont(size=14, weight="bold"))
        self.status_histories.grid(row=0, column=1, padx=12, pady=10, sticky="w")

        self.status_tools = ctk.CTkLabel(status_frame, text="🔧 Estado del entorno: comprobando...", font=ctk.CTkFont(size=14, weight="bold"))
        self.status_tools.grid(row=1, column=0, columnspan=2, padx=12, pady=10, sticky="w")

        log_box = ctk.CTkScrollableFrame(frame, height=420)
        log_box.grid(row=2, column=0, padx=16, pady=(0, 16), sticky="nsew")
        log_box.grid_columnconfigure(0, weight=1)
        self.log_text = ctk.CTkTextbox(log_box, width=1, height=420)
        self.log_text.grid(row=0, column=0, padx=12, pady=12, sticky="nsew")
        self.log_text.insert("0.0", "Esperando órdenes...")
        self.log_text.configure(state="disabled")

    def build_channels_tab(self):
        frame = self.tabview.tab("Canales")
        frame.grid_columnconfigure(0, weight=1)

        instructions = ctk.CTkLabel(frame, text="Añade o edita los enlaces de canales de YouTube usados para descargar gameplays.", justify="left")
        instructions.grid(row=0, column=0, padx=16, pady=(16, 10), sticky="w")

        self.channels_text = ctk.CTkTextbox(frame, height=420)
        self.channels_text.grid(row=1, column=0, padx=16, pady=(0, 12), sticky="nsew")
        self.load_channels()

        buttons = ctk.CTkFrame(frame)
        buttons.grid(row=2, column=0, padx=16, pady=(0, 16), sticky="e")
        ctk.CTkButton(buttons, text="Guardar Cambios", command=self.save_channels).grid(row=0, column=0, padx=8)
        ctk.CTkButton(buttons, text="Recargar", command=self.load_channels).grid(row=0, column=1, padx=8)

    def build_library_tab(self):
        frame = self.tabview.tab("Biblioteca")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        toolbar = ctk.CTkFrame(frame)
        toolbar.grid(row=0, column=0, padx=16, pady=16, sticky="ew")
        ctk.CTkButton(toolbar, text="Abrir Carpeta de Salida", command=self.open_output_folder).grid(row=0, column=0, padx=8, pady=8)
        ctk.CTkButton(toolbar, text="Actualizar Lista", command=self.refresh_library).grid(row=0, column=1, padx=8, pady=8)
        ctk.CTkButton(toolbar, text="Eliminar Antiguos", command=self.delete_old_videos).grid(row=0, column=2, padx=8, pady=8)

        self.library_list = ctk.CTkScrollableFrame(frame, height=480)
        self.library_list.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="nsew")
        self.library_list.grid_columnconfigure(0, weight=1)
        self.refresh_library()

    def load_channels(self):
        if CHANNELS_FILE.exists():
            text = CHANNELS_FILE.read_text(encoding="utf-8")
        else:
            text = ""
        self.channels_text.delete("0.0", tk.END)
        self.channels_text.insert("0.0", text)

    def save_channels(self):
        CHANNELS_FILE.parent.mkdir(parents=True, exist_ok=True)
        CHANNELS_FILE.write_text(self.channels_text.get("0.0", tk.END), encoding="utf-8")
        messagebox.showinfo("Listo", "Se han guardado los canales correctamente.")

    def refresh_status(self):
        gameplay_files = [p for p in GAMEPLAY_DIR.iterdir() if p.is_file() and p.suffix.lower() in {".mp4", ".mov", ".avi", ".webm"}]
        self.status_gameplays.configure(text=f"🎮 Gameplays disponibles: {len(gameplay_files)}")

        used_posts_file = ROOT / "data" / "used_posts.json"
        count = 0
        if used_posts_file.exists():
            try:
                data = used_posts_file.read_text(encoding="utf-8")
                count = len(json.loads(data).get("used_ids", []))
            except Exception:
                count = 0
        self.status_histories.configure(text=f"📚 Historias procesadas: {count}")

        status_message = "Estado: listo"
        progress_value = 0.0
        if STATUS_FILE.exists():
            try:
                status_data = json.loads(STATUS_FILE.read_text(encoding="utf-8"))
                status = status_data.get("status", "idle")
                stage = status_data.get("stage", "idle")
                message = status_data.get("message", "Esperando órdenes...")
                progress_value = float(status_data.get("progress", 0.0) or 0.0)
                status_message = f"Estado: {message}"
                if status == "running":
                    status_message = f"Estado: {message}"
                elif status == "completed":
                    status_message = "Estado: proceso finalizado"
                elif status == "failed":
                    status_message = f"Estado: error — {message}"
                else:
                    status_message = "Estado: listo"
            except Exception:
                status_message = "Estado: listo"

        self.status_label.configure(text=status_message)
        self.progress_bar.set(progress_value)

        self.update_tool_status()

    def update_tool_status(self):
        tools_status = []
        missing_tools = []
        ffmpeg_ok = shutil.which("ffmpeg") is not None
        imagemagick_ok = False
        for candidate in [
            Path(r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"),
            Path(r"C:\Program Files\ImageMagick\magick.exe"),
        ]:
            if candidate.exists():
                imagemagick_ok = True
                break

        if ffmpeg_ok:
            tools_status.append("ffmpeg OK")
        else:
            tools_status.append("ffmpeg NO encontrado")
            missing_tools.append("ffmpeg")

        if imagemagick_ok:
            tools_status.append("ImageMagick OK")
        else:
            tools_status.append("ImageMagick NO encontrado")
            missing_tools.append("ImageMagick")

        if missing_tools:
            self.status_tools.configure(text=f"🔧 Faltan: {', '.join(missing_tools)}")
        else:
            self.status_tools.configure(text="🔧 Todas las herramientas necesarias están instaladas")

    def refresh_library(self):
        for widget in self.library_list.winfo_children():
            widget.destroy()

        if not OUTPUT_DIR.exists():
            ctk.CTkLabel(self.library_list, text="No hay vídeos aún.").grid(row=0, column=0, padx=12, pady=12, sticky="w")
            return

        videos = sorted([p for p in OUTPUT_DIR.iterdir() if p.is_file() and p.suffix.lower() == ".mp4"])
        if not videos:
            ctk.CTkLabel(self.library_list, text="No hay vídeos aún.").grid(row=0, column=0, padx=12, pady=12, sticky="w")
            return

        for idx, video in enumerate(videos):
            row = ctk.CTkFrame(self.library_list)
            row.grid(row=idx, column=0, padx=8, pady=6, sticky="ew")
            row.grid_columnconfigure(1, weight=1)
            ctk.CTkLabel(row, text=video.name, anchor="w").grid(row=0, column=0, padx=8, pady=6, sticky="w")
            ctk.CTkButton(row, text="Abrir", command=lambda p=str(video): self.open_file(p)).grid(row=0, column=1, padx=4)
            ctk.CTkButton(row, text="Eliminar", command=lambda p=str(video): self.delete_video(p)).grid(row=0, column=2, padx=4)

    def open_output_folder(self):
        try:
            os.startfile(str(OUTPUT_DIR))
        except AttributeError:
            subprocess.run(["explorer", str(OUTPUT_DIR)], check=False)

    def open_file(self, path):
        try:
            os.startfile(path)
        except AttributeError:
            subprocess.run(["explorer", path], check=False)

    def delete_video(self, path):
        try:
            os.remove(path)
            self.refresh_library()
            messagebox.showinfo("Listo", "Vídeo eliminado.")
        except Exception as exc:
            messagebox.showerror("Error", f"No se pudo eliminar: {exc}")

    def delete_old_videos(self):
        try:
            for file in OUTPUT_DIR.glob("*.mp4"):
                file.unlink()
            self.refresh_library()
            messagebox.showinfo("Listo", "Se han eliminado los vídeos de salida.")
        except Exception as exc:
            messagebox.showerror("Error", f"No se pudo limpiar: {exc}")

    def start_generation(self):
        self.generate_btn.configure(state="disabled", text="Generando...")
        self.generation_running = True
        self.refresh_status()
        self.after(1000, self.refresh_live_status)
        threading.Thread(target=self.run_generation, daemon=True).start()

    def refresh_live_status(self):
        if not self.generation_running:
            return
        self.refresh_status()
        self.after(1000, self.refresh_live_status)

    def run_generation(self):
        self.append_log("🚀 Iniciando generación de vídeo...")
        try:
            completed = subprocess.run([sys.executable, str(ROOT / "run.py")], cwd=ROOT, capture_output=True, text=True, timeout=None)
            output = completed.stdout + completed.stderr
            if output:
                self.append_log(output)
            if completed.returncode == 0:
                self.append_log("✅ Proceso finalizado correctamente.")
            else:
                self.append_log(f"❌ Proceso finalizado con código {completed.returncode}.")
        except Exception as exc:
            self.append_log(f"❌ Error al ejecutar el proceso: {exc}")
        finally:
            self.generation_running = False
            self.generate_btn.configure(state="normal", text="Generar Nuevo Vídeo")
            self.refresh_status()
            self.refresh_library()

    def append_log(self, message):
        self.log_buffer.append(message)
        if len(self.log_buffer) > 80:
            self.log_buffer = self.log_buffer[-80:]
        text = "\n".join(self.log_buffer)
        self.log_text.configure(state="normal")
        self.log_text.delete("0.0", tk.END)
        self.log_text.insert("0.0", text)
        self.log_text.configure(state="disabled")


if __name__ == "__main__":
    app = RedditBotGUI()
    app.mainloop()
