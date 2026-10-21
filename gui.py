"""
gui.py
Interfaz gráfica simple para el Reddit Story Video Bot.
Usa Tkinter (viene con Python, sin dependencias extra).
"""

import json  # Importa `json` para utilizarlo en este archivo.
import logging  # Importa `logging` para utilizarlo en este archivo.
import os  # Importa `os` para utilizarlo en este archivo.
import subprocess  # Importa `subprocess` para utilizarlo en este archivo.
import sys  # Importa `sys` para utilizarlo en este archivo.
import threading  # Importa `threading` para utilizarlo en este archivo.
import tkinter as tk  # Importa `tkinter` para utilizarlo en este archivo.
from datetime import datetime  # Importa los nombres necesarios desde `datetime`.
from pathlib import Path  # Importa los nombres necesarios desde `pathlib`.
from tkinter import filedialog, messagebox, scrolledtext, ttk  # Importa los nombres necesarios desde `tkinter`.

# Asegurar que el directorio raíz esté en el path
BASE_DIR = Path(__file__).resolve().parent  # Guarda en `BASE_DIR` el resultado de `Path(__file__).resolve().parent`.
sys.path.insert(0, str(BASE_DIR))  # Inserta el elemento o texto indicado en la interfaz.

from config import (  # Importa los nombres necesarios desde `config`.
    BASE_DIR,  # Continua la expresion abierta arriba con este valor o argumento.
    STORIES_DIR,  # Continua la expresion abierta arriba con este valor o argumento.
    USED_STORIES_DIR,  # Continua la expresion abierta arriba con este valor o argumento.
    AUDIO_DIR,  # Continua la expresion abierta arriba con este valor o argumento.
    GAMEPLAY_DIR,  # Continua la expresion abierta arriba con este valor o argumento.
    OUTPUT_DIR,  # Continua la expresion abierta arriba con este valor o argumento.
    USED_GAMEPLAY_DIR,  # Continua la expresion abierta arriba con este valor o argumento.
    LOG_DIR,  # Continua la expresion abierta arriba con este valor o argumento.
    TTS_VOICE,  # Continua la expresion abierta arriba con este valor o argumento.
    TTS_RATE,  # Continua la expresion abierta arriba con este valor o argumento.
    TTS_PITCH,  # Continua la expresion abierta arriba con este valor o argumento.
    PUBLISH_PLATFORM,  # Continua la expresion abierta arriba con este valor o argumento.
    VIDEO_TITLE_TEMPLATE,  # Continua la expresion abierta arriba con este valor o argumento.
    save_env_config,  # Continua la expresion abierta arriba con este valor o argumento.
)  # Cierra la llamada o agrupacion de argumentos abierta anteriormente.


# ============================================================
#  VENTANA PRINCIPAL
# ============================================================

class RedditBotGUI:  # Declara la clase `RedditBotGUI` que agrupa este comportamiento.
    def __init__(self, root: tk.Tk):  # Declara la funcion `__init__` y especifica sus parametros y tipo de retorno.
        self.root = root  # Guarda en `self.root` el resultado de `root`.
        self.root.title("Reddit Story Video Bot")  # Invoca `self.root.title` con los argumentos indicados.
        self.root.geometry("900x650")  # Invoca `self.root.geometry` con los argumentos indicados.
        self.root.minsize(800, 550)  # Invoca `self.root.minsize` con los argumentos indicados.

        # Icono de la ventana (opcional, un emoji no funciona en todas las versiones)
        # self.root.iconbitmap(...)

        # Variable para controlar la ejecución
        self.process_running = False  # Guarda en `self.process_running` el resultado de `False`.
        self.process = None  # Guarda en `self.process` el resultado de `None`.

        # --- Barra de menú ---
        menubar = tk.Menu(self.root)  # Guarda en `menubar` el resultado de `tk.Menu(self.root)`.
        self.root.config(menu=menubar)  # Actualiza las opciones del componente de Tkinter.

        file_menu = tk.Menu(menubar, tearoff=0)  # Guarda en `file_menu` el resultado de `tk.Menu(menubar, tearoff=0)`.
        file_menu.add_command(label="Salir", command=self.root.quit)  # Invoca `file_menu.add_command` con los argumentos indicados.
        menubar.add_cascade(label="Archivo", menu=file_menu)  # Invoca `menubar.add_cascade` con los argumentos indicados.

        help_menu = tk.Menu(menubar, tearoff=0)  # Guarda en `help_menu` el resultado de `tk.Menu(menubar, tearoff=0)`.
        help_menu.add_command(label="Acerca de", command=self.show_about)  # Invoca `help_menu.add_command` con los argumentos indicados.
        menubar.add_cascade(label="Ayuda", menu=help_menu)  # Invoca `menubar.add_cascade` con los argumentos indicados.

        # --- Pestañas ---
        self.notebook = ttk.Notebook(self.root)  # Guarda en `self.notebook` el resultado de `ttk.Notebook(self.root)`.
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)  # Coloca el componente en el contenedor de Tkinter.

        # Crear pestañas
        self.tab_stories = ttk.Frame(self.notebook)  # Guarda en `self.tab_stories` el resultado de `ttk.Frame(self.notebook)`.
        self.tab_config = ttk.Frame(self.notebook)  # Guarda en `self.tab_config` el resultado de `ttk.Frame(self.notebook)`.
        self.tab_run = ttk.Frame(self.notebook)  # Guarda en `self.tab_run` el resultado de `ttk.Frame(self.notebook)`.
        self.tab_files = ttk.Frame(self.notebook)  # Guarda en `self.tab_files` el resultado de `ttk.Frame(self.notebook)`.

        self.notebook.add(self.tab_stories, text="  📖 Historias  ")  # Anade el elemento indicado al conjunto.
        self.notebook.add(self.tab_config, text="  ⚙️ Configuración  ")  # Anade el elemento indicado al conjunto.
        self.notebook.add(self.tab_run, text="  ▶️ Ejecución  ")  # Anade el elemento indicado al conjunto.
        self.notebook.add(self.tab_files, text="  📁 Archivos  ")  # Anade el elemento indicado al conjunto.

        # Construir cada pestaña
        self.build_stories_tab()  # Invoca `self.build_stories_tab` con los argumentos indicados.
        self.build_config_tab()  # Invoca `self.build_config_tab` con los argumentos indicados.
        self.build_run_tab()  # Invoca `self.build_run_tab` con los argumentos indicados.
        self.build_files_tab()  # Invoca `self.build_files_tab` con los argumentos indicados.

        # Refrescar listas al inicio
        self.refresh_story_lists()  # Invoca `self.refresh_story_lists` con los argumentos indicados.

        # Cerrar bien al salir
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)  # Invoca `self.root.protocol` con los argumentos indicados.

    # ========================================================
    #  PESTAÑA: HISTORIAS
    # ========================================================

    def build_stories_tab(self):  # Declara la funcion `build_stories_tab` y especifica sus parametros y tipo de retorno.
        # Frame superior con botones
        btn_frame = ttk.Frame(self.tab_stories)  # Guarda en `btn_frame` el resultado de `ttk.Frame(self.tab_stories)`.
        btn_frame.pack(fill="x", pady=(10, 5), padx=10)  # Coloca el componente en el contenedor de Tkinter.

        ttk.Button(btn_frame, text="➕ Nueva historia", command=self.new_story).pack(side="left", padx=2)  # Invoca `ttk.Button` con los argumentos indicados.
        ttk.Button(btn_frame, text="✏️ Editar seleccionada", command=self.edit_story).pack(side="left", padx=2)  # Invoca `ttk.Button` con los argumentos indicados.
        ttk.Button(btn_frame, text="🗑️ Eliminar seleccionada", command=self.delete_story).pack(side="left", padx=2)  # Invoca `ttk.Button` con los argumentos indicados.
        ttk.Button(btn_frame, text="🔄 Recargar", command=self.refresh_story_lists).pack(side="right", padx=2)  # Invoca `ttk.Button` con los argumentos indicados.

        # Panel con dos listas: Pendientes y Usadas
        paned = ttk.PanedWindow(self.tab_stories, orient="horizontal")  # Guarda en `paned` el resultado de `ttk.PanedWindow(self.tab_stories, orient="horizontal")`.
        paned.pack(fill="both", expand=True, padx=10, pady=(0, 10))  # Coloca el componente en el contenedor de Tkinter.

        # --- Lista de pendientes ---
        pending_frame = ttk.LabelFrame(paned, text="📥 Pendientes")  # Guarda en `pending_frame` el resultado de `ttk.LabelFrame(paned, text="📥 Pendientes")`.
        self.pending_listbox = tk.Listbox(pending_frame, font=("Consolas", 10))  # Guarda en `self.pending_listbox` el resultado de `tk.Listbox(pending_frame, font=("Consolas", 10))`.
        self.pending_listbox.pack(fill="both", expand=True, padx=5, pady=5)  # Coloca el componente en el contenedor de Tkinter.
        self.pending_listbox.bind("<Double-Button-1>", lambda e: self.edit_story())  # Asocia el evento indicado con la funcion de respuesta.
        scroll_p = ttk.Scrollbar(pending_frame, orient="vertical", command=self.pending_listbox.yview)  # Guarda en `scroll_p` el resultado de `ttk.Scrollbar(pending_frame, orient="vertical", command=self.pending_listbox.yview)`.
        scroll_p.pack(side="right", fill="y")  # Coloca el componente en el contenedor de Tkinter.
        self.pending_listbox.config(yscrollcommand=scroll_p.set)  # Actualiza las opciones del componente de Tkinter.
        paned.add(pending_frame, weight=1)  # Anade el elemento indicado al conjunto.

        # --- Lista de usadas ---
        used_frame = ttk.LabelFrame(paned, text="✅ Usadas")  # Guarda en `used_frame` el resultado de `ttk.LabelFrame(paned, text="✅ Usadas")`.
        self.used_listbox = tk.Listbox(used_frame, font=("Consolas", 10), fg="gray")  # Guarda en `self.used_listbox` el resultado de `tk.Listbox(used_frame, font=("Consolas", 10), fg="gray")`.
        self.used_listbox.pack(fill="both", expand=True, padx=5, pady=5)  # Coloca el componente en el contenedor de Tkinter.
        scroll_u = ttk.Scrollbar(used_frame, orient="vertical", command=self.used_listbox.yview)  # Guarda en `scroll_u` el resultado de `ttk.Scrollbar(used_frame, orient="vertical", command=self.used_listbox.yview)`.
        scroll_u.pack(side="right", fill="y")  # Coloca el componente en el contenedor de Tkinter.
        self.used_listbox.config(yscrollcommand=scroll_u.set)  # Actualiza las opciones del componente de Tkinter.
        paned.add(used_frame, weight=1)  # Anade el elemento indicado al conjunto.

        # Botón para mover de usadas a pendientes (reprocesar)
        ttk.Button(  # Invoca `ttk.Button` con los argumentos indicados.
            self.tab_stories,  # Continua la expresion abierta arriba con este valor o argumento.
            text="⬆️ Mover a pendientes (reprocesar)",  # Guarda en `text` el resultado de `"⬆️ Mover a pendientes (reprocesar)",`.
            command=self.restore_story,  # Guarda en `command` el resultado de `self.restore_story,`.
        ).pack(pady=(0, 10))  # Cierra la llamada o agrupacion de argumentos abierta anteriormente.

    def refresh_story_lists(self):  # Declara la funcion `refresh_story_lists` y especifica sus parametros y tipo de retorno.
        """Actualiza ambas listas de historias."""  # Ejecuta la operacion indicada por esta expresion.
        self.pending_listbox.delete(0, tk.END)  # Elimina el elemento o texto indicado.
        self.used_listbox.delete(0, tk.END)  # Elimina el elemento o texto indicado.

        # Pendientes
        if STORIES_DIR.exists():  # Solo ejecuta el bloque siguiente si se cumple `STORIES_DIR.exists()`.
            for f in sorted(STORIES_DIR.glob("*.txt")):  # Recorre `sorted(STORIES_DIR.glob("*.txt"))` y asigna cada elemento a `f`.
                self.pending_listbox.insert(tk.END, f.name)  # Inserta el elemento o texto indicado en la interfaz.

        # Usadas
        if USED_STORIES_DIR.exists():  # Solo ejecuta el bloque siguiente si se cumple `USED_STORIES_DIR.exists()`.
            for f in sorted(USED_STORIES_DIR.glob("*.txt")):  # Recorre `sorted(USED_STORIES_DIR.glob("*.txt"))` y asigna cada elemento a `f`.
                self.used_listbox.insert(tk.END, f.name)  # Inserta el elemento o texto indicado en la interfaz.

        if self.pending_listbox.size() == 0:  # Solo ejecuta el bloque siguiente si se cumple `self.pending_listbox.size() == 0`.
            self.pending_listbox.insert(tk.END, "(No hay historias pendientes)")  # Inserta el elemento o texto indicado en la interfaz.

        if self.used_listbox.size() == 0:  # Solo ejecuta el bloque siguiente si se cumple `self.used_listbox.size() == 0`.
            self.used_listbox.insert(tk.END, "(No hay historias usadas)")  # Inserta el elemento o texto indicado en la interfaz.

    def get_selected_story_path(self, listbox) -> Path | None:  # Declara la funcion `get_selected_story_path` y especifica sus parametros y tipo de retorno.
        """Devuelve el Path del archivo seleccionado en un listbox, o None."""  # Ejecuta la operacion indicada por esta expresion.
        sel = listbox.curselection()  # Guarda en `sel` el resultado de `listbox.curselection()`.
        if not sel:  # Solo ejecuta el bloque siguiente si se cumple `not sel`.
            messagebox.showwarning("Seleccionar", "Selecciona una historia de la lista.")  # Muestra al usuario el dialogo o aviso indicado desde Tkinter.
            return None  # Devuelve `None` al llamador y termina esta funcion.
        filename = listbox.get(sel[0])  # Guarda en `filename` el resultado de `listbox.get(sel[0])`.
        # Comprobar primero en pendientes, luego en usadas
        for folder in (STORIES_DIR, USED_STORIES_DIR):  # Recorre `(STORIES_DIR, USED_STORIES_DIR)` y asigna cada elemento a `folder`.
            p = folder / filename  # Guarda en `p` el resultado de `folder / filename`.
            if p.exists():  # Solo ejecuta el bloque siguiente si se cumple `p.exists()`.
                return p  # Devuelve `p` al llamador y termina esta funcion.
        return None  # Devuelve `None` al llamador y termina esta funcion.

    def new_story(self):  # Declara la funcion `new_story` y especifica sus parametros y tipo de retorno.
        """Abre un editor para crear una nueva historia."""  # Ejecuta la operacion indicada por esta expresion.
        editor = StoryEditor(self.root, mode="new")  # Guarda en `editor` el resultado de `StoryEditor(self.root, mode="new")`.
        self.root.wait_window(editor.window)  # Invoca `self.root.wait_window` con los argumentos indicados.
        self.refresh_story_lists()  # Invoca `self.refresh_story_lists` con los argumentos indicados.

    def edit_story(self):  # Declara la funcion `edit_story` y especifica sus parametros y tipo de retorno.
        """Abre la historia seleccionada en el editor."""  # Ejecuta la operacion indicada por esta expresion.
        path = self.get_selected_story_path(self.pending_listbox)  # Guarda en `path` el resultado de `self.get_selected_story_path(self.pending_listbox)`.
        if path is None:  # Solo ejecuta el bloque siguiente si se cumple `path is None`.
            path = self.get_selected_story_path(self.used_listbox)  # Guarda en `path` el resultado de `self.get_selected_story_path(self.used_listbox)`.
        if path is None:  # Solo ejecuta el bloque siguiente si se cumple `path is None`.
            return  # Termina esta funcion sin devolver un valor explicito.
        editor = StoryEditor(self.root, mode="edit", filepath=path)  # Guarda en `editor` el resultado de `StoryEditor(self.root, mode="edit", filepath=path)`.
        self.root.wait_window(editor.window)  # Invoca `self.root.wait_window` con los argumentos indicados.
        self.refresh_story_lists()  # Invoca `self.refresh_story_lists` con los argumentos indicados.

    def delete_story(self):  # Declara la funcion `delete_story` y especifica sus parametros y tipo de retorno.
        """Elimina la historia seleccionada."""  # Ejecuta la operacion indicada por esta expresion.
        path = self.get_selected_story_path(self.pending_listbox)  # Guarda en `path` el resultado de `self.get_selected_story_path(self.pending_listbox)`.
        if path is None:  # Solo ejecuta el bloque siguiente si se cumple `path is None`.
            path = self.get_selected_story_path(self.used_listbox)  # Guarda en `path` el resultado de `self.get_selected_story_path(self.used_listbox)`.
        if path is None:  # Solo ejecuta el bloque siguiente si se cumple `path is None`.
            return  # Termina esta funcion sin devolver un valor explicito.
        if messagebox.askyesno("Confirmar", f"¿Eliminar '{path.name}' definitivamente?"):  # Solo ejecuta el bloque siguiente si se cumple `messagebox.askyesno("Confirmar", f"¿Eliminar '{path.name}' definitivamente")`.
            path.unlink()  # Elimina el archivo indicado.
            self.refresh_story_lists()  # Invoca `self.refresh_story_lists` con los argumentos indicados.

    def restore_story(self):  # Declara la funcion `restore_story` y especifica sus parametros y tipo de retorno.
        """Mueve una historia de usadas a pendientes para reprocesarla."""  # Ejecuta la operacion indicada por esta expresion.
        sel = self.used_listbox.curselection()  # Guarda en `sel` el resultado de `self.used_listbox.curselection()`.
        if not sel:  # Solo ejecuta el bloque siguiente si se cumple `not sel`.
            messagebox.showwarning("Seleccionar", "Selecciona una historia de la lista de usadas.")  # Muestra al usuario el dialogo o aviso indicado desde Tkinter.
            return  # Termina esta funcion sin devolver un valor explicito.
        filename = self.used_listbox.get(sel[0])  # Guarda en `filename` el resultado de `self.used_listbox.get(sel[0])`.
        src = USED_STORIES_DIR / filename  # Guarda en `src` el resultado de `USED_STORIES_DIR / filename`.
        dst = STORIES_DIR / filename  # Construye en `dst` la ruta del archivo o carpeta indicada.
        if src.exists():  # Solo ejecuta el bloque siguiente si se cumple `src.exists()`.
            # También limpiar su ID de used_posts.json para que se pueda reprocesar
            self._remove_from_used_posts(filename)  # Invoca `self._remove_from_used_posts` con los argumentos indicados.
            src.rename(dst)  # Renombra o mueve el archivo indicado.
            self.refresh_story_lists()  # Invoca `self.refresh_story_lists` con los argumentos indicados.
            messagebox.showinfo("Hecho", f"'{filename}' movido a pendientes.")  # Muestra al usuario el dialogo o aviso indicado desde Tkinter.

    def _remove_from_used_posts(self, story_filename: str):  # Declara la funcion `_remove_from_used_posts` y especifica sus parametros y tipo de retorno.
        """Elimina el ID de la historia de used_posts.json para permitir reprocesarla."""  # Ejecuta la operacion indicada por esta expresion.
        used_posts_file = BASE_DIR / "data" / "used_posts.json"  # Construye en `used_posts_file` la ruta del archivo o carpeta indicada.
        story_id = Path(story_filename).stem  # Guarda en `story_id` el resultado de `Path(story_filename).stem`.
        if used_posts_file.exists():  # Solo ejecuta el bloque siguiente si se cumple `used_posts_file.exists()`.
            try:   # Inicia un bloque cuyo error puede gestionarse en una clausula except.
                data = json.loads(used_posts_file.read_text(encoding="utf-8"))  # Guarda en `data` el resultado de `json.loads(used_posts_file.read_text(encoding="utf-8"))`.
                ids = set(data.get("used_ids", []))  # Guarda en `ids` el resultado de `set(data.get("used_ids", []))`.
                ids.discard(story_id)  # Invoca `ids.discard` con los argumentos indicados.
                data["used_ids"] = sorted(list(ids))  # Ejecuta la operacion indicada por esta expresion.
                used_posts_file.write_text(json.dumps(data, indent=4, ensure_ascii=False), encoding="utf-8")  # Escribe el contenido generado en el archivo indicado.
            except Exception:  # Captura `Exception` para gestionar el error en este bloque.
                pass  # No realiza ninguna operacion en esta rama; sirve como bloque vacio.

    # ========================================================
    #  PESTAÑA: CONFIGURACIÓN
    # ========================================================

    def build_config_tab(self):  # Declara la funcion `build_config_tab` y especifica sus parametros y tipo de retorno.
        # Usar un Canvas con scroll por si hay muchas opciones
        canvas = tk.Canvas(self.tab_config, highlightthickness=0)  # Guarda en `canvas` el resultado de `tk.Canvas(self.tab_config, highlightthickness=0)`.
        scrollbar = ttk.Scrollbar(self.tab_config, orient="vertical", command=canvas.yview)  # Guarda en `scrollbar` el resultado de `ttk.Scrollbar(self.tab_config, orient="vertical", command=canvas.yview)`.
        scroll_frame = ttk.Frame(canvas)  # Guarda en `scroll_frame` el resultado de `ttk.Frame(canvas)`.

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))  # Asocia el evento indicado con la funcion de respuesta.
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")  # Invoca `canvas.create_window` con los argumentos indicados.
        canvas.configure(yscrollcommand=scrollbar.set)  # Invoca `canvas.configure` con los argumentos indicados.

        canvas.pack(side="left", fill="both", expand=True)  # Coloca el componente en el contenedor de Tkinter.
        scrollbar.pack(side="right", fill="y")  # Coloca el componente en el contenedor de Tkinter.

        # Bind de la rueda del ratón
        def _on_mousewheel(event):  # Declara la funcion `_on_mousewheel` y especifica sus parametros y tipo de retorno.
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")  # Invoca `canvas.yview_scroll` con los argumentos indicados.
        canvas.bind_all("<MouseWheel>", _on_mousewheel)  # Invoca `canvas.bind_all` con los argumentos indicados.

        # --- TTS ---
        tts_frame = ttk.LabelFrame(scroll_frame, text="🗣️ Texto a Voz (TTS)", padding=10)  # Guarda en `tts_frame` el resultado de `ttk.LabelFrame(scroll_frame, text="🗣️ Texto a Voz (TTS)", padding=10)`.
        tts_frame.pack(fill="x", padx=10, pady=5)  # Coloca el componente en el contenedor de Tkinter.

        ttk.Label(tts_frame, text="Voz:").grid(row=0, column=0, sticky="w", pady=2)  # Invoca `ttk.Label` con los argumentos indicados.
        self.tts_voice_var = tk.StringVar(value=TTS_VOICE)  # Guarda en `self.tts_voice_var` el resultado de `tk.StringVar(value=TTS_VOICE)`.
        voice_combo = ttk.Combobox(tts_frame, textvariable=self.tts_voice_var, width=30, state="readonly")  # Guarda en `voice_combo` el resultado de `ttk.Combobox(tts_frame, textvariable=self.tts_voice_var, width=30, state="readonly")`.
        voice_combo["values"] = [  # Ejecuta la operacion indicada por esta expresion.
            "es-ES-AlvaroNeural",  # Aporta este texto a la lista, llamada o mensaje construido arriba.
            "es-ES-ElviraNeural",  # Aporta este texto a la lista, llamada o mensaje construido arriba.
            "es-MX-DaliaNeural",  # Aporta este texto a la lista, llamada o mensaje construido arriba.
            "es-MX-JorgeNeural",  # Aporta este texto a la lista, llamada o mensaje construido arriba.
            "es-AR-ElenaNeural",  # Aporta este texto a la lista, llamada o mensaje construido arriba.
            "es-CL-CatalinaNeural",  # Aporta este texto a la lista, llamada o mensaje construido arriba.
        ]   # Cierra la lista o indice abierto anteriormente.
        voice_combo.grid(row=0, column=1, sticky="w", pady=2)  # Ubica el componente en la fila y columna indicadas de Tkinter.

        ttk.Label(tts_frame, text="Velocidad:").grid(row=1, column=0, sticky="w", pady=2)  # Invoca `ttk.Label` con los argumentos indicados.
        self.tts_rate_var = tk.StringVar(value=TTS_RATE)  # Guarda en `self.tts_rate_var` el resultado de `tk.StringVar(value=TTS_RATE)`.
        rate_combo = ttk.Combobox(tts_frame, textvariable=self.tts_rate_var, width=10, state="readonly")  # Guarda en `rate_combo` el resultado de `ttk.Combobox(tts_frame, textvariable=self.tts_rate_var, width=10, state="readonly")`.
        rate_combo["values"] = ["-20%", "-10%", "+0%", "+10%", "+20%"]  # Ejecuta la operacion indicada por esta expresion.
        rate_combo.grid(row=1, column=1, sticky="w", pady=2)  # Ubica el componente en la fila y columna indicadas de Tkinter.

        ttk.Label(tts_frame, text="Tono:").grid(row=2, column=0, sticky="w", pady=2)  # Invoca `ttk.Label` con los argumentos indicados.
        self.tts_pitch_var = tk.StringVar(value=TTS_PITCH)  # Guarda en `self.tts_pitch_var` el resultado de `tk.StringVar(value=TTS_PITCH)`.
        pitch_combo = ttk.Combobox(tts_frame, textvariable=self.tts_pitch_var, width=10, state="readonly")  # Guarda en `pitch_combo` el resultado de `ttk.Combobox(tts_frame, textvariable=self.tts_pitch_var, width=10, state="readonly")`.
        pitch_combo["values"] = ["-20Hz", "-10Hz", "+0Hz", "+10Hz", "+20Hz"]  # Ejecuta la operacion indicada por esta expresion.
        pitch_combo.grid(row=2, column=1, sticky="w", pady=2)  # Ubica el componente en la fila y columna indicadas de Tkinter.

        # --- Publicación ---
        pub_frame = ttk.LabelFrame(scroll_frame, text="📤 Publicación", padding=10)  # Guarda en `pub_frame` el resultado de `ttk.LabelFrame(scroll_frame, text="📤 Publicación", padding=10)`.
        pub_frame.pack(fill="x", padx=10, pady=5)  # Coloca el componente en el contenedor de Tkinter.

        ttk.Label(pub_frame, text="Plataforma:").grid(row=0, column=0, sticky="w", pady=2)  # Invoca `ttk.Label` con los argumentos indicados.
        self.publish_platform_var = tk.StringVar(value=PUBLISH_PLATFORM)  # Guarda en `self.publish_platform_var` el resultado de `tk.StringVar(value=PUBLISH_PLATFORM)`.
        pub_combo = ttk.Combobox(pub_frame, textvariable=self.publish_platform_var, width=15, state="readonly")  # Guarda en `pub_combo` el resultado de `ttk.Combobox(pub_frame, textvariable=self.publish_platform_var, width=15, state="readonly")`.
        pub_combo["values"] = ["local", "youtube"]  # Ejecuta la operacion indicada por esta expresion.
        pub_combo.grid(row=0, column=1, sticky="w", pady=2)  # Ubica el componente en la fila y columna indicadas de Tkinter.

        ttk.Label(pub_frame, text="Plantilla título:").grid(row=1, column=0, sticky="w", pady=2)  # Invoca `ttk.Label` con los argumentos indicados.
        self.title_template_var = tk.StringVar(value=VIDEO_TITLE_TEMPLATE)  # Guarda en `self.title_template_var` el resultado de `tk.StringVar(value=VIDEO_TITLE_TEMPLATE)`.
        ttk.Entry(pub_frame, textvariable=self.title_template_var, width=50).grid(row=1, column=1, sticky="w", pady=2)  # Invoca `ttk.Entry` con los argumentos indicados.

        ttk.Label(pub_frame, text="Usa {title} como marcador de posición del título de la historia.").grid(  # Invoca `ttk.Label` con los argumentos indicados.
            row=2, column=0, columnspan=2, sticky="w", pady=2  # Guarda en `row` el resultado de `2, column=0, columnspan=2, sticky="w", pady=2`.
        )  # Cierra la llamada o agrupacion de argumentos abierta anteriormente.

        # --- Botón guardar ---
        ttk.Button(  # Invoca `ttk.Button` con los argumentos indicados.
            scroll_frame,  # Continua la expresion abierta arriba con este valor o argumento.
            text="💾 Guardar configuración",  # Guarda en `text` el resultado de `"💾 Guardar configuración",`.
            command=self.save_config,  # Guarda en `command` el resultado de `self.save_config,`.
        ).pack(pady=15)  # Cierra la llamada o agrupacion de argumentos abierta anteriormente.

    def save_config(self):  # Declara la funcion `save_config` y especifica sus parametros y tipo de retorno.
        """Guarda la configuración en el .env y recarga las variables."""  # Ejecuta la operacion indicada por esta expresion.
        updates = {  # Inicia el diccionario que se completa con los campos de las lineas siguientes.
            "TTS_VOICE": self.tts_voice_var.get(),  # Asocia la clave `TTS_VOICE` con el valor indicado en este diccionario.
            "TTS_RATE": self.tts_rate_var.get(),  # Asocia la clave `TTS_RATE` con el valor indicado en este diccionario.
            "TTS_PITCH": self.tts_pitch_var.get(),  # Asocia la clave `TTS_PITCH` con el valor indicado en este diccionario.
            "PUBLISH_PLATFORM": self.publish_platform_var.get(),  # Asocia la clave `PUBLISH_PLATFORM` con el valor indicado en este diccionario.
            "VIDEO_TITLE_TEMPLATE": self.title_template_var.get(),  # Asocia la clave `VIDEO_TITLE_TEMPLATE` con el valor indicado en este diccionario.
        }  # Cierra el diccionario o conjunto abierto anteriormente.
        # Si la plataforma es local, no hace falta el título de YouTube, pero lo guardamos igual
        try:   # Inicia un bloque cuyo error puede gestionarse en una clausula except.
            save_env_config(updates)  # Invoca `save_env_config` con los argumentos indicados.
            messagebox.showinfo("Guardado", "Configuración guardada correctamente en .env")  # Muestra al usuario el dialogo o aviso indicado desde Tkinter.
        except Exception as e:  # Captura `Exception as e` para gestionar el error en este bloque.
            messagebox.showerror("Error", f"No se pudo guardar: {e}")  # Muestra al usuario el dialogo o aviso indicado desde Tkinter.

    # ========================================================
    #  PESTAÑA: EJECUCIÓN
    # ========================================================

    def build_run_tab(self):  # Declara la funcion `build_run_tab` y especifica sus parametros y tipo de retorno.
        # Frame superior: botón + barra de progreso
        top_frame = ttk.Frame(self.tab_run)  # Guarda en `top_frame` el resultado de `ttk.Frame(self.tab_run)`.
        top_frame.pack(fill="x", pady=(10, 5), padx=10)  # Coloca el componente en el contenedor de Tkinter.

        self.run_btn = ttk.Button(  # Guarda en `self.run_btn` el resultado de `ttk.Button(`.
            top_frame,  # Continua la expresion abierta arriba con este valor o argumento.
            text="▶️ Generar vídeo ahora",  # Guarda en `text` el resultado de `"▶️ Generar vídeo ahora",`.
            command=self.run_pipeline,  # Guarda en `command` el resultado de `self.run_pipeline,`.
        )  # Cierra la llamada o agrupacion de argumentos abierta anteriormente.
        self.run_btn.pack(side="left", padx=2)  # Coloca el componente en el contenedor de Tkinter.

        self.cancel_btn = ttk.Button(  # Guarda en `self.cancel_btn` el resultado de `ttk.Button(`.
            top_frame,  # Continua la expresion abierta arriba con este valor o argumento.
            text="⏹️ Cancelar",  # Guarda en `text` el resultado de `"⏹️ Cancelar",`.
            command=self.cancel_pipeline,  # Guarda en `command` el resultado de `self.cancel_pipeline,`.
            state="disabled",  # Guarda en `state` el resultado de `"disabled",`.
        )  # Cierra la llamada o agrupacion de argumentos abierta anteriormente.
        self.cancel_btn.pack(side="left", padx=2)  # Coloca el componente en el contenedor de Tkinter.

        self.progress = ttk.Progressbar(top_frame, mode="determinate", value=0)  # Guarda en `self.progress` el resultado de `ttk.Progressbar(top_frame, mode="determinate", value=0)`.
        self.progress.pack(fill="x", expand=True, side="right", padx=(10, 0))  # Coloca el componente en el contenedor de Tkinter.

        self.status_label = ttk.Label(top_frame, text="Estado: Esperando...", foreground="gray")  # Guarda en `self.status_label` el resultado de `ttk.Label(top_frame, text="Estado: Esperando...", foreground="gray")`.
        self.status_label.pack(side="right", padx=5)  # Coloca el componente en el contenedor de Tkinter.

        # Área de logs en tiempo real
        log_frame = ttk.LabelFrame(self.tab_run, text="📋 Logs en tiempo real")  # Guarda en `log_frame` el resultado de `ttk.LabelFrame(self.tab_run, text="📋 Logs en tiempo real")`.
        log_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))  # Coloca el componente en el contenedor de Tkinter.

        self.log_text = scrolledtext.ScrolledText(  # Guarda en `self.log_text` el resultado de `scrolledtext.ScrolledText(`.
            log_frame,  # Continua la expresion abierta arriba con este valor o argumento.
            font=("Consolas", 9),  # Guarda en `font` el resultado de `("Consolas", 9),`.
            wrap="word",  # Guarda en `wrap` el resultado de `"word",`.
            state="disabled",  # Guarda en `state` el resultado de `"disabled",`.
            bg="#1e1e1e",  # Guarda en `bg` el resultado de `"#1e1e1e",`.
            fg="#d4d4d4",  # Guarda en `fg` el resultado de `"#d4d4d4",`.
            insertbackground="white",  # Guarda en `insertbackground` el resultado de `"white",`.
        )  # Cierra la llamada o agrupacion de argumentos abierta anteriormente.
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)  # Coloca el componente en el contenedor de Tkinter.

        # Configurar tags de color para logs
        self.log_text.tag_config("INFO", foreground="#6a9955")  # Invoca `self.log_text.tag_config` con los argumentos indicados.
        self.log_text.tag_config("WARNING", foreground="#ce9178")  # Invoca `self.log_text.tag_config` con los argumentos indicados.
        self.log_text.tag_config("ERROR", foreground="#f44747")  # Invoca `self.log_text.tag_config` con los argumentos indicados.
        self.log_text.tag_config("DEBUG", foreground="#569cd6")  # Invoca `self.log_text.tag_config` con los argumentos indicados.
        self.log_text.tag_config("BOLD", font=("Consolas", 9, "bold"))  # Invoca `self.log_text.tag_config` con los argumentos indicados.

    def run_pipeline(self):  # Declara la funcion `run_pipeline` y especifica sus parametros y tipo de retorno.
        """Lanza main.py en un hilo separado y captura su salida."""  # Ejecuta la operacion indicada por esta expresion.
        if self.process_running:  # Solo ejecuta el bloque siguiente si se cumple `self.process_running`.
            return  # Termina esta funcion sin devolver un valor explicito.

        self.process_running = True  # Guarda en `self.process_running` el resultado de `True`.
        self.run_btn.config(state="disabled")  # Actualiza las opciones del componente de Tkinter.
        self.cancel_btn.config(state="normal")  # Actualiza las opciones del componente de Tkinter.
        self.progress["value"] = 0  # Ejecuta la operacion indicada por esta expresion.
        self.status_label.config(text="Estado: Ejecutando...", foreground="blue")  # Actualiza las opciones del componente de Tkinter.
        self.log_text.config(state="normal")  # Actualiza las opciones del componente de Tkinter.
        self.log_text.delete(1.0, tk.END)  # Elimina el elemento o texto indicado.
        self.log_text.config(state="disabled")  # Actualiza las opciones del componente de Tkinter.

        hilo = threading.Thread(target=self._run_pipeline_thread, daemon=True)  # Guarda en `hilo` el resultado de `threading.Thread(target=self._run_pipeline_thread, daemon=True)`.
        hilo.start()  # Inicia el hilo o proceso preparado anteriormente.

    def _run_pipeline_thread(self):  # Declara la funcion `_run_pipeline_thread` y especifica sus parametros y tipo de retorno.
        """Ejecuta main.py en un subproceso y captura stdout/stderr."""  # Ejecuta la operacion indicada por esta expresion.
        python_exe = BASE_DIR / ".venv" / "Scripts" / "python.exe"  # Construye en `python_exe` la ruta del archivo o carpeta indicada.
        if not python_exe.exists():  # Solo ejecuta el bloque siguiente si se cumple `not python_exe.exists()`.
            python_exe = sys.executable  # Guarda en `python_exe` el resultado de `sys.executable`.

        main_script = BASE_DIR / "main.py"  # Construye en `main_script` la ruta del archivo o carpeta indicada.

        try:   # Inicia un bloque cuyo error puede gestionarse en una clausula except.
            self.process = subprocess.Popen(  # Guarda en `self.process` el resultado de `subprocess.Popen(`.
                [str(python_exe), str(main_script)],  # Abre la agrupacion, lista o diccionario que se completa en las lineas siguientes.
                cwd=str(BASE_DIR),  # Guarda en `cwd` el resultado de `str(BASE_DIR),`.
                stdout=subprocess.PIPE,  # Guarda en `stdout` el resultado de `subprocess.PIPE,`.
                stderr=subprocess.STDOUT,  # Guarda en `stderr` el resultado de `subprocess.STDOUT,`.
                text=True,  # Guarda en `text` el resultado de `True,`.
                encoding="utf-8",  # Guarda en `encoding` el resultado de `"utf-8",`.
                bufsize=1,  # Guarda en `bufsize` el resultado de `1,`.
            )  # Cierra la llamada o agrupacion de argumentos abierta anteriormente.

            for line in iter(self.process.stdout.readline, ""):  # Recorre `iter(self.process.stdout.readline, "")` y asigna cada elemento a `line`.
                if not line:  # Solo ejecuta el bloque siguiente si se cumple `not line`.
                    break  # Termina inmediatamente el bucle actual.
                self._append_log(line.rstrip())  # Invoca `self._append_log` con los argumentos indicados.
                # Actualizar barra de progreso según palabras clave en el log
                self._update_progress_from_log(line)  # Invoca `self._update_progress_from_log` con los argumentos indicados.

            self.process.wait()  # Espera a que termine el proceso hijo.

            if self.process.returncode == 0:  # Solo ejecuta el bloque siguiente si se cumple `self.process.returncode == 0`.
                self._append_log("✅ Pipeline completado con éxito.")  # Invoca `self._append_log` con los argumentos indicados.
                self.status_label.config(text="Estado: Completado ✅", foreground="green")  # Actualiza las opciones del componente de Tkinter.
            else:  # Ejecuta este bloque cuando no se cumple la condicion o rama anterior.
                self._append_log(f"❌ Pipeline terminó con código de error {self.process.returncode}.")  # Invoca `self._append_log` con los argumentos indicados.
                self.status_label.config(text="Estado: Falló ❌", foreground="red")  # Actualiza las opciones del componente de Tkinter.

        except Exception as e:  # Captura `Exception as e` para gestionar el error en este bloque.
            self._append_log(f"❌ Error al ejecutar el pipeline: {e}")  # Invoca `self._append_log` con los argumentos indicados.
            self.status_label.config(text="Estado: Error ❌", foreground="red")  # Actualiza las opciones del componente de Tkinter.
        finally:   # Ejecuta la limpieza incluso si falla el bloque anterior.
            self.process_running = False  # Guarda en `self.process_running` el resultado de `False`.
            self.root.after(0, self._reset_ui)  # Programa la actualizacion de la interfaz en el hilo principal de Tkinter.

    def _append_log(self, text: str):  # Declara la funcion `_append_log` y especifica sus parametros y tipo de retorno.
        """Añade una línea al log con colores según el nivel."""  # Ejecuta la operacion indicada por esta expresion.
        def do_append():  # Declara la funcion `do_append` y especifica sus parametros y tipo de retorno.
            self.log_text.config(state="normal")  # Actualiza las opciones del componente de Tkinter.
            # Determinar tag según el texto
            tag = None  # Guarda en `tag` el resultado de `None`.
            if text.startswith("202"):  # Solo ejecuta el bloque siguiente si se cumple `text.startswith("202")`.
                # Es una línea de log con timestamp
                if "[ERROR]" in text:  # Solo ejecuta el bloque siguiente si se cumple `"[ERROR]" in text`.
                    tag = "ERROR"  # Guarda en `tag` el resultado de `"ERROR"`.
                elif "[WARNING]" in text or "[WARN]" in text:  # Comprueba la condicion alternativa `"[WARNING]" in text or "[WARN]" in text` si las anteriores fueron falsas.
                    tag = "WARNING"  # Guarda en `tag` el resultado de `"WARNING"`.
                elif "[INFO]" in text:  # Comprueba la condicion alternativa `"[INFO]" in text` si las anteriores fueron falsas.
                    tag = "INFO"  # Guarda en `tag` el resultado de `"INFO"`.
                elif "[DEBUG]" in text:  # Comprueba la condicion alternativa `"[DEBUG]" in text` si las anteriores fueron falsas.
                    tag = "DEBUG"  # Guarda en `tag` el resultado de `"DEBUG"`.
            elif text.startswith("✅") or text.startswith("🎬"):  # Comprueba la condicion alternativa `text.startswith("✅") or text.startswith("🎬")` si las anteriores fueron falsas.
                tag = "BOLD"  # Guarda en `tag` el resultado de `"BOLD"`.

            if tag:  # Solo ejecuta el bloque siguiente si se cumple `tag`.
                self.log_text.insert(tk.END, text + "\n", tag)  # Inserta el elemento o texto indicado en la interfaz.
            else:  # Ejecuta este bloque cuando no se cumple la condicion o rama anterior.
                self.log_text.insert(tk.END, text + "\n")  # Inserta el elemento o texto indicado en la interfaz.

            self.log_text.see(tk.END)  # Invoca `self.log_text.see` con los argumentos indicados.
            self.log_text.config(state="disabled")  # Actualiza las opciones del componente de Tkinter.

        self.root.after(0, do_append)  # Programa la actualizacion de la interfaz en el hilo principal de Tkinter.

    def _update_progress_from_log(self, line: str):  # Declara la funcion `_update_progress_from_log` y especifica sus parametros y tipo de retorno.
        """Actualiza la barra de progreso según la fase que aparece en el log."""  # Ejecuta la operacion indicada por esta expresion.
        if "[0/4]" in line:  # Solo ejecuta el bloque siguiente si se cumple `"[0/4]" in line`.
            self._set_progress(10)  # Invoca `self._set_progress` con los argumentos indicados.
        elif "[1/4]" in line:  # Comprueba la condicion alternativa `"[1/4]" in line` si las anteriores fueron falsas.
            self._set_progress(25)  # Invoca `self._set_progress` con los argumentos indicados.
        elif "[2/4]" in line:  # Comprueba la condicion alternativa `"[2/4]" in line` si las anteriores fueron falsas.
            self._set_progress(50)  # Invoca `self._set_progress` con los argumentos indicados.
        elif "[3/4]" in line:  # Comprueba la condicion alternativa `"[3/4]" in line` si las anteriores fueron falsas.
            self._set_progress(75)  # Invoca `self._set_progress` con los argumentos indicados.
        elif "[4/4]" in line:  # Comprueba la condicion alternativa `"[4/4]" in line` si las anteriores fueron falsas.
            self._set_progress(90)  # Invoca `self._set_progress` con los argumentos indicados.
        elif "completado con éxito" in line.lower() or "Vídeo generado" in line:  # Comprueba la condicion alternativa `"completado con éxito" in line.lower() or "Vídeo generado" in line` si las anteriores fueron falsas.
            self._set_progress(100)  # Invoca `self._set_progress` con los argumentos indicados.

    def _set_progress(self, value: int):  # Declara la funcion `_set_progress` y especifica sus parametros y tipo de retorno.
        self.root.after(0, lambda: self.progress.configure(value=value))  # Programa la actualizacion de la interfaz en el hilo principal de Tkinter.

    def _reset_ui(self):  # Declara la funcion `_reset_ui` y especifica sus parametros y tipo de retorno.
        self.run_btn.config(state="normal")  # Actualiza las opciones del componente de Tkinter.
        self.cancel_btn.config(state="disabled")  # Actualiza las opciones del componente de Tkinter.

    def cancel_pipeline(self):  # Declara la funcion `cancel_pipeline` y especifica sus parametros y tipo de retorno.
        if self.process and self.process_running:  # Solo ejecuta el bloque siguiente si se cumple `self.process and self.process_running`.
            self.process.terminate()  # Solicita la terminacion del proceso hijo.
            self._append_log("⏹️ Pipeline cancelado por el usuario.")  # Invoca `self._append_log` con los argumentos indicados.
            self.status_label.config(text="Estado: Cancelado ⏹️", foreground="orange")  # Actualiza las opciones del componente de Tkinter.
            self.process_running = False  # Guarda en `self.process_running` el resultado de `False`.
            self._reset_ui()  # Invoca `self._reset_ui` con los argumentos indicados.

    # ========================================================
    #  PESTAÑA: ARCHIVOS
    # ========================================================

    def build_files_tab(self):  # Declara la funcion `build_files_tab` y especifica sus parametros y tipo de retorno.
        frame = ttk.Frame(self.tab_files)  # Guarda en `frame` el resultado de `ttk.Frame(self.tab_files)`.
        frame.pack(fill="both", expand=True, padx=10, pady=10)  # Coloca el componente en el contenedor de Tkinter.

        ttk.Label(frame, text="Accesos rápidos a carpetas del proyecto:", font=("Segoe UI", 11)).pack(anchor="w", pady=(0, 10))  # Invoca `ttk.Label` con los argumentos indicados.

        folders = [  # Inicia la lista que se completa con los elementos de las lineas siguientes.
            ("📖 Historias pendientes", STORIES_DIR),  # Abre la agrupacion, lista o diccionario que se completa en las lineas siguientes.
            ("✅ Historias usadas", USED_STORIES_DIR),  # Abre la agrupacion, lista o diccionario que se completa en las lineas siguientes.
            ("🎬 Gameplays", GAMEPLAY_DIR),  # Abre la agrupacion, lista o diccionario que se completa en las lineas siguientes.
            ("🎥 Vídeos generados (output)", OUTPUT_DIR),  # Abre la agrupacion, lista o diccionario que se completa en las lineas siguientes.
            ("🔊 Audios generados", AUDIO_DIR),  # Abre la agrupacion, lista o diccionario que se completa en las lineas siguientes.
            ("📦 Gameplays usados", USED_GAMEPLAY_DIR),  # Abre la agrupacion, lista o diccionario que se completa en las lineas siguientes.
            ("📋 Logs", LOG_DIR),  # Abre la agrupacion, lista o diccionario que se completa en las lineas siguientes.
            ("📁 Raíz del proyecto", BASE_DIR),  # Abre la agrupacion, lista o diccionario que se completa en las lineas siguientes.
        ]   # Cierra la lista o indice abierto anteriormente.

        for label, path in folders:  # Recorre `folders` y asigna cada elemento a `label, path`.
            btn_frame = ttk.Frame(frame)  # Guarda en `btn_frame` el resultado de `ttk.Frame(frame)`.
            btn_frame.pack(fill="x", pady=2)  # Coloca el componente en el contenedor de Tkinter.

            ttk.Label(btn_frame, text=label, width=30, anchor="w").pack(side="left")  # Invoca `ttk.Label` con los argumentos indicados.
            ttk.Label(btn_frame, text=str(path), foreground="gray").pack(side="left", fill="x", expand=True, padx=5)  # Invoca `ttk.Label` con los argumentos indicados.
            ttk.Button(  # Invoca `ttk.Button` con los argumentos indicados.
                btn_frame,  # Continua la expresion abierta arriba con este valor o argumento.
                text="📂 Abrir",  # Guarda en `text` el resultado de `"📂 Abrir",`.
                command=lambda p=path: self.open_folder(p),  # Guarda en `command` el resultado de `lambda p=path: self.open_folder(p),`.
                width=8,  # Guarda en `width` el resultado de `8,`.
            ).pack(side="right")  # Cierra la llamada o agrupacion de argumentos abierta anteriormente.

    def open_folder(self, path: Path):  # Declara la funcion `open_folder` y especifica sus parametros y tipo de retorno.
        """Abre la carpeta en el explorador de archivos."""  # Ejecuta la operacion indicada por esta expresion.
        if path.exists():  # Solo ejecuta el bloque siguiente si se cumple `path.exists()`.
            os.startfile(str(path))  # Invoca `os.startfile` con los argumentos indicados.
        else:  # Ejecuta este bloque cuando no se cumple la condicion o rama anterior.
            messagebox.showerror("Error", f"La carpeta no existe:\n{path}")  # Muestra al usuario el dialogo o aviso indicado desde Tkinter.

    # ========================================================
    #  MÉTODOS AUXILIARES
    # ========================================================

    def show_about(self):  # Declara la funcion `show_about` y especifica sus parametros y tipo de retorno.
        messagebox.showinfo(  # Muestra al usuario el dialogo o aviso indicado desde Tkinter.
            "Acerca de",  # Aporta este texto a la lista, llamada o mensaje construido arriba.
            "Reddit Story Video Bot\n\n"  # Ejecuta la operacion indicada por esta expresion.
            "Genera vídeos verticales estilo TikTok/Shorts\n"  # Ejecuta la operacion indicada por esta expresion.
            "con historias narradas y gameplay de fondo.\n\n"  # Ejecuta la operacion indicada por esta expresion.
            "Versión 1.0",  # Aporta este texto a la lista, llamada o mensaje construido arriba.
        )  # Cierra la llamada o agrupacion de argumentos abierta anteriormente.

    def on_closing(self):  # Declara la funcion `on_closing` y especifica sus parametros y tipo de retorno.
        if self.process_running:  # Solo ejecuta el bloque siguiente si se cumple `self.process_running`.
            if messagebox.askyesno("Confirmar", "Hay un pipeline en ejecución. ¿Detenerlo y salir?"):  # Solo ejecuta el bloque siguiente si se cumple `messagebox.askyesno("Confirmar", "Hay un pipeline en ejecución. ¿Detenerlo y salir")`.
                self.cancel_pipeline()  # Invoca `self.cancel_pipeline` con los argumentos indicados.
            else:  # Ejecuta este bloque cuando no se cumple la condicion o rama anterior.
                return  # Termina esta funcion sin devolver un valor explicito.
        self.root.destroy()  # Invoca `self.root.destroy` con los argumentos indicados.


# ============================================================
#  VENTANA EDITOR DE HISTORIAS
# ============================================================

class StoryEditor:  # Declara la clase `StoryEditor` que agrupa este comportamiento.
    def __init__(self, parent, mode="new", filepath: Path = None):  # Declara la funcion `__init__` y especifica sus parametros y tipo de retorno.
        self.parent = parent  # Guarda en `self.parent` el resultado de `parent`.
        self.mode = mode  # Guarda en `self.mode` el resultado de `mode`.
        self.filepath = filepath  # Guarda en `self.filepath` el resultado de `filepath`.

        self.window = tk.Toplevel(parent)  # Guarda en `self.window` el resultado de `tk.Toplevel(parent)`.
        self.window.title("Editar historia" if mode == "edit" else "Nueva historia")  # Invoca `self.window.title` con los argumentos indicados.
        self.window.geometry("600x500")  # Invoca `self.window.geometry` con los argumentos indicados.
        self.window.minsize(400, 300)  # Invoca `self.window.minsize` con los argumentos indicados.
        self.window.transient(parent)  # Invoca `self.window.transient` con los argumentos indicados.
        self.window.grab_set()  # Invoca `self.window.grab_set` con los argumentos indicados.

        ttk.Label(self.window, text="Título:").pack(anchor="w", padx=10, pady=(10, 2))  # Invoca `ttk.Label` con los argumentos indicados.
        self.title_entry = ttk.Entry(self.window, font=("Segoe UI", 11))  # Guarda en `self.title_entry` el resultado de `ttk.Entry(self.window, font=("Segoe UI", 11))`.
        self.title_entry.pack(fill="x", padx=10, pady=(0, 5))  # Coloca el componente en el contenedor de Tkinter.

        ttk.Label(self.window, text="Cuerpo de la historia:").pack(anchor="w", padx=10, pady=(5, 2))  # Invoca `ttk.Label` con los argumentos indicados.
        self.body_text = scrolledtext.ScrolledText(  # Guarda en `self.body_text` el resultado de `scrolledtext.ScrolledText(`.
            self.window,  # Continua la expresion abierta arriba con este valor o argumento.
            font=("Segoe UI", 10),  # Guarda en `font` el resultado de `("Segoe UI", 10),`.
            wrap="word",  # Guarda en `wrap` el resultado de `"word",`.
            height=15,  # Guarda en `height` el resultado de `15,`.
        )  # Cierra la llamada o agrupacion de argumentos abierta anteriormente.
        self.body_text.pack(fill="both", expand=True, padx=10, pady=(0, 5))  # Coloca el componente en el contenedor de Tkinter.

        # Botones
        btn_frame = ttk.Frame(self.window)  # Guarda en `btn_frame` el resultado de `ttk.Frame(self.window)`.
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))  # Coloca el componente en el contenedor de Tkinter.

        ttk.Button(btn_frame, text="💾 Guardar", command=self.save).pack(side="left", padx=2)  # Invoca `ttk.Button` con los argumentos indicados.
        ttk.Button(btn_frame, text="❌ Cancelar", command=self.window.destroy).pack(side="left", padx=2)  # Invoca `ttk.Button` con los argumentos indicados.

        # Si es edición, cargar contenido
        if mode == "edit" and filepath and filepath.exists():  # Solo ejecuta el bloque siguiente si se cumple `mode == "edit" and filepath and filepath.exists()`.
            self.load_content(filepath)  # Invoca `self.load_content` con los argumentos indicados.

    def load_content(self, path: Path):  # Declara la funcion `load_content` y especifica sus parametros y tipo de retorno.
        """Carga el contenido de un archivo .txt en el editor."""  # Ejecuta la operacion indicada por esta expresion.
        content = path.read_text(encoding="utf-8").strip()  # Guarda en `content` el resultado de `path.read_text(encoding="utf-8").strip()`.
        lines = content.splitlines()  # Guarda en `lines` el resultado de `content.splitlines()`.
        if lines:  # Solo ejecuta el bloque siguiente si se cumple `lines`.
            self.title_entry.delete(0, tk.END)  # Elimina el elemento o texto indicado.
            self.title_entry.insert(0, lines[0].strip())  # Inserta el elemento o texto indicado en la interfaz.
            resto = lines[1:]  # Guarda en `resto` el resultado de `lines[1:]`.
            # Saltar línea en blanco si es separador
            if resto and resto[0].strip() == "":  # Solo ejecuta el bloque siguiente si se cumple `resto and resto[0].strip() == ""`.
                resto = resto[1:]  # Guarda en `resto` el resultado de `resto[1:]`.
            self.body_text.delete(1.0, tk.END)  # Elimina el elemento o texto indicado.
            self.body_text.insert(1.0, "\n".join(resto).strip())  # Inserta el elemento o texto indicado en la interfaz.

    def save(self):  # Declara la funcion `save` y especifica sus parametros y tipo de retorno.
        """Guarda el contenido como .txt en STORIES_DIR."""  # Ejecuta la operacion indicada por esta expresion.
        title = self.title_entry.get().strip()  # Guarda en `title` el resultado de `self.title_entry.get().strip()`.
        body = self.body_text.get(1.0, tk.END).strip()  # Guarda en `body` el resultado de `self.body_text.get(1.0, tk.END).strip()`.

        if not title:  # Solo ejecuta el bloque siguiente si se cumple `not title`.
            messagebox.showwarning("Validación", "El título no puede estar vacío.")  # Muestra al usuario el dialogo o aviso indicado desde Tkinter.
            return  # Termina esta funcion sin devolver un valor explicito.
        if not body:  # Solo ejecuta el bloque siguiente si se cumple `not body`.
            messagebox.showwarning("Validación", "El cuerpo de la historia no puede estar vacío.")  # Muestra al usuario el dialogo o aviso indicado desde Tkinter.
            return  # Termina esta funcion sin devolver un valor explicito.

        # Si es nueva, generar nombre de archivo a partir del título
        if self.mode == "new":  # Solo ejecuta el bloque siguiente si se cumple `self.mode == "new"`.
            # Nombre seguro para archivo
            safe_name = "".join(c if c.isalnum() or c in " _-" else "" for c in title)  # Guarda en `safe_name` el resultado de `"".join(c if c.isalnum() or c in " _-" else "" for c in title)`.
            safe_name = safe_name.strip().replace(" ", "_")[:80]  # Guarda en `safe_name` el resultado de `safe_name.strip().replace(" ", "_")[:80]`.
            if not safe_name:  # Solo ejecuta el bloque siguiente si se cumple `not safe_name`.
                safe_name = "historia"  # Guarda en `safe_name` el resultado de `"historia"`.
            # Asegurar que no exista
            counter = 0  # Guarda en `counter` el resultado de `0`.
            filename = f"{safe_name}.txt"  # Guarda en `filename` el resultado de `f"{safe_name}.txt"`.
            while (STORIES_DIR / filename).exists():  # Repite el bloque mientras se cumpla `(STORIES_DIR / filename).exists()`.
                counter += 1  # Actualiza `counter`: acumula su valor con `1`.
                filename = f"{safe_name}_{counter}.txt"  # Guarda en `filename` el resultado de `f"{safe_name}_{counter}.txt"`.
            self.filepath = STORIES_DIR / filename  # Construye en `self.filepath` la ruta del archivo o carpeta indicada.
        else:  # Ejecuta este bloque cuando no se cumple la condicion o rama anterior.
            # En edición, si se cambió el título, renombrar el archivo
            if self.filepath and self.filepath.exists():  # Solo ejecuta el bloque siguiente si se cumple `self.filepath and self.filepath.exists()`.
                old_title = self.filepath.stem  # Guarda en `old_title` el resultado de `self.filepath.stem`.
                new_safe = "".join(c if c.isalnum() or c in " _-" else "" for c in title)  # Guarda en `new_safe` el resultado de `"".join(c if c.isalnum() or c in " _-" else "" for c in title)`.
                new_safe = new_safe.strip().replace(" ", "_")[:80]  # Guarda en `new_safe` el resultado de `new_safe.strip().replace(" ", "_")[:80]`.
                if new_safe and new_safe != self.filepath.stem:  # Solo ejecuta el bloque siguiente si se cumple `new_safe and new_safe != self.filepath.stem`.
                    new_path = self.filepath.with_stem(new_safe)  # Guarda en `new_path` el resultado de `self.filepath.with_stem(new_safe)`.
                    if not new_path.exists():  # Solo ejecuta el bloque siguiente si se cumple `not new_path.exists()`.
                        self.filepath.rename(new_path)  # Renombra o mueve el archivo indicado.
                        self.filepath = new_path  # Guarda en `self.filepath` el resultado de `new_path`.

        # Escribir archivo con formato título + línea en blanco + cuerpo
        content = f"{title}\n\n{body}\n"  # Guarda en `content` el resultado de `f"{title}\n\n{body}\n"`.
        self.filepath.write_text(content, encoding="utf-8")  # Escribe el contenido generado en el archivo indicado.

        messagebox.showinfo("Guardado", f"Historia guardada:\n{self.filepath.name}")  # Muestra al usuario el dialogo o aviso indicado desde Tkinter.
        self.window.destroy()  # Invoca `self.window.destroy` con los argumentos indicados.


# ============================================================
#  PUNTO DE ENTRADA
# ============================================================

def main():  # Declara la funcion `main` y especifica sus parametros y tipo de retorno.
    root = tk.Tk()  # Guarda en `root` el resultado de `tk.Tk()`.
    app = RedditBotGUI(root)  # Guarda en `app` el resultado de `RedditBotGUI(root)`.
    root.mainloop()  # Invoca `root.mainloop` con los argumentos indicados.


if __name__ == "__main__":  # Solo ejecuta el bloque siguiente si se cumple `__name__ == "__main__"`.
    main()  # Invoca `main` con los argumentos indicados.