"""
gui.py
Interfaz gráfica simple para el Reddit Story Video Bot.
Usa Tkinter (viene con Python, sin dependencias extra).
"""

import json
import logging
import os
import subprocess
import sys
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk

# Asegurar que el directorio raíz esté en el path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from config import (
    BASE_DIR,
    STORIES_DIR,
    USED_STORIES_DIR,
    AUDIO_DIR,
    GAMEPLAY_DIR,
    OUTPUT_DIR,
    USED_GAMEPLAY_DIR,
    LOG_DIR,
    TTS_VOICE,
    TTS_RATE,
    TTS_PITCH,
    PUBLISH_PLATFORM,
    VIDEO_TITLE_TEMPLATE,
    save_env_config,
)


# ============================================================
#  VENTANA PRINCIPAL
# ============================================================

class RedditBotGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Reddit Story Video Bot")
        self.root.geometry("900x650")
        self.root.minsize(800, 550)

        # Icono de la ventana (opcional, un emoji no funciona en todas las versiones)
        # self.root.iconbitmap(...)

        # Variable para controlar la ejecución
        self.process_running = False
        self.process = None

        # --- Barra de menú ---
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Salir", command=self.root.quit)
        menubar.add_cascade(label="Archivo", menu=file_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Acerca de", command=self.show_about)
        menubar.add_cascade(label="Ayuda", menu=help_menu)

        # --- Pestañas ---
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # Crear pestañas
        self.tab_stories = ttk.Frame(self.notebook)
        self.tab_config = ttk.Frame(self.notebook)
        self.tab_run = ttk.Frame(self.notebook)
        self.tab_files = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_stories, text="  📖 Historias  ")
        self.notebook.add(self.tab_config, text="  ⚙️ Configuración  ")
        self.notebook.add(self.tab_run, text="  ▶️ Ejecución  ")
        self.notebook.add(self.tab_files, text="  📁 Archivos  ")

        # Construir cada pestaña
        self.build_stories_tab()
        self.build_config_tab()
        self.build_run_tab()
        self.build_files_tab()

        # Refrescar listas al inicio
        self.refresh_story_lists()

        # Cerrar bien al salir
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    # ========================================================
    #  PESTAÑA: HISTORIAS
    # ========================================================

    def build_stories_tab(self):
        # Frame superior con botones
        btn_frame = ttk.Frame(self.tab_stories)
        btn_frame.pack(fill="x", pady=(10, 5), padx=10)

        ttk.Button(btn_frame, text="➕ Nueva historia", command=self.new_story).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="✏️ Editar seleccionada", command=self.edit_story).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="🗑️ Eliminar seleccionada", command=self.delete_story).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="🔄 Recargar", command=self.refresh_story_lists).pack(side="right", padx=2)

        # Panel con dos listas: Pendientes y Usadas
        paned = ttk.PanedWindow(self.tab_stories, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # --- Lista de pendientes ---
        pending_frame = ttk.LabelFrame(paned, text="📥 Pendientes")
        self.pending_listbox = tk.Listbox(pending_frame, font=("Consolas", 10))
        self.pending_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        self.pending_listbox.bind("<Double-Button-1>", lambda e: self.edit_story())
        scroll_p = ttk.Scrollbar(pending_frame, orient="vertical", command=self.pending_listbox.yview)
        scroll_p.pack(side="right", fill="y")
        self.pending_listbox.config(yscrollcommand=scroll_p.set)
        paned.add(pending_frame, weight=1)

        # --- Lista de usadas ---
        used_frame = ttk.LabelFrame(paned, text="✅ Usadas")
        self.used_listbox = tk.Listbox(used_frame, font=("Consolas", 10), fg="gray")
        self.used_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        scroll_u = ttk.Scrollbar(used_frame, orient="vertical", command=self.used_listbox.yview)
        scroll_u.pack(side="right", fill="y")
        self.used_listbox.config(yscrollcommand=scroll_u.set)
        paned.add(used_frame, weight=1)

        # Botón para mover de usadas a pendientes (reprocesar)
        ttk.Button(
            self.tab_stories,
            text="⬆️ Mover a pendientes (reprocesar)",
            command=self.restore_story,
        ).pack(pady=(0, 10))

    def refresh_story_lists(self):
        """Actualiza ambas listas de historias."""
        self.pending_listbox.delete(0, tk.END)
        self.used_listbox.delete(0, tk.END)

        # Pendientes
        if STORIES_DIR.exists():
            for f in sorted(STORIES_DIR.glob("*.txt")):
                self.pending_listbox.insert(tk.END, f.name)

        # Usadas
        if USED_STORIES_DIR.exists():
            for f in sorted(USED_STORIES_DIR.glob("*.txt")):
                self.used_listbox.insert(tk.END, f.name)

        if self.pending_listbox.size() == 0:
            self.pending_listbox.insert(tk.END, "(No hay historias pendientes)")

        if self.used_listbox.size() == 0:
            self.used_listbox.insert(tk.END, "(No hay historias usadas)")

    def get_selected_story_path(self, listbox) -> Path | None:
        """Devuelve el Path del archivo seleccionado en un listbox, o None."""
        sel = listbox.curselection()
        if not sel:
            messagebox.showwarning("Seleccionar", "Selecciona una historia de la lista.")
            return None
        filename = listbox.get(sel[0])
        # Comprobar primero en pendientes, luego en usadas
        for folder in (STORIES_DIR, USED_STORIES_DIR):
            p = folder / filename
            if p.exists():
                return p
        return None

    def new_story(self):
        """Abre un editor para crear una nueva historia."""
        editor = StoryEditor(self.root, mode="new")
        self.root.wait_window(editor.window)
        self.refresh_story_lists()

    def edit_story(self):
        """Abre la historia seleccionada en el editor."""
        path = self.get_selected_story_path(self.pending_listbox)
        if path is None:
            path = self.get_selected_story_path(self.used_listbox)
        if path is None:
            return
        editor = StoryEditor(self.root, mode="edit", filepath=path)
        self.root.wait_window(editor.window)
        self.refresh_story_lists()

    def delete_story(self):
        """Elimina la historia seleccionada."""
        path = self.get_selected_story_path(self.pending_listbox)
        if path is None:
            path = self.get_selected_story_path(self.used_listbox)
        if path is None:
            return
        if messagebox.askyesno("Confirmar", f"¿Eliminar '{path.name}' definitivamente?"):
            path.unlink()
            self.refresh_story_lists()

    def restore_story(self):
        """Mueve una historia de usadas a pendientes para reprocesarla."""
        sel = self.used_listbox.curselection()
        if not sel:
            messagebox.showwarning("Seleccionar", "Selecciona una historia de la lista de usadas.")
            return
        filename = self.used_listbox.get(sel[0])
        src = USED_STORIES_DIR / filename
        dst = STORIES_DIR / filename
        if src.exists():
            # También limpiar su ID de used_posts.json para que se pueda reprocesar
            self._remove_from_used_posts(filename)
            src.rename(dst)
            self.refresh_story_lists()
            messagebox.showinfo("Hecho", f"'{filename}' movido a pendientes.")

    def _remove_from_used_posts(self, story_filename: str):
        """Elimina el ID de la historia de used_posts.json para permitir reprocesarla."""
        used_posts_file = BASE_DIR / "data" / "used_posts.json"
        story_id = Path(story_filename).stem
        if used_posts_file.exists():
            try:
                data = json.loads(used_posts_file.read_text(encoding="utf-8"))
                ids = set(data.get("used_ids", []))
                ids.discard(story_id)
                data["used_ids"] = sorted(list(ids))
                used_posts_file.write_text(json.dumps(data, indent=4, ensure_ascii=False), encoding="utf-8")
            except Exception:
                pass

    # ========================================================
    #  PESTAÑA: CONFIGURACIÓN
    # ========================================================

    def build_config_tab(self):
        # Usar un Canvas con scroll por si hay muchas opciones
        canvas = tk.Canvas(self.tab_config, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.tab_config, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind de la rueda del ratón
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # --- TTS ---
        tts_frame = ttk.LabelFrame(scroll_frame, text="🗣️ Texto a Voz (TTS)", padding=10)
        tts_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(tts_frame, text="Voz:").grid(row=0, column=0, sticky="w", pady=2)
        self.tts_voice_var = tk.StringVar(value=TTS_VOICE)
        voice_combo = ttk.Combobox(tts_frame, textvariable=self.tts_voice_var, width=30, state="readonly")
        voice_combo["values"] = [
            "es-ES-AlvaroNeural",
            "es-ES-ElviraNeural",
            "es-MX-DaliaNeural",
            "es-MX-JorgeNeural",
            "es-AR-ElenaNeural",
            "es-CL-CatalinaNeural",
        ]
        voice_combo.grid(row=0, column=1, sticky="w", pady=2)

        ttk.Label(tts_frame, text="Velocidad:").grid(row=1, column=0, sticky="w", pady=2)
        self.tts_rate_var = tk.StringVar(value=TTS_RATE)
        rate_combo = ttk.Combobox(tts_frame, textvariable=self.tts_rate_var, width=10, state="readonly")
        rate_combo["values"] = ["-20%", "-10%", "+0%", "+10%", "+20%"]
        rate_combo.grid(row=1, column=1, sticky="w", pady=2)

        ttk.Label(tts_frame, text="Tono:").grid(row=2, column=0, sticky="w", pady=2)
        self.tts_pitch_var = tk.StringVar(value=TTS_PITCH)
        pitch_combo = ttk.Combobox(tts_frame, textvariable=self.tts_pitch_var, width=10, state="readonly")
        pitch_combo["values"] = ["-20Hz", "-10Hz", "+0Hz", "+10Hz", "+20Hz"]
        pitch_combo.grid(row=2, column=1, sticky="w", pady=2)

        # --- Publicación ---
        pub_frame = ttk.LabelFrame(scroll_frame, text="📤 Publicación", padding=10)
        pub_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(pub_frame, text="Plataforma:").grid(row=0, column=0, sticky="w", pady=2)
        self.publish_platform_var = tk.StringVar(value=PUBLISH_PLATFORM)
        pub_combo = ttk.Combobox(pub_frame, textvariable=self.publish_platform_var, width=15, state="readonly")
        pub_combo["values"] = ["local", "youtube"]
        pub_combo.grid(row=0, column=1, sticky="w", pady=2)

        ttk.Label(pub_frame, text="Plantilla título:").grid(row=1, column=0, sticky="w", pady=2)
        self.title_template_var = tk.StringVar(value=VIDEO_TITLE_TEMPLATE)
        ttk.Entry(pub_frame, textvariable=self.title_template_var, width=50).grid(row=1, column=1, sticky="w", pady=2)

        ttk.Label(pub_frame, text="Usa {title} como marcador de posición del título de la historia.").grid(
            row=2, column=0, columnspan=2, sticky="w", pady=2
        )

        # --- Botón guardar ---
        ttk.Button(
            scroll_frame,
            text="💾 Guardar configuración",
            command=self.save_config,
        ).pack(pady=15)

    def save_config(self):
        """Guarda la configuración en el .env y recarga las variables."""
        updates = {
            "TTS_VOICE": self.tts_voice_var.get(),
            "TTS_RATE": self.tts_rate_var.get(),
            "TTS_PITCH": self.tts_pitch_var.get(),
            "PUBLISH_PLATFORM": self.publish_platform_var.get(),
            "VIDEO_TITLE_TEMPLATE": self.title_template_var.get(),
        }
        # Si la plataforma es local, no hace falta el título de YouTube, pero lo guardamos igual
        try:
            save_env_config(updates)
            messagebox.showinfo("Guardado", "Configuración guardada correctamente en .env")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar: {e}")

    # ========================================================
    #  PESTAÑA: EJECUCIÓN
    # ========================================================

    def build_run_tab(self):
        # Frame superior: botón + barra de progreso
        top_frame = ttk.Frame(self.tab_run)
        top_frame.pack(fill="x", pady=(10, 5), padx=10)

        self.run_btn = ttk.Button(
            top_frame,
            text="▶️ Generar vídeo ahora",
            command=self.run_pipeline,
        )
        self.run_btn.pack(side="left", padx=2)

        self.cancel_btn = ttk.Button(
            top_frame,
            text="⏹️ Cancelar",
            command=self.cancel_pipeline,
            state="disabled",
        )
        self.cancel_btn.pack(side="left", padx=2)

        self.progress = ttk.Progressbar(top_frame, mode="determinate", value=0)
        self.progress.pack(fill="x", expand=True, side="right", padx=(10, 0))

        self.status_label = ttk.Label(top_frame, text="Estado: Esperando...", foreground="gray")
        self.status_label.pack(side="right", padx=5)

        # Área de logs en tiempo real
        log_frame = ttk.LabelFrame(self.tab_run, text="📋 Logs en tiempo real")
        log_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            font=("Consolas", 9),
            wrap="word",
            state="disabled",
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="white",
        )
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)

        # Configurar tags de color para logs
        self.log_text.tag_config("INFO", foreground="#6a9955")
        self.log_text.tag_config("WARNING", foreground="#ce9178")
        self.log_text.tag_config("ERROR", foreground="#f44747")
        self.log_text.tag_config("DEBUG", foreground="#569cd6")
        self.log_text.tag_config("BOLD", font=("Consolas", 9, "bold"))

    def run_pipeline(self):
        """Lanza main.py en un hilo separado y captura su salida."""
        if self.process_running:
            return

        self.process_running = True
        self.run_btn.config(state="disabled")
        self.cancel_btn.config(state="normal")
        self.progress["value"] = 0
        self.status_label.config(text="Estado: Ejecutando...", foreground="blue")
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state="disabled")

        hilo = threading.Thread(target=self._run_pipeline_thread, daemon=True)
        hilo.start()

    def _run_pipeline_thread(self):
        """Ejecuta main.py en un subproceso y captura stdout/stderr."""
        python_exe = BASE_DIR / ".venv" / "Scripts" / "python.exe"
        if not python_exe.exists():
            python_exe = sys.executable

        main_script = BASE_DIR / "main.py"

        try:
            self.process = subprocess.Popen(
                [str(python_exe), str(main_script)],
                cwd=str(BASE_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                bufsize=1,
            )

            for line in iter(self.process.stdout.readline, ""):
                if not line:
                    break
                self._append_log(line.rstrip())
                # Actualizar barra de progreso según palabras clave en el log
                self._update_progress_from_log(line)

            self.process.wait()

            if self.process.returncode == 0:
                self._append_log("✅ Pipeline completado con éxito.")
                self.status_label.config(text="Estado: Completado ✅", foreground="green")
            else:
                self._append_log(f"❌ Pipeline terminó con código de error {self.process.returncode}.")
                self.status_label.config(text="Estado: Falló ❌", foreground="red")

        except Exception as e:
            self._append_log(f"❌ Error al ejecutar el pipeline: {e}")
            self.status_label.config(text="Estado: Error ❌", foreground="red")
        finally:
            self.process_running = False
            self.root.after(0, self._reset_ui)

    def _append_log(self, text: str):
        """Añade una línea al log con colores según el nivel."""
        def do_append():
            self.log_text.config(state="normal")
            # Determinar tag según el texto
            tag = None
            if text.startswith("202"):
                # Es una línea de log con timestamp
                if "[ERROR]" in text:
                    tag = "ERROR"
                elif "[WARNING]" in text or "[WARN]" in text:
                    tag = "WARNING"
                elif "[INFO]" in text:
                    tag = "INFO"
                elif "[DEBUG]" in text:
                    tag = "DEBUG"
            elif text.startswith("✅") or text.startswith("🎬"):
                tag = "BOLD"

            if tag:
                self.log_text.insert(tk.END, text + "\n", tag)
            else:
                self.log_text.insert(tk.END, text + "\n")

            self.log_text.see(tk.END)
            self.log_text.config(state="disabled")

        self.root.after(0, do_append)

    def _update_progress_from_log(self, line: str):
        """Actualiza la barra de progreso según la fase que aparece en el log."""
        if "[0/4]" in line:
            self._set_progress(10)
        elif "[1/4]" in line:
            self._set_progress(25)
        elif "[2/4]" in line:
            self._set_progress(50)
        elif "[3/4]" in line:
            self._set_progress(75)
        elif "[4/4]" in line:
            self._set_progress(90)
        elif "completado con éxito" in line.lower() or "Vídeo generado" in line:
            self._set_progress(100)

    def _set_progress(self, value: int):
        self.root.after(0, lambda: self.progress.configure(value=value))

    def _reset_ui(self):
        self.run_btn.config(state="normal")
        self.cancel_btn.config(state="disabled")

    def cancel_pipeline(self):
        if self.process and self.process_running:
            self.process.terminate()
            self._append_log("⏹️ Pipeline cancelado por el usuario.")
            self.status_label.config(text="Estado: Cancelado ⏹️", foreground="orange")
            self.process_running = False
            self._reset_ui()

    # ========================================================
    #  PESTAÑA: ARCHIVOS
    # ========================================================

    def build_files_tab(self):
        frame = ttk.Frame(self.tab_files)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        ttk.Label(frame, text="Accesos rápidos a carpetas del proyecto:", font=("Segoe UI", 11)).pack(anchor="w", pady=(0, 10))

        folders = [
            ("📖 Historias pendientes", STORIES_DIR),
            ("✅ Historias usadas", USED_STORIES_DIR),
            ("🎬 Gameplays", GAMEPLAY_DIR),
            ("🎥 Vídeos generados (output)", OUTPUT_DIR),
            ("🔊 Audios generados", AUDIO_DIR),
            ("📦 Gameplays usados", USED_GAMEPLAY_DIR),
            ("📋 Logs", LOG_DIR),
            ("📁 Raíz del proyecto", BASE_DIR),
        ]

        for label, path in folders:
            btn_frame = ttk.Frame(frame)
            btn_frame.pack(fill="x", pady=2)

            ttk.Label(btn_frame, text=label, width=30, anchor="w").pack(side="left")
            ttk.Label(btn_frame, text=str(path), foreground="gray").pack(side="left", fill="x", expand=True, padx=5)
            ttk.Button(
                btn_frame,
                text="📂 Abrir",
                command=lambda p=path: self.open_folder(p),
                width=8,
            ).pack(side="right")

    def open_folder(self, path: Path):
        """Abre la carpeta en el explorador de archivos."""
        if path.exists():
            os.startfile(str(path))
        else:
            messagebox.showerror("Error", f"La carpeta no existe:\n{path}")

    # ========================================================
    #  MÉTODOS AUXILIARES
    # ========================================================

    def show_about(self):
        messagebox.showinfo(
            "Acerca de",
            "Reddit Story Video Bot\n\n"
            "Genera vídeos verticales estilo TikTok/Shorts\n"
            "con historias narradas y gameplay de fondo.\n\n"
            "Versión 1.0",
        )

    def on_closing(self):
        if self.process_running:
            if messagebox.askyesno("Confirmar", "Hay un pipeline en ejecución. ¿Detenerlo y salir?"):
                self.cancel_pipeline()
            else:
                return
        self.root.destroy()


# ============================================================
#  VENTANA EDITOR DE HISTORIAS
# ============================================================

class StoryEditor:
    def __init__(self, parent, mode="new", filepath: Path = None):
        self.parent = parent
        self.mode = mode
        self.filepath = filepath

        self.window = tk.Toplevel(parent)
        self.window.title("Editar historia" if mode == "edit" else "Nueva historia")
        self.window.geometry("600x500")
        self.window.minsize(400, 300)
        self.window.transient(parent)
        self.window.grab_set()

        ttk.Label(self.window, text="Título:").pack(anchor="w", padx=10, pady=(10, 2))
        self.title_entry = ttk.Entry(self.window, font=("Segoe UI", 11))
        self.title_entry.pack(fill="x", padx=10, pady=(0, 5))

        ttk.Label(self.window, text="Cuerpo de la historia:").pack(anchor="w", padx=10, pady=(5, 2))
        self.body_text = scrolledtext.ScrolledText(
            self.window,
            font=("Segoe UI", 10),
            wrap="word",
            height=15,
        )
        self.body_text.pack(fill="both", expand=True, padx=10, pady=(0, 5))

        # Botones
        btn_frame = ttk.Frame(self.window)
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))

        ttk.Button(btn_frame, text="💾 Guardar", command=self.save).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="❌ Cancelar", command=self.window.destroy).pack(side="left", padx=2)

        # Si es edición, cargar contenido
        if mode == "edit" and filepath and filepath.exists():
            self.load_content(filepath)

    def load_content(self, path: Path):
        """Carga el contenido de un archivo .txt en el editor."""
        content = path.read_text(encoding="utf-8").strip()
        lines = content.splitlines()
        if lines:
            self.title_entry.delete(0, tk.END)
            self.title_entry.insert(0, lines[0].strip())
            resto = lines[1:]
            # Saltar línea en blanco si es separador
            if resto and resto[0].strip() == "":
                resto = resto[1:]
            self.body_text.delete(1.0, tk.END)
            self.body_text.insert(1.0, "\n".join(resto).strip())

    def save(self):
        """Guarda el contenido como .txt en STORIES_DIR."""
        title = self.title_entry.get().strip()
        body = self.body_text.get(1.0, tk.END).strip()

        if not title:
            messagebox.showwarning("Validación", "El título no puede estar vacío.")
            return
        if not body:
            messagebox.showwarning("Validación", "El cuerpo de la historia no puede estar vacío.")
            return

        # Si es nueva, generar nombre de archivo a partir del título
        if self.mode == "new":
            # Nombre seguro para archivo
            safe_name = "".join(c if c.isalnum() or c in " _-" else "" for c in title)
            safe_name = safe_name.strip().replace(" ", "_")[:80]
            if not safe_name:
                safe_name = "historia"
            # Asegurar que no exista
            counter = 0
            filename = f"{safe_name}.txt"
            while (STORIES_DIR / filename).exists():
                counter += 1
                filename = f"{safe_name}_{counter}.txt"
            self.filepath = STORIES_DIR / filename
        else:
            # En edición, si se cambió el título, renombrar el archivo
            if self.filepath and self.filepath.exists():
                old_title = self.filepath.stem
                new_safe = "".join(c if c.isalnum() or c in " _-" else "" for c in title)
                new_safe = new_safe.strip().replace(" ", "_")[:80]
                if new_safe and new_safe != self.filepath.stem:
                    new_path = self.filepath.with_stem(new_safe)
                    if not new_path.exists():
                        self.filepath.rename(new_path)
                        self.filepath = new_path

        # Escribir archivo con formato título + línea en blanco + cuerpo
        content = f"{title}\n\n{body}\n"
        self.filepath.write_text(content, encoding="utf-8")

        messagebox.showinfo("Guardado", f"Historia guardada:\n{self.filepath.name}")
        self.window.destroy()


# ============================================================
#  PUNTO DE ENTRADA
# ============================================================

def main():
    root = tk.Tk()
    app = RedditBotGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()