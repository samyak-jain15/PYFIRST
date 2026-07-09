"""
PyFirst IDE - A friendly Python editor built for beginners.
Run this file with: python pyfirst_ide.py
Requires: Python 3.8+ with tkinter (included in most Python installs)
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import threading
import sys
import os
import tempfile
import queue
import re
import bisect
import time
import ast


# ---------------------------------------------------------------------------
# Constants & Theme
# ---------------------------------------------------------------------------

APP_NAME = "🐍 PyFirst — Your Python Playground"
APP_VERSION = "v1.7"
WINDOW_SIZE = "1300x820"
AUTO_SAVE_MS = 60_000          # 1 minute
HIGHLIGHT_DELAY_MS = 120       # debounce for syntax highlighting & mistake checking
FONT_FAMILY = "Consolas"
FONT_MIN, FONT_MAX = 8, 40

COLORS = {
    "bg_dark":      "#08090f",   # overall darkest background (Activity Bar, window background)
    "bg_editor":    "#0a0b12",   # editor canvas
    "bg_sidebar":   "#0e101a",   # explorer sidebar, AI sidebar, headers
    "bg_panel":     "#121422",   # panels, input containers, chat bubbles
    "border_color": "#1a1d30",   # thin dividing borders
    "text_light":   "#e2e8f0",   # main text
    "text_muted":   "#64748b",   # muted gray text
    "accent_cyan":  "#22d3ee",   # cyan brand accent
    "accent_green": "#10b981",   # emerald green
    "accent_red":   "#ef4444",   # rose red
    "accent_amber": "#f59e0b",   # warnings amber
    "console_fg":   "#ffffff",   # output console text default to bright white
    # Syntax colours — vivid & beginner-friendly
    "syn_keyword":  "#f472b6",   # fuchsia / pink keywords
    "syn_builtin":  "#22d3ee",   # cyan builtins
    "syn_string":   "#a3e635",   # lime strings
    "syn_comment":  "#475569",   # slate comments
    "syn_number":   "#fb923c",   # orange numbers
    "syn_bracket":  "#c084fc",   # purple brackets
    "syn_operator": "#f472b6",   # pink operators
    "syn_punct":    "#38bdf8",   # sky punctuation
}

PYTHON_KEYWORDS = [
    "False", "None", "True", "and", "as", "assert", "async", "await",
    "break", "class", "continue", "def", "del", "elif", "else", "except",
    "finally", "for", "from", "global", "if", "import", "in", "is",
    "lambda", "nonlocal", "not", "or", "pass", "raise", "return", "try",
    "while", "with", "yield",
]

PYTHON_BUILTINS = [
    "abs", "all", "any", "bin", "bool", "bytes", "callable", "chr",
    "classmethod", "dict", "dir", "divmod", "enumerate", "eval", "exec",
    "filter", "float", "format", "globals", "hasattr", "hash", "help",
    "hex", "id", "input", "int", "isinstance", "issubclass", "iter",
    "len", "list", "locals", "map", "max", "min", "next", "object",
    "oct", "open", "ord", "pow", "print", "range", "repr", "reversed",
    "round", "set", "setattr", "slice", "sorted", "staticmethod", "str",
    "sum", "super", "tuple", "type", "vars", "zip",
]

PYTHON_METHODS = [
    "append", "extend", "insert", "remove", "pop", "clear", "index",
    "count", "sort", "reverse", "copy", "keys", "values", "items", "get",
    "update", "popitem", "setdefault", "add", "discard", "difference",
    "intersection", "union", "split", "join", "strip", "replace", "find",
    "startswith", "endswith", "lower", "upper", "title", "self", "__init__",
]

PYTHON_EXCEPTIONS = [
    "Exception", "ValueError", "TypeError", "IndexError", "KeyError",
    "ZeroDivisionError", "NameError", "AttributeError", "FileNotFoundError",
    "StopIteration", "RuntimeError", "OSError", "IOError", "ImportError",
]

AUTOCOMPLETE_WORDS = sorted(
    set(PYTHON_KEYWORDS + PYTHON_BUILTINS + PYTHON_METHODS + PYTHON_EXCEPTIONS)
)

# ---------------------------------------------------------------------------
# Code Templates
# ---------------------------------------------------------------------------

TEMPLATES = {
    "👋 Hello World": (
        "# ---- Lesson 0: Your Very First Python Program ----\n"
        "# Click ▶ RUN or press Ctrl+R to run this!\n\n"
        "print('Hello, World! 🌍')\n"
        "print('Welcome to PyFirst — let\\'s learn Python!')\n\n"
        "# Change the name below and run again 🙂\n"
        "your_name = 'Sam'\n"
        "print(f'Nice to meet you, {your_name}!')\n"
    ),
    "📦 Variables & Types": (
        "# ---- Lesson 1: Variables & Data Types ----\n"
        "# A variable is a box that stores a value.\n\n"
        "name    = 'Alice'     # str  — text in quotes\n"
        "age     = 20          # int  — whole number\n"
        "height  = 1.68        # float — decimal number\n"
        "student = True        # bool — True or False\n\n"
        "print('Name  :', name,    '→ type:', type(name).__name__)\n"
        "print('Age   :', age,     '→ type:', type(age).__name__)\n"
        "print('Height:', height,  '→ type:', type(height).__name__)\n"
        "print('Is student?', student)\n\n"
        "# f-strings let you embed variables inside text:\n"
        "print(f'Hi {name}! Next year you will be {age + 1} years old.')\n"
    ),
    "🔀 If / Else": (
        "# ---- Lesson 2: Making Decisions ----\n"
        "# Python checks conditions top-to-bottom and runs the first True block.\n\n"
        "score = 78   # Try changing this number!\n\n"
        "if score >= 90:\n"
        "    grade = 'A ⭐'\n"
        "elif score >= 80:\n"
        "    grade = 'B 👍'\n"
        "elif score >= 70:\n"
        "    grade = 'C 🙂'\n"
        "elif score >= 60:\n"
        "    grade = 'D 😬'\n"
        "else:\n"
        "    grade = 'F 😢'\n\n"
        "print(f'Score: {score}  →  Grade: {grade}')\n"
    ),
    "🔁 Loops": (
        "# ---- Lesson 3: Repeating Actions with Loops ----\n\n"
        "# --- for loop: repeat a known number of times ---\n"
        "print('=== Counting with for loop ===')\n"
        "for i in range(1, 6):           # 1, 2, 3, 4, 5\n"
        "    print(f'  {i} squared = {i ** 2}')\n\n"
        "# --- while loop: repeat until a condition is false ---\n"
        "print('\\n=== Countdown with while loop ===')\n"
        "count = 5\n"
        "while count > 0:\n"
        "    print(f'  T-minus {count}...')\n"
        "    count -= 1          # same as: count = count - 1\n"
        "print('  🚀 Blastoff!')\n"
    ),
}

WELCOME_CODE = (
    "# 🐍 Welcome to PyFirst — Your Python Playground!\n"
    "#\n"
    "# ▶  Press the green RUN button (or Ctrl+R) to run your code.\n"
    "# 📋  Pick a lesson from the 'Lessons' dropdown on the right.\n"
    "# 💾  Save your work with Ctrl+S. Close tabs with Ctrl+W.\n"
    "# 🔤  Zoom the editor: Ctrl+= / Ctrl+- (or Ctrl+scroll).\n"
    "# 🖥️  Fullscreen Mode: Toggle with F11.\n"
    "#\n\n"
    "print('Hello, World! 🌍')\n\n"
    "# Try editing me and pressing RUN!\n"
    "for i in range(1, 6):\n"
    "    print(f'  {i} × {i} = {i * i}')\n"
)


# ---------------------------------------------------------------------------
# Reusable UI Widgets & Helper Functions
# ---------------------------------------------------------------------------

def set_app_icon(window):
    """
    Applies the application window icon.
    Outside the file: Looks for 'logo.png' or 'logo.ico' next to the script.
    Inside the file: Falls back to an embedded base64-encoded Python logo.
    """
    try:
        # 1. Look outside the file first (in the current directory)
        script_dir = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
        ext_png = os.path.join(script_dir, "logo.png")
        ext_ico = os.path.join(script_dir, "logo.ico")

        if os.path.exists(ext_png):
            img = tk.PhotoImage(file=ext_png)
            window.iconphoto(True, img)
            return
        elif os.path.exists(ext_ico):
            window.iconbitmap(ext_ico)
            return
    except Exception:
        pass

    try:
        # 2. Inside the file fallback (Base64 Python-like Logo)
        base64_data = (
            "R0lGODlhIAAgAPMAAAAAAH9/f5+fn8/Pz9/f3+fn587OzszMzP///wAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAACH5BAEAAAsALAAAAAAgACAAAwS8cMlJq7046827/2AoiuNoHicJrOnKrqz7vU8M0HDd6Lre"
            "96OfD3gUGo3FYbEIDHqcD6h0GqVSr0+s9Yr9cr3hsHhMLpvP6LR6zW673/C4fE6v2+/4vH7P7/v/"
            "gIGCg4SFhoeIiYqLjI2Oj5CRkpOUlZaXmJmAnp+Xg6GDFKKFFKOEFKSCFaKAFp+BpqemqaSjpqyv"
            "qq6pqZ+vs66ysrSytLO1trK3t7m6vK26vLq6vL+vsbe8vbS8wMG/xMnIycrLzM3OAwQAOw=="
        )
        img = tk.PhotoImage(data=base64_data)
        window.iconphoto(True, img)
    except Exception:
        pass


def draw_x(img, color):
    """Draws a clean, single-pixel thick X inside a 12x12 transparent PhotoImage."""
    for i in range(3, 9):
        img.put(color, to=(i, i))
        img.put(color, to=(11 - i, i))


def create_mac_dots(parent, bg_color, size=16, on_close=None, on_minimize=None, on_maximize=None):
    """
    Creates a frame containing three functional macOS-style window controls.
    Colors: Red (#ff5f56), Yellow (#ffbd2e), Green (#27c93f).
    """
    frame = tk.Frame(parent, bg=bg_color)
    colors = ["#ff5f56", "#ffbd2e", "#27c93f"]
    callbacks = [on_close, on_minimize, on_maximize]

    for color, callback in zip(colors, callbacks):
        dot = tk.Canvas(frame, width=size, height=size, bg=bg_color, bd=0, highlightthickness=0)
        if callback:
            dot.configure(cursor="hand2")
            dot.bind("<Button-1>", lambda e, cb=callback: cb())
        dot.pack(side=tk.LEFT, padx=4)
        dot.create_oval(1, 1, size - 1, size - 1, fill=color, outline=color)
    return frame


class RoundedButton(tk.Canvas):
    """
    A canvas-based button with rounded corners and smooth hover feedback.
    """
    def __init__(self, parent, text, command,
                 normal_color, hover_color,
                 width=130, height=36, radius=10,
                 text_color="#ffffff", font_size=9):
        super().__init__(
            parent,
            width=width, height=height,
            bg=parent["bg"], bd=0,
            highlightthickness=0,
            cursor="hand2",
        )
        self.text = text
        self.command = command
        self.normal_color = normal_color
        self.hover_color = hover_color
        self.radius = radius
        self._width = width
        self._height = height
        self.text_color = text_color
        self.font_size = font_size

        self._draw(self.normal_color)
        self.bind("<Enter>",    lambda _e: self._draw(self.hover_color))
        self.bind("<Leave>",    lambda _e: self._draw(self.normal_color))
        self.bind("<Button-1>", self._on_click)

    def _draw(self, color: str) -> None:
        self.delete("all")
        w, h, r = self._width, self._height, self.radius
        r = min(r, w // 2, h // 2)
        for cx, cy in [(0, 0), (w - 2*r, 0), (0, h - 2*r), (w - 2*r, h - 2*r)]:
            self.create_oval(cx, cy, cx + 2*r, cy + 2*r, fill=color, outline=color)
        self.create_rectangle(r, 0, w - r, h, fill=color, outline=color)
        self.create_rectangle(0, r, w, h - r, fill=color, outline=color)
        self.create_text(
            w / 2, h / 2,
            text=self.text,
            fill=self.text_color,
            font=(FONT_FAMILY, self.font_size, "bold"),
        )

    def _on_click(self, _event) -> None:
        self._draw("#ffffff")
        self.after(80, lambda: self._draw(self.hover_color))
        if self.command:
            self.command()


class RoundedFrame(tk.Canvas):
    """
    A canvas-based container frame with rounded corners and an optional outer border.
    Specifies style=tk.ARC on border paths to prevent internal right-angle visual lines.
    """
    def __init__(self, parent, bg, fill_color, radius=12, outline="", outline_width=1, **kwargs):
        super().__init__(
            parent,
            bg=bg,
            bd=0,
            highlightthickness=0,
            **kwargs,
        )
        self.fill_color = fill_color
        self.radius = radius
        self.outline = outline
        self.outline_width = outline_width
        self.bind("<Configure>", self._draw)

    def _draw(self, _event=None) -> None:
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        r = self.radius

        if w <= 2 * r or h <= 2 * r:
            return

        ow = self.outline_width if self.outline else 1
        pad = ow / 2
        x0, y0 = pad, pad
        x1, y1 = w - pad - 1, h - pad - 1

        # 1. Fill the background interior (no outlines to prevent interior lines)
        self.create_arc(x0, y0, x0 + 2 * r, y0 + 2 * r, start=90, extent=90, fill=self.fill_color, outline="")
        self.create_arc(x1 - 2 * r, y0, x1, y0 + 2 * r, start=0, extent=90, fill=self.fill_color, outline="")
        self.create_arc(x0, y1 - 2 * r, x0 + 2 * r, y1, start=180, extent=90, fill=self.fill_color, outline="")
        self.create_arc(x1 - 2 * r, y1 - 2 * r, x1, y1, start=270, extent=90, fill=self.fill_color, outline="")

        self.create_rectangle(x0 + r, y0, x1 - r, y1, fill=self.fill_color, outline="")
        self.create_rectangle(x0, y0 + r, x1, y1 - r, fill=self.fill_color, outline="")

        # 2. Draw outer outline border lines if specified (using tk.ARC path style)
        if self.outline:
            self.create_arc(x0, y0, x0 + 2 * r, y0 + 2 * r, start=90, extent=90, style=tk.ARC, outline=self.outline, width=ow)
            self.create_arc(x1 - 2 * r, y0, x1, y0 + 2 * r, start=0, extent=90, style=tk.ARC, outline=self.outline, width=ow)
            self.create_arc(x0, y1 - 2 * r, x0 + 2 * r, y1, start=180, extent=90, style=tk.ARC, outline=self.outline, width=ow)
            self.create_arc(x1 - 2 * r, y1 - 2 * r, x1, y1, start=270, extent=90, style=tk.ARC, outline=self.outline, width=ow)

            self.create_line(x0 + r, y0, x1 - r, y0, fill=self.outline, width=ow)
            self.create_line(x0 + r, y1, x1 - r, y1, fill=self.outline, width=ow)
            self.create_line(x0, y0 + r, x0, y1 - r, fill=self.outline, width=ow)
            self.create_line(x1, y0 + r, x1, y1 - r, fill=self.outline, width=ow)


class CustomNotebook(ttk.Notebook):
    """
    A custom ttk Notebook incorporating individual interactive close buttons
    directly on each open tab header.
    """
    __initialized = False

    def __init__(self, parent, app, *args, **kwargs):
        self.app = app
        if not CustomNotebook.__initialized:
            self.__initialize_custom_style()
            CustomNotebook.__initialized = True

        kwargs["style"] = "CustomNotebook"
        super().__init__(parent, *args, **kwargs)

        self._active = None
        self.bind("<ButtonPress-1>", self.on_close_press, True)
        self.bind("<ButtonRelease-1>", self.on_close_release, True)

    def __initialize_custom_style(self):
        style = ttk.Style()
        
        # Build self-contained PhotoImages
        self.img_close = tk.PhotoImage("img_close", width=12, height=12)
        draw_x(self.img_close, COLORS["text_muted"])

        self.img_close_active = tk.PhotoImage("img_close_active", width=12, height=12)
        draw_x(self.img_close_active, COLORS["accent_red"])

        self.img_close_pressed = tk.PhotoImage("img_close_pressed", width=12, height=12)
        draw_x(self.img_close_pressed, "#991b1b")

        # Create close element mappings
        style.element_create("close", "image", "img_close",
                             ("active", "pressed", "!disabled", "img_close_pressed"),
                             ("active", "!disabled", "img_close_active"),
                             border=8, sticky='')

        # Configure custom layout hierarchies
        style.layout("CustomNotebook", [("CustomNotebook.client", {"sticky": "nswe"})])
        style.layout("CustomNotebook.Tab", [
            ("CustomNotebook.tab", {
                "sticky": "nswe",
                "children": [
                    ("CustomNotebook.padding", {
                        "side": "top",
                        "sticky": "nswe",
                        "children": [
                            ("CustomNotebook.focus", {
                                "side": "top",
                                "sticky": "nswe",
                                "children": [
                                    ("CustomNotebook.label", {"side": "left", "sticky": ''}),
                                    ("CustomNotebook.close", {"side": "left", "sticky": ''})
                                ]
                            })
                        ]
                    })
                ]
            })
        ])
        
        # Apply visual colors matching core editor styling
        style.configure(
            "CustomNotebook",
            background=COLORS["bg_dark"],
            borderwidth=0,
            bordercolor=COLORS["bg_dark"],
            lightcolor=COLORS["bg_dark"],
            darkcolor=COLORS["bg_dark"],
        )
        style.configure(
            "CustomNotebook.Tab",
            background=COLORS["bg_sidebar"],
            foreground=COLORS["text_muted"],
            font=(FONT_FAMILY, 9),
            padding=[12, 6],
            borderwidth=0,
            bordercolor=COLORS["bg_dark"],
            lightcolor=COLORS["bg_dark"],
            darkcolor=COLORS["bg_dark"],
        )
        style.map(
            "CustomNotebook.Tab",
            background=[("selected", COLORS["bg_editor"])],
            foreground=[("selected", COLORS["accent_cyan"])],
            bordercolor=[("selected", COLORS["bg_dark"])],
            lightcolor=[("selected", COLORS["accent_cyan"])], # Draws a subtle cyan accent top border on active tab
            darkcolor=[("selected", COLORS["bg_dark"])],
        )

    def on_close_press(self, event):
        element = self.identify(event.x, event.y)
        if "close" in element:
            index = self.index("@%d,%d" % (event.x, event.y))
            self.state(['pressed'])
            self._active = index
            return "break"

    def on_close_release(self, event):
        if not self.instate(['pressed']):
            return

        element = self.identify(event.x, event.y)
        if "close" in element:
            index = self.index("@%d,%d" % (event.x, event.y))
            if self._active == index:
                self.app.close_tab_by_index(index)
        self.state(['!pressed'])
        self._active = None


class LineNumbers(tk.Canvas):
    """
    Sidebar widget that displays line numbers synced to a Text widget.
    """
    _MIN_WIDTH = 45
    _PADDING   = 15   

    def __init__(self, parent, text_widget: tk.Text, **kwargs):
        super().__init__(
            parent,
            bg=COLORS["bg_editor"],
            bd=0,
            highlightthickness=0,
            width=self._MIN_WIDTH,
            **kwargs,
        )
        self.text_widget = text_widget

    def redraw(self) -> None:
        self.delete("all")

        try:
            last_line  = int(self.text_widget.index("end-1c").split(".")[0])
        except tk.TclError:
            return

        digit_px   = len(str(last_line)) * 10
        new_width  = max(self._MIN_WIDTH, digit_px + self._PADDING)
        if self.winfo_width() != new_width:
            self.config(width=new_width)

        index = self.text_widget.index("@0,0")
        font  = self.text_widget.cget("font")

        while True:
            info = self.text_widget.dlineinfo(index)
            if info is None:
                break
            y        = info[1]
            line_num = index.split(".")[0]
            self.create_text(
                new_width - 8, y + 2,
                anchor="ne",
                text=line_num,
                fill=COLORS["text_muted"],
                font=font,
            )
            index = self.text_widget.index(f"{index}+1line")


# ---------------------------------------------------------------------------
# Editor Tab Helper
# ---------------------------------------------------------------------------

class EditorTab:
    """
    Represents a single open tab inside the multiple-file workspace.
    """
    def __init__(self, parent_notebook: CustomNotebook, app, file_path="", content=""):
        self.app = app
        self.notebook = parent_notebook
        self.file_path = file_path
        self.last_saved_content = content

        self.frame = tk.Frame(self.notebook, bg=COLORS["bg_dark"])

        self.container = RoundedFrame(self.frame, bg=COLORS["bg_dark"], fill_color=COLORS["bg_editor"], radius=14)
        self.container.pack(fill=tk.BOTH, expand=True, padx=10, pady=(4, 10))

        self.scrollbar = ttk.Scrollbar(self.container, orient=tk.VERTICAL, style="App.Vertical.TScrollbar")
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 6), pady=6)

        self.editor = tk.Text(
            self.container,
            bg=COLORS["bg_editor"],
            fg=COLORS["text_light"],
            insertbackground=COLORS["accent_cyan"],
            insertwidth=2,
            font=(FONT_FAMILY, self.app.editor_font_size),
            bd=0, highlightthickness=0,
            padx=10, pady=10,
            yscrollcommand=self.scrollbar.set,
            undo=True,
            maxundo=200,
            wrap=tk.NONE,
            selectbackground=COLORS["border_color"],
            selectforeground=COLORS["text_light"],
            tabs=("1c",),   
        )

        self.line_nums = LineNumbers(self.container, self.editor)
        self.line_nums.pack(side=tk.LEFT, fill=tk.Y, padx=(6, 0), pady=6)
        self.editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=6)

        def _sync_scroll(*args):
            self.editor.yview(*args)
            self.line_nums.redraw()

        self.scrollbar.config(command=_sync_scroll)
        self.editor.config(
            yscrollcommand=lambda *a: (self.scrollbar.set(*a), self.line_nums.redraw())
        )

        for tag, color in [
            ("keyword",     COLORS["syn_keyword"]),
            ("builtin",     COLORS["syn_builtin"]),
            ("string",      COLORS["syn_string"]),
            ("comment",     COLORS["syn_comment"]),
            ("number",      COLORS["syn_number"]),
            ("bracket",     COLORS["syn_bracket"]),
            ("operator",    COLORS["syn_operator"]),
            ("punctuation", COLORS["syn_punct"]),
            ("function",    "#e5c07b"), # Function calls/definitions highlighted in VS Code style Yellow
            ("self_cls",    "#e06c75"), # Reference keywords highlighted in Soft Coral Red
        ]:
            self.editor.tag_configure(tag, foreground=color)

        self.editor.tag_configure("error_marker", background="#2a1215", underline=True, underlinefg=COLORS["accent_red"])
        self.editor.tag_configure("search_highlight", background=COLORS["border_color"], foreground=COLORS["accent_cyan"])

        if content:
            self.editor.insert("1.0", content)

        # Basic text inputs
        self.editor.bind("<KeyRelease>", self.app._on_key_release)
        self.editor.bind("<KeyPress>",   self.app._on_key_press)
        self.editor.bind("<BackSpace>",  self.app._on_backspace)
        self.editor.bind("<Button-1>",   self.app._on_editor_click)
        self.editor.bind("<FocusOut>",   lambda _e: self.app._ac_hide())

        # Bind Smart Auto-Indentation & Autocomplete trigger on Return
        self.editor.bind("<Return>",     self.app._on_return_pressed)

        # Autocomplete navigation overrides
        self.editor.bind("<Up>",     self.app._ac_up)
        self.editor.bind("<Down>",   self.app._ac_down)
        self.editor.bind("<Tab>",    self.app._ac_tab)
        self.editor.bind("<Escape>", self.app._ac_escape)


# ---------------------------------------------------------------------------
# Main Application Class
# ---------------------------------------------------------------------------

class PyFirstIDE:
    """
    PyFirst — A beginner-friendly Python IDE.
    """

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry(WINDOW_SIZE)
        self.root.configure(bg=COLORS["bg_dark"])
        set_app_icon(self.root)

        self.process: subprocess.Popen | None = None
        self.output_queue: queue.Queue        = queue.Queue()
        self.typing_queue: queue.Queue        = queue.Queue()
        self.incoming_buffer                  = ""
        self.last_char_time                   = 0.0
        self._highlight_job: str | None       = None
        self.current_mistake_line: int | None = None

        # Standard secure gateway endpoint for Pollinations.AI
        self.ai_provider = "Free AI (Pollinations.ai)"
        self.ai_api_key  = ""
        self.ai_endpoint = "https://gen.pollinations.ai"
        self.ai_model    = "openai"

        self.editor_font_size  = 13
        self.console_font_size = 12

        self.tabs = []  # Holds open EditorTab instances
        self.auto_save_enabled = tk.BooleanVar(value=True)

        self._apply_scrollbar_style()
        self.setup_menu()
        self.setup_ui()
        self.setup_bindings()
        self._load_welcome()
        self._poll_output_queue()
        self._poll_typing_queue()

        self.toggle_dark_mode_border()
        self.root.after(AUTO_SAVE_MS, self._auto_save_tick)

    # ── Active Tab Property Helpers (keeps code clean and compatible) ───

    @property
    def active_tab(self) -> EditorTab | None:
        if not self.tabs:
            return None
        try:
            current_idx = self.editor_notebook.index("current")
            if 0 <= current_idx < len(self.tabs):
                return self.tabs[current_idx]
        except tk.TclError:
            pass
        return None

    @property
    def editor(self) -> tk.Text | None:
        tab = self.active_tab
        return tab.editor if tab else None

    @property
    def line_nums(self) -> LineNumbers | None:
        tab = self.active_tab
        return tab.line_nums if tab else None

    @property
    def current_file_path(self) -> str:
        tab = self.active_tab
        return tab.file_path if tab else ""

    @current_file_path.setter
    def current_file_path(self, val: str) -> None:
        tab = self.active_tab
        if tab:
            tab.file_path = val

    @property
    def last_saved_content(self) -> str:
        tab = self.active_tab
        return tab.last_saved_content if tab else ""

    @last_saved_content.setter
    def last_saved_content(self, val: str) -> None:
        tab = self.active_tab
        if tab:
            tab.last_saved_content = val

    # ──────────────────────────────────────────────────────────────────

    def _apply_scrollbar_style(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "App.Vertical.TScrollbar",
            background=COLORS["bg_panel"],
            troughcolor=COLORS["bg_dark"],
            bordercolor=COLORS["bg_dark"],
            arrowcolor=COLORS["accent_cyan"],
            relief="flat",
            borderwidth=1,
            arrowsize=0,
        )
        style.map(
            "App.Vertical.TScrollbar",
            background=[("active", COLORS["accent_cyan"]), ("pressed", COLORS["accent_cyan"])],
        )
        # Harmonize dropdown theme colors with dark slate borders
        style.configure(
            "App.TCombobox",
            fieldbackground=COLORS["bg_panel"],
            background=COLORS["bg_dark"],
            foreground=COLORS["text_light"],
            bordercolor=COLORS["border_color"],
            lightcolor=COLORS["bg_panel"],
            darkcolor=COLORS["bg_panel"],
            arrowcolor=COLORS["accent_cyan"],
            arrowsize=12,
        )
        style.map(
            "App.TCombobox",
            fieldbackground=[("readonly", COLORS["bg_panel"])],
            foreground=[("readonly", COLORS["text_light"])],
        )
        # Force system popups inside Combobox dropdown lists to apply the dark canvas style
        self.root.option_add("*TCombobox*Listbox.background", COLORS["bg_panel"])
        self.root.option_add("*TCombobox*Listbox.foreground", COLORS["text_light"])
        self.root.option_add("*TCombobox*Listbox.selectBackground", COLORS["accent_cyan"])
        self.root.option_add("*TCombobox*Listbox.selectForeground", "#000000")
        self.root.option_add("*TCombobox*Listbox.font", (FONT_FAMILY, 9))

    def setup_menu(self) -> None:
        menu_cfg = dict(
            bg=COLORS["bg_sidebar"],
            fg=COLORS["text_light"],
            activebackground=COLORS["accent_cyan"],
            activeforeground="#0e0f17",
            tearoff=0,
            relief="flat",
        )
        self.menubar = tk.Menu(self.root, bg=COLORS["bg_dark"], fg=COLORS["text_light"])

        # ---- File ----
        self.file_menu = tk.Menu(self.menubar, **menu_cfg)
        self.file_menu.add_command(label="📄  New Tab",         command=self.file_new,     accelerator="Ctrl+N")
        self.file_menu.add_command(label="📂  Open File…",      command=self.file_open,    accelerator="Ctrl+O")
        self.file_menu.add_command(label="💾  Save Current",    command=self.file_save,    accelerator="Ctrl+S")
        self.file_menu.add_command(label="💾  Save As…",        command=self.file_save_as, accelerator="Ctrl+Shift+S")
        self.file_menu.add_command(label="❌  Close Tab",       command=self.close_active_tab, accelerator="Ctrl+W")
        self.file_menu.add_separator()
        self.file_menu.add_checkbutton(label="⏱  Auto-save all active files", variable=self.auto_save_enabled)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="❌  Exit",           command=self._on_close)
        self.menubar.add_cascade(label="File", menu=self.file_menu)

        # ---- Dark Mode ----
        self.dark_menu = tk.Menu(self.menubar, **menu_cfg)
        self.dark_mode_var = tk.BooleanVar(value=True)
        self.dark_menu.add_checkbutton(
            label="🌙  Dark Mode Boundary (Title Bar)",
            variable=self.dark_mode_var,
            command=self.toggle_dark_mode_border,
        )
        self.menubar.add_cascade(label="Dark Mode", menu=self.dark_menu)

        # ---- Help ----
        self.help_menu = tk.Menu(self.menubar, **menu_cfg)
        self.help_menu.add_command(label="⌨  Keyboard Shortcuts", command=self._show_shortcuts)
        self.help_menu.add_command(label="ℹ  About PyFirst",      command=self._show_about)
        self.menubar.add_cascade(label="Help", menu=self.help_menu)

    def setup_ui(self) -> None:
        self._build_top_bar()
        self._build_status_bar()

        # Workspace Container
        self.main_container = tk.Frame(self.root, bg=COLORS["bg_dark"])
        self.main_container.pack(fill=tk.BOTH, expand=True)

        self._build_activity_bar()

        # Resizable Workspace Splitter with low sash thickness
        self.master_paned = tk.PanedWindow(
            self.main_container,
            orient=tk.HORIZONTAL,
            bg=COLORS["border_color"],
            bd=0,
            sashwidth=3,
            sashpad=1,
            sashrelief="flat",
        )
        self.master_paned.pack(fill=tk.BOTH, expand=True)

        self._build_editor_pane()
        self._build_utility_pane()

        # Set realistic proportional widths
        self.root.after(100, self._configure_initial_pane_widths)
        self._build_autocomplete_popup()

    def _configure_initial_pane_widths(self) -> None:
        try:
            total_w = self.master_paned.winfo_width()
            self.master_paned.sash_place(0, int(total_w * 0.65), 0)
        except Exception:
            pass

    def _build_top_bar(self) -> None:
        bar = tk.Frame(self.root, bg=COLORS["bg_dark"], height=52)
        bar.pack(fill=tk.X, padx=15, pady=(8, 4))

        # Functional macOS style window control dots (Red, Yellow, Green)
        mac_dots = create_mac_dots(
            bar, 
            COLORS["bg_dark"], 
            size=16, 
            on_close=self._on_close, 
            on_minimize=self.root.iconify,
            on_maximize=self.toggle_fullscreen
        )
        mac_dots.pack(side=tk.LEFT, padx=(0, 15))

        logo_frame = tk.Frame(bar, bg=COLORS["bg_dark"])
        logo_frame.pack(side=tk.LEFT, padx=(0, 20))

        tk.Label(
            logo_frame, text="🐍  PyFirst",
            fg=COLORS["accent_cyan"], bg=COLORS["bg_dark"],
            font=(FONT_FAMILY, 14, "bold"),
        ).pack(side=tk.LEFT)

        # Run, Stop, and Clear are highlighted in bright colours permanently with safe hover triggers
        self._btn_run = RoundedButton(
            bar, "▶  Run", self.run_code,
            COLORS["accent_green"], "#0d9488",
            width=85, height=32, radius=8,
        )
        self._btn_run.pack(side=tk.LEFT, padx=3)

        self._btn_stop = RoundedButton(
            bar, "■  Stop", self.stop_code,
            COLORS["accent_red"], "#b91c1c",
            width=85, height=32, radius=8,
        )
        self._btn_stop.pack(side=tk.LEFT, padx=3)

        self._btn_clear = RoundedButton(
            bar, "🗑  Clear Output", self.clear_console,
            COLORS["bg_panel"], "#252840",
            width=120, height=32, radius=8,
        )
        self._btn_clear.pack(side=tk.LEFT, padx=3)

        # Compact Controls Packed to Right
        self._template_var = tk.StringVar()
        dropdown = ttk.Combobox(
            bar,
            textvariable=self._template_var,
            state="readonly",
            width=16,
            style="App.TCombobox",
        )
        dropdown["values"] = list(TEMPLATES.keys())
        dropdown.pack(side=tk.RIGHT, padx=5)
        dropdown.bind("<<ComboboxSelected>>", self._apply_template)

        tk.Label(
            bar, text="Lessons:",
            fg=COLORS["text_muted"], bg=COLORS["bg_dark"],
            font=(FONT_FAMILY, 9),
        ).pack(side=tk.RIGHT, padx=2)

        # Segmented Code Font Zoom Pill Layout
        zoom_frame = RoundedFrame(bar, bg=COLORS["bg_dark"], fill_color=COLORS["bg_panel"], radius=8, width=64, height=28)
        zoom_frame.pack(side=tk.RIGHT, padx=5)
        zoom_frame.pack_propagate(False)

        btn_dec = tk.Label(
            zoom_frame, text="-", font=(FONT_FAMILY, 12, "bold"),
            bg=COLORS["bg_panel"], fg=COLORS["text_light"],
            cursor="hand2"
        )
        btn_dec.place(relx=0.0, rely=0.0, relwidth=0.45, relheight=1.0)
        btn_dec.bind("<Enter>", lambda _e: btn_dec.config(fg=COLORS["accent_cyan"]))
        btn_dec.bind("<Leave>", lambda _e: btn_dec.config(fg=COLORS["text_light"]))
        btn_dec.bind("<Button-1>", lambda _e: self._change_editor_font(-1))

        # Vertical separator line
        sep = tk.Frame(zoom_frame, bg=COLORS["border_color"], width=1)
        sep.place(relx=0.48, rely=0.15, relwidth=0.04, relheight=0.7)

        btn_inc = tk.Label(
            zoom_frame, text="+", font=(FONT_FAMILY, 12, "bold"),
            bg=COLORS["bg_panel"], fg=COLORS["text_light"],
            cursor="hand2"
        )
        btn_inc.place(relx=0.55, rely=0.0, relwidth=0.45, relheight=1.0)
        btn_inc.bind("<Enter>", lambda _e: btn_inc.config(fg=COLORS["accent_cyan"]))
        btn_inc.bind("<Leave>", lambda _e: btn_inc.config(fg=COLORS["text_light"]))
        btn_inc.bind("<Button-1>", lambda _e: self._change_editor_font(+1))

        tk.Label(
            bar, text="Code Font:",
            fg=COLORS["text_muted"], bg=COLORS["bg_dark"],
            font=(FONT_FAMILY, 9),
        ).pack(side=tk.RIGHT, padx=2)

        # Horizontal line boundary under top bar
        div = tk.Frame(self.root, bg=COLORS["border_color"], height=1)
        div.pack(fill=tk.X)

    def _build_status_bar(self) -> None:
        # Status Bar Container
        bar = tk.Frame(self.root, bg=COLORS["bg_sidebar"], height=28)
        bar.pack(side=tk.BOTTOM, fill=tk.X)

        self._status_dot = tk.Label(
            bar, text="● Ready",
            fg=COLORS["accent_green"], bg=COLORS["bg_sidebar"],
            font=(FONT_FAMILY, 9, "bold"),
        )
        self._status_dot.pack(side=tk.LEFT, padx=(14, 4))

        self.mistakes_label = tk.Label(
            bar, text="✓ No issues found - Looking good!",
            fg=COLORS["text_muted"], bg=COLORS["bg_sidebar"],
            font=(FONT_FAMILY, 9),
        )
        self.mistakes_label.pack(side=tk.LEFT, padx=6)
        self.mistakes_label.bind("<Button-1>", self._jump_to_mistake)

        # Right Side info metrics - Active file displays with custom python snake icon 🐍
        self._active_file_lbl = tk.Label(
            bar, text="🐍 unsaved_file.py",
            fg=COLORS["accent_cyan"], bg=COLORS["bg_sidebar"],
            font=(FONT_FAMILY, 9, "bold")
        )
        self._active_file_lbl.pack(side=tk.RIGHT, padx=14)

        self._py_version_lbl = tk.Label(
            bar, text="Python 3.10.0",
            fg=COLORS["text_muted"], bg=COLORS["bg_sidebar"],
            font=(FONT_FAMILY, 9)
        )
        self._py_version_lbl.pack(side=tk.RIGHT, padx=12)

        self._spaces_lbl = tk.Label(
            bar, text="Spaces: 4",
            fg=COLORS["text_muted"], bg=COLORS["bg_sidebar"],
            font=(FONT_FAMILY, 9)
        )
        self._spaces_lbl.pack(side=tk.RIGHT, padx=12)

        self._cursor_label = tk.Label(
            bar, text="Ln 1, Col 0",
            fg=COLORS["text_muted"], bg=COLORS["bg_sidebar"],
            font=(FONT_FAMILY, 9),
        )
        self._cursor_label.pack(side=tk.RIGHT, padx=12)

        # Horizontal 1px Border Division Line
        div = tk.Frame(self.root, bg=COLORS["border_color"], height=1)
        div.pack(side=tk.BOTTOM, fill=tk.X)

    def _create_activity_btn(self, parent, text, command):
        """Creates a Left Activity Bar item with vertical accent indicators and hovers."""
        item_frame = tk.Frame(parent, bg=COLORS["bg_dark"], height=48)
        item_frame.pack(fill=tk.X, pady=2)
        item_frame.pack_propagate(False)

        indicator = tk.Frame(item_frame, bg=COLORS["bg_dark"], width=3)
        indicator.pack(side=tk.LEFT, fill=tk.Y)

        btn = tk.Label(
            item_frame, text=text, font=(FONT_FAMILY, 15),
            bg=COLORS["bg_dark"], fg=COLORS["text_muted"],
            cursor="hand2"
        )
        btn.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(4, 0))

        def on_enter(_e):
            btn.config(fg=COLORS["accent_cyan"])
            indicator.config(bg=COLORS["accent_cyan"])

        def on_leave(_e):
            btn.config(fg=COLORS["text_muted"])
            indicator.config(bg=COLORS["bg_dark"])

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        btn.bind("<Button-1>", lambda _e: command())

    def _create_settings_btn(self, parent):
        """Creates the Settings gear button with vertical margins matching Core indicators."""
        item_frame = tk.Frame(parent, bg=COLORS["bg_dark"], height=48)
        item_frame.pack(fill=tk.X)
        item_frame.pack_propagate(False)

        indicator = tk.Frame(item_frame, bg=COLORS["bg_dark"], width=3)
        indicator.pack(side=tk.LEFT, fill=tk.Y)

        btn = tk.Label(
            item_frame, text="⚙", font=(FONT_FAMILY, 15),
            bg=COLORS["bg_dark"], fg=COLORS["text_muted"],
            cursor="hand2"
        )
        btn.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(4, 0))

        def on_enter(_e):
            btn.config(fg=COLORS["accent_cyan"])
            indicator.config(bg=COLORS["accent_cyan"])

        def on_leave(_e):
            btn.config(fg=COLORS["text_muted"])
            indicator.config(bg=COLORS["bg_dark"])

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        btn.bind("<Button-1>", self.show_settings_popup)

    def _build_activity_bar(self) -> None:
        """Left thin functional utility side panel containing key workspace commands."""
        panel = tk.Frame(self.main_container, bg=COLORS["bg_dark"], width=55)
        panel.pack(side=tk.LEFT, fill=tk.Y)
        panel.pack_propagate(False)

        # Render Activity buttons using indicators and standard handlers
        self._create_activity_btn(panel, "📁", self.file_open)
        self._create_activity_btn(panel, "🔍", self.show_find_dialog)
        self._create_activity_btn(panel, "▶", self.run_code)

        # Pin Settings to Bottom
        bottom_frame = tk.Frame(panel, bg=COLORS["bg_dark"])
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=15)

        self._create_settings_btn(bottom_frame)

    def _build_editor_pane(self) -> None:
        pane = tk.Frame(self.master_paned, bg=COLORS["bg_dark"])
        self.master_paned.add(pane, minsize=350)

        # Custom multi-tab notebook wrapper with active tab close markings
        self.editor_notebook = CustomNotebook(pane, app=self)
        self.editor_notebook.pack(fill=tk.BOTH, expand=True)

    def _build_utility_pane(self) -> None:
        """Unified switcher panel for Console Output & AI Assistant."""
        pane = tk.Frame(self.master_paned, bg=COLORS["bg_dark"])
        self.master_paned.add(pane, minsize=280)

        # Utility Header Switcher Area
        header = tk.Frame(pane, bg=COLORS["bg_sidebar"], height=36)
        header.pack(fill=tk.X)

        self.tab_btn_output = tk.Label(
            header, text="  OUTPUT  ",
            fg=COLORS["accent_cyan"], bg=COLORS["bg_editor"],
            font=(FONT_FAMILY, 9, "bold"), cursor="hand2"
        )
        self.tab_btn_output.pack(side=tk.LEFT, fill=tk.Y, padx=(10, 0))

        self.tab_btn_ai = tk.Label(
            header, text="  AI ASSISTANT  ",
            fg=COLORS["text_muted"], bg=COLORS["bg_sidebar"],
            font=(FONT_FAMILY, 9, "bold"), cursor="hand2"
        )
        self.tab_btn_ai.pack(side=tk.LEFT, fill=tk.Y, padx=2)

        # Output Font Zoom controls
        font_lbl = tk.Label(header, text="Output Font:", fg=COLORS["text_muted"], bg=COLORS["bg_sidebar"], font=(FONT_FAMILY, 8))
        font_lbl.pack(side=tk.RIGHT, padx=2)

        self._btn_utility_font_inc = RoundedButton(
            header, "+", lambda: self._change_console_font(+1),
            COLORS["bg_panel"], COLORS["border_color"],
            width=22, height=22, radius=4, font_size=9
        )
        self._btn_utility_font_inc.pack(side=tk.RIGHT, padx=2)

        self._btn_utility_font_dec = RoundedButton(
            header, "-", lambda: self._change_console_font(-1),
            COLORS["bg_panel"], COLORS["border_color"],
            width=22, height=22, radius=4, font_size=9
        )
        self._btn_utility_font_dec.pack(side=tk.RIGHT, padx=2)

        # Content Containers for dynamic frame switching
        self.output_content_frame = tk.Frame(pane, bg=COLORS["bg_dark"])
        self.ai_content_frame = tk.Frame(pane, bg=COLORS["bg_sidebar"])

        # Render internal panels into their respective switcher hosts
        self._render_console_inside(self.output_content_frame)
        self._render_ai_inside(self.ai_content_frame)

        # Default Active Panel View
        self.show_utility_tab("output")

        # Click tab toggle bindings
        self.tab_btn_output.bind("<Button-1>", lambda e: self.show_utility_tab("output"))
        self.tab_btn_ai.bind("<Button-1>", lambda e: self.show_utility_tab("ai"))

    def show_utility_tab(self, tab_name: str) -> None:
        """Switches the active pane focus between console execution output and AI tutoring blocks."""
        if tab_name == "output":
            self.ai_content_frame.pack_forget()
            self.output_content_frame.pack(fill=tk.BOTH, expand=True)
            self.tab_btn_output.config(fg=COLORS["accent_cyan"], bg=COLORS["bg_editor"])
            self.tab_btn_ai.config(fg=COLORS["text_muted"], bg=COLORS["bg_sidebar"])
        else:
            self.output_content_frame.pack_forget()
            self.ai_content_frame.pack(fill=tk.BOTH, expand=True)
            self.tab_btn_ai.config(fg=COLORS["accent_cyan"], bg=COLORS["bg_editor"])
            self.tab_btn_output.config(fg=COLORS["text_muted"], bg=COLORS["bg_sidebar"])

    def _render_console_inside(self, parent: tk.Frame) -> None:
        """Builds terminal execution display window inside the utility container."""
        container = tk.Frame(parent, bg=COLORS["bg_editor"])
        container.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, style="App.Vertical.TScrollbar")
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 4), pady=4)

        self.console = tk.Text(
            container,
            bg=COLORS["bg_editor"],
            fg="#ffffff", # Console output is configured to render in bright white
            font=(FONT_FAMILY, self.console_font_size),
            bd=0, highlightthickness=0,
            padx=10, pady=10,
            yscrollcommand=scrollbar.set,
            state="disabled",
            wrap=tk.WORD,
        )
        self.console.pack(fill=tk.BOTH, expand=True, pady=4, padx=(4, 0))
        scrollbar.config(command=self.console.yview)

        # Click to focus console so arrow bindings can take effect
        self.console.bind("<Button-1>", lambda e: self.console.focus_set())
        # Custom arrow key bindings to scroll the output text widget
        self.console.bind("<Up>", lambda e: self._scroll_widget(self.console, -1))
        self.console.bind("<Down>", lambda e: self._scroll_widget(self.console, 1))

        # Auto-colored tags inside terminal container
        self.console.tag_configure("error", foreground=COLORS["accent_red"])
        self.console.tag_configure("user_input", foreground=COLORS["accent_cyan"])
        self.console.tag_configure("success", foreground=COLORS["accent_green"])

        # Bottom Input Docking Bar
        input_title = tk.Label(
            parent, text="INPUT (optional)",
            fg=COLORS["text_muted"], bg=COLORS["bg_dark"],
            font=(FONT_FAMILY, 8, "bold"), anchor="w"
        )
        input_title.pack(fill=tk.X, padx=14, pady=(2, 2))

        con_entry_container = RoundedFrame(parent, bg=COLORS["bg_dark"], fill_color=COLORS["bg_panel"], radius=8)
        con_entry_container.pack(fill=tk.X, padx=12, pady=(0, 14))

        self.console_entry = tk.Entry(
            con_entry_container,
            bg=COLORS["bg_panel"],
            fg=COLORS["text_light"],
            insertbackground=COLORS["accent_cyan"],
            bd=0, highlightthickness=0,
            font=(FONT_FAMILY, 10),
        )
        self.console_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=12, pady=8)
        self.console_entry.insert(0, "Type input and press Enter...")
        self.console_entry.bind("<FocusIn>", lambda e: self._on_entry_placeholder_focus(self.console_entry, "Type input and press Enter..."))
        self.console_entry.bind("<Return>", lambda _e: self.send_console_input())

        self._btn_console_send = RoundedButton(
            con_entry_container, "→", self.send_console_input,
            COLORS["accent_cyan"], "#0d9488",
            width=28, height=24, radius=6, text_color="#000000", font_size=10
        )
        self._btn_console_send.pack(side=tk.RIGHT, padx=6)

    def _render_ai_inside(self, parent: tk.Frame) -> None:
        """Builds chatbot interfaces inside the utility container."""
        header = tk.Frame(parent, bg=COLORS["bg_sidebar"])
        header.pack(fill=tk.X, padx=14, pady=(14, 6))

        tk.Label(
            header, text="✨  AI Assistant",
            fg=COLORS["text_light"], bg=COLORS["bg_sidebar"],
            font=(FONT_FAMILY, 10, "bold")
        ).pack(side=tk.LEFT)

        self._btn_ai_config = RoundedButton(
            header, "⚙", self._show_ai_settings,
            COLORS["bg_panel"], COLORS["border_color"],
            width=24, height=24, radius=5, font_size=9,
        )
        self._btn_ai_config.pack(side=tk.RIGHT)

        # Explanatory trigger buttons
        self._btn_ai_explain = RoundedButton(
            parent, "Explain this code", self.ai_explain_current_code,
            COLORS["border_color"], COLORS["accent_cyan"],
            width=180, height=30, radius=8, font_size=8,
        )
        self._btn_ai_explain.pack(fill=tk.X, padx=14, pady=6)

        # Scrollable Text Container Area
        ai_container = RoundedFrame(parent, bg=COLORS["bg_sidebar"], fill_color=COLORS["bg_editor"], radius=12)
        ai_container.pack(fill=tk.BOTH, expand=True, padx=14, pady=8)

        ai_scroll = ttk.Scrollbar(ai_container, orient=tk.VERTICAL, style="App.Vertical.TScrollbar")
        ai_scroll.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 4), pady=4)

        self.ai_output = tk.Text(
            ai_container,
            bg=COLORS["bg_editor"],
            fg=COLORS["text_light"],
            font=(FONT_FAMILY, self.console_font_size),
            bd=0, highlightthickness=0,
            padx=12, pady=12,
            yscrollcommand=ai_scroll.set,
            state="disabled",
            wrap=tk.WORD,
        )
        self.ai_output.pack(fill=tk.BOTH, expand=True, pady=4, padx=(4, 0))
        ai_scroll.config(command=self.ai_output.yview)

        # Tags structure for markdown visualization mappings
        self.ai_output.tag_configure("header", font=(FONT_FAMILY, self.console_font_size, "bold"), foreground=COLORS["accent_cyan"])
        self.ai_output.tag_configure("code", font=(FONT_FAMILY, self.console_font_size), foreground=COLORS["syn_string"], background=COLORS["bg_panel"])
        self.ai_output.tag_configure("system", font=(FONT_FAMILY, self.console_font_size, "italic"), foreground=COLORS["text_muted"])
        self.ai_output.tag_configure("error", font=(FONT_FAMILY, self.console_font_size, "bold"), foreground=COLORS["accent_red"])

        # Bottom Input Docking Prompt Row
        prompt_container = RoundedFrame(parent, bg=COLORS["bg_sidebar"], fill_color=COLORS["bg_panel"], radius=8)
        prompt_container.pack(fill=tk.X, padx=14, pady=14)

        self.ai_entry = tk.Entry(
            prompt_container,
            bg=COLORS["bg_panel"],
            fg=COLORS["text_light"],
            insertbackground=COLORS["accent_cyan"],
            bd=0, highlightthickness=0,
            font=(FONT_FAMILY, 9),
        )
        self.ai_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=8)
        self.ai_entry.insert(0, "Ask anything...")
        self.ai_entry.bind("<FocusIn>", lambda e: self._on_entry_placeholder_focus(self.ai_entry, "Ask anything..."))
        self.ai_entry.bind("<Return>", lambda _e: self.ai_ask_custom())

        self._btn_ai_ask = RoundedButton(
            prompt_container, "➔", self.ai_ask_custom,
            COLORS["accent_cyan"], "#0d9488",
            width=28, height=24, radius=6, text_color="#000000", font_size=10,
        )
        self._btn_ai_ask.pack(side=tk.RIGHT, padx=6)

    def _build_autocomplete_popup(self) -> None:
        self._popup = tk.Toplevel(self.root)
        self._popup.withdraw()
        self._popup.overrideredirect(True)
        self._popup.configure(bg=COLORS["border_color"])

        self._popup_list = tk.Listbox(
            self._popup,
            bg=COLORS["bg_panel"],
            fg=COLORS["text_light"],
            selectbackground=COLORS["accent_cyan"],
            selectforeground="#000000",
            font=(FONT_FAMILY, self.editor_font_size),
            bd=0, highlightthickness=0,
            relief="flat",
            height=6,
            width=25, # Explicit width helps prevent clipping
        )
        self._popup_list.pack(padx=2, pady=2)
        self._popup_list.bind("<ButtonRelease-1>", lambda _e: self._ac_insert())

    def _on_entry_placeholder_focus(self, entry_widget, placeholder) -> None:
        if entry_widget.get() == placeholder:
            entry_widget.delete(0, tk.END)

    def setup_bindings(self) -> None:
        root = self.root
        root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Fullscreen Mode Binding
        root.bind("<F11>", self.toggle_fullscreen)

        # Run / Stop
        root.bind("<Control-r>",       lambda _e: self.run_code())
        root.bind("<Control-R>",       lambda _e: self.run_code())

        # Find File Shortcuts
        root.bind("<Control-f>",       self.show_find_dialog)
        root.bind("<Control-F>",       self.show_find_dialog)

        # File Management
        root.bind("<Control-n>",       lambda e: self.file_new(e))
        root.bind("<Control-N>",       lambda e: self.file_new(e))
        root.bind("<Control-o>",       lambda e: self.file_open(e))
        root.bind("<Control-O>",       lambda e: self.file_open(e))
        root.bind("<Control-s>",       lambda e: self.file_save(e))
        root.bind("<Control-S>",       lambda e: self.file_save(e))
        root.bind("<Control-Shift-s>", lambda e: self.file_save_as(e))
        root.bind("<Control-Shift-S>", lambda e: self.file_save_as(e))
        root.bind("<Control-w>",       lambda _e: self.close_active_tab())
        root.bind("<Control-W>",       lambda _e: self.close_active_tab())

        # Editor font zoom
        root.bind("<Control-equal>",      lambda _e: self._change_editor_font(+1))
        root.bind("<Control-plus>",       lambda _e: self._change_editor_font(+1))
        root.bind("<Control-minus>",      lambda _e: self._change_editor_font(-1))
        root.bind("<Control-MouseWheel>",       self._editor_mousewheel)
        root.bind("<Control-Button-4>",   lambda _e: self._change_editor_font(+1))
        root.bind("<Control-Button-5>",   lambda _e: self._change_editor_font(-1))

        # Console font zoom
        root.bind("<Control-Shift-equal>",      lambda _e: self._change_console_font(+1))
        root.bind("<Control-Shift-plus>",       lambda _e: self._change_console_font(+1))
        root.bind("<Control-Shift-minus>",      lambda _e: self._change_console_font(-1))
        root.bind("<Control-Shift-MouseWheel>",  self._console_mousewheel)
        root.bind("<Control-Shift-Button-4>",   lambda _e: self._change_console_font(+1))
        root.bind("<Control-Shift-Button-5>",   lambda _e: self._change_console_font(-1))

        root.bind("<Configure>", lambda _e: self._ac_hide())

    # ── Workspace Multi-Tab Management ────────────────────────────────────────

    def add_tab(self, file_path="", content="", select=True) -> EditorTab:
        """Creates a brand new tab in the editor space."""
        tab = EditorTab(self.editor_notebook, self, file_path, content)
        self.tabs.append(tab)

        name = os.path.basename(file_path) if file_path else "unsaved_file.py"
        # Display tab item using clean green Python snake icon 🐍 next to name, leaving extra padding for the close button
        self.editor_notebook.add(tab.frame, text=f" 🐍 {name}   ")

        if select:
            self.editor_notebook.select(tab.frame)

        self.editor_notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        tab.line_nums.redraw()
        self._highlight()
        self._refresh_title()
        return tab

    def close_active_tab(self, _event=None) -> str:
        """Safely coordinates tab-closing by targeting currently focused notebook indexes."""
        try:
            current_idx = self.editor_notebook.index("current")
            self.close_tab_by_index(current_idx)
        except tk.TclError:
            pass
        return "break"

    def close_tab_by_index(self, idx: int) -> str:
        """Closes a specific tab index, complete with unsaved prompt triggers."""
        if idx < 0 or idx >= len(self.tabs):
            return "break"
        tab = self.tabs[idx]

        current = tab.editor.get("1.0", "end-1c")
        if current != tab.last_saved_content:
            name = os.path.basename(tab.file_path) if tab.file_path else "unsaved_file.py"
            answer = messagebox.askyesnocancel(
                "Unsaved Changes",
                f"'{name}' has unsaved changes.\nSave before closing?",
            )
            if answer is None:  # Cancel
                return "break"
            if answer:          # Yes -> Save it
                self.editor_notebook.select(tab.frame)
                self.file_save()

        self.editor_notebook.forget(tab.frame)
        self.tabs.pop(idx)

        # Keep at least one blank playground if all are closed
        if not self.tabs:
            self.add_tab(content=WELCOME_CODE)

        self._refresh_title()
        self._update_cursor()
        return "break"

    def _on_tab_changed(self, event) -> None:
        """Triggered whenever a user changes tabs."""
        tab = self.active_tab
        if tab:
            tab.line_nums.redraw()
        self._highlight()
        self._refresh_title()
        self._update_cursor()

    # ── Fullscreen toggle helper ──────────────────────────────────────────────

    def toggle_fullscreen(self, _event=None) -> str:
        is_fullscreen = self.root.attributes("-fullscreen")
        self.root.attributes("-fullscreen", not is_fullscreen)
        self.toggle_dark_mode_border()
        return "break"

    # ── Code execution ────────────────────────────────────────────────────────

    def run_code(self) -> None:
        # Automatically toggle switcher container focus to terminal logs view
        self.show_utility_tab("output")

        if self.process:
            self._console_write("⚠️  Already running — stop it first or wait.\n", tag="error")
            return

        if self.current_file_path:
            self.file_save()

        self.clear_console()
        self._console_write("🚀 Running…\n\n")
        
        if not self.editor:
            return
            
        code = self.editor.get("1.0", "end-1c")
        threading.Thread(
            target=self._execute_in_thread,
            args=(code,),
            daemon=True,
        ).start()

        # Shifts cursor focus directly into the execution prompt entry widget
        self.console_entry.focus_set()

    def _execute_in_thread(self, code: str) -> None:
        if self.current_file_path:
            file_path   = self.current_file_path
            working_dir = os.path.dirname(file_path) or "."
        else:
            tmp_dir   = tempfile.gettempdir()
            file_path = os.path.join(tmp_dir, "pyfirst_run.py")
            working_dir = tmp_dir
            with open(file_path, "w", encoding="utf-8") as fh:
                fh.write(code)

        try:
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            env["PYTHONUTF8"] = "1"

            self.process = subprocess.Popen(
                [sys.executable, "-u", file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,  
                text=True,
                encoding="utf-8",
                errors="replace",       
                cwd=working_dir,
                env=env,
            )
            
            while True:
                char = self.process.stdout.read(1)
                if not char:
                    break
                self.output_queue.put(char)
                
            self.process.stdout.close()
            self.process.wait()
        except Exception as exc:
            self.output_queue.put(f"❌ Launch error: {exc}\n")
        finally:
            self.output_queue.put("\n✅ Done.\n")
            self.process = None
            if not self.current_file_path:
                try:
                    os.remove(file_path)
                except OSError:
                    pass

    def stop_code(self) -> None:
        if self.process:
            self.process.terminate()
            self._console_write("\n🛑 Stopped by user.\n", tag="error")
            self.process = None
        else:
            self._console_write("ℹ️  Nothing is running.\n")

    def send_console_input(self) -> None:
        user_input = self.console_entry.get()
        if user_input == "Type input and press Enter...":
            return
        if self.process and self.process.poll() is None:
            try:
                self.process.stdin.write(user_input + "\n")
                self.process.stdin.flush()
                self._console_write(user_input + "\n", tag="user_input")
            except Exception as e:
                self._console_write(f"\n❌ Failed to send input: {e}\n", tag="error")
        else:
            self._console_write("⚠️  No program is currently running to accept input.\n", tag="error")
        
        self.console_entry.delete(0, tk.END)

    def _poll_output_queue(self) -> None:
        # Pull all currently available raw characters from output_queue
        has_new_chars = False
        try:
            while True:
                char = self.output_queue.get_nowait()
                self.incoming_buffer += char
                has_new_chars = True
        except queue.Empty:
            pass

        if has_new_chars:
            self.last_char_time = time.time()

        # Decide whether to flush the buffer
        # Flush if:
        # 1. We have a newline '\n' in the buffer
        # 2. Or some time (50ms) has passed since the last character (interactive prompt support)
        if self.incoming_buffer:
            current_time = time.time()
            if '\n' in self.incoming_buffer:
                parts = self.incoming_buffer.split('\n')
                # Flush all completed lines
                for line in parts[:-1]:
                    self._flush_line(line + '\n')
                # Retain incomplete line
                self.incoming_buffer = parts[-1]
            elif current_time - self.last_char_time > 0.05:
                self._flush_line(self.incoming_buffer)
                self.incoming_buffer = ""

        self.root.after(50, self._poll_output_queue)

    def _flush_line(self, line: str) -> None:
        if not line:
            return
        tag = ""
        line_lower = line.lower()
        if "error" in line_lower or "exception" in line_lower or "traceback" in line_lower or "failed" in line_lower or "❌" in line:
            tag = "error"
        elif "success" in line_lower or "done" in line_lower or "✅" in line:
            tag = "success"
        
        for char in line:
            self.typing_queue.put((char, tag))

    def _poll_typing_queue(self) -> None:
        q_size = self.typing_queue.qsize()
        if q_size > 0:
            # Smart batching: if the queue is very full, process more characters per tick to avoid infinite lag
            if q_size > 2000:
                batch_size = 30
            elif q_size > 500:
                batch_size = 10
            elif q_size > 100:
                batch_size = 3
            else:
                batch_size = 1

            self.console.configure(state="normal")
            for _ in range(batch_size):
                try:
                    char, tag = self.typing_queue.get_nowait()
                    self.console.insert("end", char, tag)
                except queue.Empty:
                    break
            self.console.see("end")
            self.console.configure(state="disabled")

        self.root.after(30, self._poll_typing_queue)

    def _queue_typing(self, text: str, tag: str = "") -> None:
        if not tag:
            text_lower = text.lower()
            if "✅" in text or "done" in text_lower or "successful" in text_lower:
                tag = "success"
            elif "❌" in text or "error" in text_lower or "⚠️" in text or "failed" in text_lower:
                tag = "error"
        for char in text:
            self.typing_queue.put((char, tag))

    def _console_write(self, text: str, tag: str = "") -> None:
        self._queue_typing(text, tag)

    def clear_console(self) -> None:
        while not self.typing_queue.empty():
            try:
                self.typing_queue.get_nowait()
            except queue.Empty:
                break
        self.console.configure(state="normal")
        self.console.delete("1.0", "end")
        self.console.configure(state="disabled")

    # ── Syntax highlighting ───────────────────────────────────────────────────

    _HIGHLIGHT_PATTERNS = [
        (r'#[^\n]*|"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'', "comment"),
        (r'"[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\'',  "string"),
        (
            r'\b(False|None|True|and|as|assert|async|await|break|class|continue|'
            r'def|del|elif|else|except|finally|for|from|global|if|import|in|is|'
            r'lambda|nonlocal|not|or|pass|raise|return|try|while|with|yield)\b',
            "keyword",
        ),
        (
            r'\b(print|input|len|range|str|int|float|list|dict|set|tuple|open|type|'
            r'abs|max|min|sum|enumerate|zip|map|filter|sorted|reversed|isinstance|'
            r'hasattr|getattr|setattr|repr|format|vars|dir|help|id|hash|chr|ord)\b',
            "builtin",
        ),
        (r'\b(self|cls)\b', "self_cls"),
        (r'\b[a-zA-Z_]\w*(?=\s*\()', "function"), # Identifies function definition and invocation structures
        (r'\b\d+(\.\d+)?\b',   "number"),
        (r'[\(\)\{\}\[\]]',    "bracket"),
        (r'[\+\-\*/%&|^~=<>!]+', "operator"),
        (r'[,;.:]',            "punctuation"),
    ]

    _MASTER_PATTERN: re.Pattern | None = None   

    def _get_pattern(self) -> re.Pattern:
        if PyFirstIDE._MASTER_PATTERN is None:
            parts = [f'(?P<{tag}>{pat})' for pat, tag in self._HIGHLIGHT_PATTERNS]
            PyFirstIDE._MASTER_PATTERN = re.compile("|".join(parts))
        return PyFirstIDE._MASTER_PATTERN

    def _trigger_highlight(self, _event=None) -> None:
        if self._highlight_job:
            self.root.after_cancel(self._highlight_job)
        self._highlight_job = self.root.after(HIGHLIGHT_DELAY_MS, self._highlight)

    def _highlight(self) -> None:
        tab = self.active_tab
        if not tab:
            return

        content = tab.editor.get("1.0", "end-1c")
        for tag in ("keyword","builtin","string","comment","number","bracket","operator","punctuation","function","self_cls"):
            tab.editor.tag_remove(tag, "1.0", "end")

        line_starts = [0]
        for m in re.finditer(r'\n', content):
            line_starts.append(m.end())

        def to_tk(idx: int) -> str:
            line = bisect.bisect_right(line_starts, idx) - 1
            col  = idx - line_starts[line]
            return f"{line + 1}.{col}"

        try:
            for m in re.finditer(self._get_pattern(), content):
                for tag, val in m.groupdict().items():
                    if val is not None:
                        tab.editor.tag_add(tag, to_tk(m.start(tag)), to_tk(m.end(tag)))
        except Exception:
            pass  

        self._check_mistakes(content)

    # ── Mistake Finder ────────────────────────────────────────────────────────

    def _translate_syntax_error(self, msg: str, line_text: str) -> str:
        msg_lower = msg.lower()
        line_text = line_text.strip() if line_text else ""
        
        if "expected ':'" in msg_lower:
            return "You forgot a colon ':' at the end of this line. Try adding one after 'if', 'elif', 'else', 'for', 'while', or 'def'."
        
        if "invalid syntax" in msg_lower or "invalid syntax. Perhaps you forgot a comma?" in msg_lower:
            if "print " in line_text and not ("(" in line_text and ")" in line_text):
                return "In Python 3, 'print' is a function and needs parentheses. Write it like: print('your text')"
            if "=" in line_text and any(line_text.startswith(x) for x in ("if ", "elif ", "while ")) and "==" not in line_text and "!=" not in line_text and "<=" not in line_text and ">=" not in line_text:
                return "You used a single '=' (which assigns a variable). To compare values inside conditions, use '=='. "
            if "for " in line_text and "in" in line_text and "range" in line_text and not ("(" in line_text):
                return "The 'range' function needs parentheses. Try: range(5)"
            return "Python doesn't understand this line. Check for typing mistakes, missing commas, or unclosed quotes."
            
        if "was never closed" in msg_lower or "unclosed" in msg_lower:
            if "(" in line_text or ")" in line_text:
                return "You opened a parenthesis '(' but didn't close it with a matching ')'."
            if "[" in line_text or "]" in line_text:
                return "You opened a square bracket '[' but didn't close it with a matching ']'. Check your lists!"
            if "{" in line_text or "}" in line_text:
                return "You opened a curly bracket '{' but didn't close it with a matching '}'."
            if "'" in line_text or '"' in line_text:
                return "You started a text string with a quote mark but forgot the matching quote mark at the end."
            return f"Unclosed bracket or quote: {msg}"
            
        if "unmatched" in msg_lower:
            return "You have an extra closing bracket or parenthesis that doesn't match any opening one."
            
        if "unexpected indent" in msg_lower:
            return "This line has extra spaces or tabs at the start. Ensure your indents match perfectly!"
            
        if "expected an indented block" in msg_lower:
            return "The line after a colon ':' (like after 'if', 'for', or 'def') must be indented with spaces or a tab."
            
        return msg

    def _check_mistakes(self, code: str) -> None:
        mistakes = []
        tab = self.active_tab
        if not tab:
            return

        try:
            compile(code, "<string>", "exec")
        except SyntaxError as e:
            line_text = ""
            if e.lineno:
                try:
                    line_text = tab.editor.get(f"{e.lineno}.0", f"{e.lineno}.end")
                except tk.TclError:
                    pass
            friendly_msg = self._translate_syntax_error(e.msg, line_text)
            mistakes.append({
                "line": e.lineno or 1,
                "message": friendly_msg,
                "severity": "error"
            })

        if not mistakes:
            try:
                tree = ast.parse(code)
                class BeginnerMistakeVisitor(ast.NodeVisitor):
                    def __init__(self):
                        self.warnings = []
                        
                    def visit_Assign(self, node):
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                if target.id in ["print", "input", "len", "str", "int", "float", "list", "dict", "set", "tuple", "type"]:
                                    self.warnings.append({
                                        "line": node.lineno,
                                        "message": f"You redefined the built-in function '{target.id}'. This might break your code if you try to use '{target.id}()' later!",
                                        "severity": "warning"
                                    })
                        self.generic_visit(node)
                        
                    def visit_Compare(self, node):
                        for op in node.ops:
                            if isinstance(op, (ast.Is, ast.IsNot)):
                                for comparator in node.comparators:
                                    if isinstance(comparator, (ast.Constant, ast.Num, ast.Str)):
                                        self.warnings.append({
                                            "line": node.lineno,
                                            "message": "Using 'is' or 'is not' to compare text or numbers is unreliable. Use '==' or '!=' instead.",
                                            "severity": "warning"
                                        })
                        self.generic_visit(node)

                    def visit_Expr(self, node):
                        if isinstance(node.value, ast.Name):
                            name_id = node.value.id
                            if name_id in PYTHON_BUILTINS or name_id in AUTOCOMPLETE_WORDS:
                                self.warnings.append({
                                    "line": node.lineno,
                                    "message": f"You wrote '{name_id}' but did not call it. Did you forget parentheses? Try: {name_id}()",
                                    "severity": "warning"
                                })
                        self.generic_visit(node)
                        
                visitor = BeginnerMistakeVisitor()
                visitor.visit(tree)
                mistakes.extend(visitor.warnings)
            except Exception:
                pass

        tab.editor.tag_remove("error_marker", "1.0", "end")
        if mistakes:
            first = mistakes[0]
            self.current_mistake_line = first["line"]
            prefix = "❌" if first["severity"] == "error" else "💡"
            self.mistakes_label.config(
                text=f"{prefix} Line {first['line']}: {first['message']}",
                fg=COLORS["accent_amber"] if first["severity"] == "warning" else COLORS["accent_red"]
            )
            self._status_dot.config(fg=COLORS["accent_red"])
                
            try:
                tab.editor.tag_add("error_marker", f"{first['line']}.0", f"{first['line']}.end")
            except tk.TclError:
                pass
        else:
            self.current_mistake_line = None
            self.mistakes_label.config(
                text="✓ No issues found - Looking good!",
                fg=COLORS["text_muted"]
            )
            self._status_dot.config(fg=COLORS["accent_green"])

    def _jump_to_mistake(self, _event=None) -> None:
        if self.current_mistake_line is not None and self.editor:
            self.editor.mark_set("insert", f"{self.current_mistake_line}.0")
            self.editor.see(f"{self.current_mistake_line}.0")
            self.editor.focus_set()
            self._update_cursor()

    # ── Search & Find (Ctrl+F) Dialog ────────────────────────────────────────

    def show_find_dialog(self, _event=None) -> None:
        """Launches localized visual find text search helper."""
        if not self.editor:
            return

        win = tk.Toplevel(self.root)
        win.title("🔍 Find Text")
        win.geometry("360x130")
        win.configure(bg=COLORS["bg_panel"])
        win.transient(self.root)
        win.resizable(False, False)

        tk.Label(
            win, text="Search for:",
            fg=COLORS["text_light"], bg=COLORS["bg_panel"],
            font=(FONT_FAMILY, 10)
        ).pack(anchor="w", padx=15, pady=(15, 2))

        search_entry = tk.Entry(
            win, bg=COLORS["bg_dark"], fg=COLORS["text_light"],
            insertbackground=COLORS["accent_cyan"], bd=0, font=(FONT_FAMILY, 10)
        )
        search_entry.pack(fill=tk.X, padx=15, pady=5, ipady=4)
        search_entry.focus_set()

        btn_frame = tk.Frame(win, bg=COLORS["bg_panel"])
        btn_frame.pack(fill=tk.X, padx=15, pady=10)

        # Track last search text location
        search_pos = ["1.0"]

        def find_next():
            word = search_entry.get()
            if not word or not self.editor:
                return

            self.editor.tag_remove("search_highlight", "1.0", "end")

            start_pos = search_pos[0]
            idx = self.editor.search(word, start_pos, stopindex="end", nocase=True)
            if not idx:
                # Wrap search context around from start
                idx = self.editor.search(word, "1.0", stopindex="end", nocase=True)
            
            if idx:
                end_idx = f"{idx} + {len(word)} chars"
                self.editor.tag_add("search_highlight", idx, end_idx)
                self.editor.mark_set("insert", idx)
                self.editor.see(idx)
                search_pos[0] = end_idx
            else:
                self._set_status(f"No matches found for '{word}'")

        RoundedButton(
            btn_frame, "Find Next", find_next,
            COLORS["accent_cyan"], "#0284c7",
            width=100, height=26, radius=6, text_color="#000000"
        ).pack(side=tk.LEFT)

        search_entry.bind("<Return>", lambda e: find_next())

    # ── AI Assistant Core Logic ───────────────────────────────────────────────

    def _write_ai_output(self, text: str, tag: str = "") -> None:
        self.ai_output.configure(state="normal")
        if tag:
            self.ai_output.insert("end", text, tag)
        else:
            self.ai_output.insert("end", text)
        self.ai_output.see("end")
        self.ai_output.configure(state="disabled")

    def _clear_ai_output(self) -> None:
        self.ai_output.configure(state="normal")
        self.ai_output.delete("1.0", "end")
        self.ai_output.configure(state="disabled")

    def _show_ai_settings(self) -> None:
        win = tk.Toplevel(self.root)
        win.title("🤖 AI Assistant Config")
        win.geometry("420x340")
        win.configure(bg=COLORS["bg_panel"])
        win.transient(self.root)
        win.grab_set()

        tk.Label(
            win, text="🤖 Configure AI Assistant",
            fg=COLORS["accent_cyan"], bg=COLORS["bg_panel"],
            font=(FONT_FAMILY, 12, "bold"),
        ).pack(pady=12)

        form = tk.Frame(win, bg=COLORS["bg_panel"])
        form.pack(fill=tk.BOTH, expand=True, padx=20)

        # Provider Selection
        tk.Label(form, text="AI Provider:", fg=COLORS["text_light"], bg=COLORS["bg_panel"], font=(FONT_FAMILY, 9)).grid(row=0, column=0, sticky="w", pady=5)
        prov_var = tk.StringVar(value=self.ai_provider)
        prov_dropdown = ttk.Combobox(
            form, textvariable=prov_var, state="readonly", width=25,
            values=["Free AI (Pollinations.ai)", "Ollama (Local)", "Google Gemini", "OpenAI", "Custom API"],
        )
        prov_dropdown.grid(row=0, column=1, sticky="w", pady=5, padx=10)

        # Endpoint URL
        tk.Label(form, text="API Endpoint:", fg=COLORS["text_light"], bg=COLORS["bg_panel"], font=(FONT_FAMILY, 9)).grid(row=1, column=0, sticky="w", pady=5)
        end_entry = tk.Entry(form, bg=COLORS["bg_dark"], fg=COLORS["text_light"], insertbackground=COLORS["accent_cyan"], width=28, bd=0)
        end_entry.insert(0, self.ai_endpoint)
        end_entry.grid(row=1, column=1, sticky="w", pady=5, padx=10, ipady=3)

        # API Key
        tk.Label(form, text="API Key:", fg=COLORS["text_light"], bg=COLORS["bg_panel"], font=(FONT_FAMILY, 9)).grid(row=2, column=0, sticky="w", pady=5)
        key_entry = tk.Entry(form, bg=COLORS["bg_dark"], fg=COLORS["text_light"], insertbackground=COLORS["accent_cyan"], width=28, bd=0, show="*")
        key_entry.insert(0, self.ai_api_key)
        key_entry.grid(row=2, column=1, sticky="w", pady=5, padx=10, ipady=3)

        # Model Target
        tk.Label(form, text="Model Name:", fg=COLORS["text_light"], bg=COLORS["bg_panel"], font=(FONT_FAMILY, 9)).grid(row=3, column=0, sticky="w", pady=5)
        mod_entry = tk.Entry(form, bg=COLORS["bg_dark"], fg=COLORS["text_light"], insertbackground=COLORS["accent_cyan"], width=28, bd=0)
        mod_entry.insert(0, self.ai_model)
        mod_entry.grid(row=3, column=1, sticky="w", pady=5, padx=10, ipady=3)

        def update_fields(_event=None):
            p = prov_var.get()
            if p == "Free AI (Pollinations.ai)":
                end_entry.delete(0, tk.END)
                end_entry.insert(0, "https://gen.pollinations.ai")
                mod_entry.delete(0, tk.END)
                mod_entry.insert(0, "openai")
                key_entry.config(state="normal")
            elif p == "Ollama (Local)":
                end_entry.delete(0, tk.END)
                end_entry.insert(0, "http://localhost:11434")
                mod_entry.delete(0, tk.END)
                mod_entry.insert(0, "qwen2.5:1.5b")
                key_entry.config(state="disabled")
            elif p == "Google Gemini":
                end_entry.delete(0, tk.END)
                end_entry.insert(0, "https://generativelanguage.googleapis.com")
                mod_entry.delete(0, tk.END)
                mod_entry.insert(0, "gemini-2.5-flash")
                key_entry.config(state="normal")
            elif p == "OpenAI":
                end_entry.delete(0, tk.END)
                end_entry.insert(0, "https://api.openai.com/v1")
                mod_entry.delete(0, tk.END)
                mod_entry.insert(0, "gpt-4o-mini")
                key_entry.config(state="normal")
            elif p == "Custom API":
                key_entry.config(state="normal")
        
        prov_dropdown.bind("<<ComboboxSelected>>", update_fields)
        if self.ai_provider == "Ollama (Local)":
            key_entry.config(state="disabled")

        def save():
            self.ai_provider = prov_var.get()
            self.ai_endpoint = end_entry.get().strip()
            self.ai_api_key  = key_entry.get().strip()
            self.ai_model    = mod_entry.get().strip()
            win.destroy()
            self._write_ai_output("🤖 AI configuration saved successfully.\n", tag="system")

        RoundedButton(
            win, "SAVE CONFIG", save,
            COLORS["accent_cyan"], "#0284c7",
            width=120, height=30, radius=8, text_color="#000000",
        ).pack(pady=15)

    def ai_ask_custom(self) -> None:
        # Switch switcher utility container to the AI Assistant tab
        self.show_utility_tab("ai")

        query = self.ai_entry.get().strip()
        if not query or query == "Ask anything...":
            return
        self.ai_entry.delete(0, tk.END)
        self._write_ai_output(f"\n👤 You: {query}\n", tag="header")

        if not self.editor:
            return
            
        code = self.editor.get("1.0", "end-1c")
        full_prompt = (
            "You are a friendly and encouraging Python tutor assisting a beginner. "
            f"Here is the student's current Python code:\n```python\n{code}\n```\n\n"
            f"The student asks: \"{query}\"\n\n"
            "Keep your explanation simple, clear, and highly encouraging. Guide them step-by-step!"
        )
        self._write_ai_output("🤖 Thinking…\n", tag="system")
        threading.Thread(target=self._ai_worker, args=(full_prompt,), daemon=True).start()

    def ai_explain_current_code(self) -> None:
        # Switch switcher utility container to the AI Assistant tab
        self.show_utility_tab("ai")

        if not self.editor:
            return
            
        code = self.editor.get("1.0", "end-1c").strip()
        if not code:
            self._write_ai_output("ℹ️ Write some code in the editor first so I can explain it!\n", tag="system")
            return

        current_mistake = self.mistakes_label.cget("text")
        mistake_context = ""
        if "No mistakes found" not in current_mistake:
            mistake_context = f"The IDE currently flags this issue: {current_mistake}\n"

        full_prompt = (
            "You are an encouraging Python tutor helping a beginner. Analyze their code and explain what it does. "
            "If there is an error, guide them gently to understand why it happens and suggest a step-by-step fix. "
            "Always include highly explanatory, simple commentary.\n\n"
            f"Code:\n```python\n{code}\n```\n\n"
            f"{mistake_context}"
            "Please provide a simple breakdown of the code's objective, and a friendly explanation of any issues."
        )
        self._clear_ai_output()
        self._write_ai_output("🤖 Reviewing your code…\n", tag="system")
        threading.Thread(target=self._ai_worker, args=(full_prompt,), daemon=True).start()

    def _ai_worker(self, prompt: str) -> None:
        import urllib.request
        import json
        import ssl

        # Local bypass support for educational environments with strict SSL
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        provider = self.ai_provider
        endpoint = self.ai_endpoint.rstrip("/")
        api_key  = self.ai_api_key
        model    = self.ai_model

        url = ""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0"
        }
        payload = {}

        try:
            if provider == "Free AI (Pollinations.ai)":
                url = f"{endpoint}/v1/chat/completions"
                if api_key:
                    headers["Authorization"] = f"Bearer {api_key}"
                payload = {
                    "model": model or "openai",
                    "messages": [
                        {"role": "system", "content": "You are an encouraging Python tutor helping a beginner learn programming. Keep explanations friendly and structured."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7
                }
            elif provider == "Ollama (Local)":
                url = f"{endpoint}/api/generate"
                payload = {
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                }
            elif provider == "Google Gemini":
                url = f"{endpoint}/v1beta/models/{model}:generateContent?key={api_key}"
                payload = {
                    "contents": [{
                        "parts": [{
                            "text": prompt
                        }]
                    }]
                }
            elif provider in ("OpenAI", "Custom API"):
                url = f"{endpoint}/chat/completions"
                if api_key:
                    headers["Authorization"] = f"Bearer {api_key}"
                payload = {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7
                }

            data_bytes = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data_bytes, headers=headers, method="POST")

            with urllib.request.urlopen(req, timeout=30, context=ctx) as response:
                resp_data = response.read().decode("utf-8")

            extra = ""
            if provider == "Free AI (Pollinations.ai)" or provider in ("OpenAI", "Custom API"):
                try:
                    resp_json = json.loads(resp_data)
                    if "choices" in resp_json:
                        extra = resp_json["choices"][0]["message"]["content"]
                    else:
                        extra = str(resp_json)
                except json.JSONDecodeError:
                    extra = resp_data
            elif provider == "Ollama (Local)":
                resp_json = json.loads(resp_data)
                extra = resp_json.get("response", "")
            elif provider == "Google Gemini":
                resp_json = json.loads(resp_data)
                try:
                    extra = resp_json["candidates"][0]["content"]["parts"][0]["text"]
                except KeyError:
                    extra = f"Gemini API returned unexpected structure: {resp_json}"

            self._render_ai_response(extra)

        except Exception as exc:
            err_msg = str(exc)
            if provider == "Free AI (Pollinations.ai)":
                err_msg += (
                    "\n\n💡 Tip: Pollinations.ai has updated its system and now requires a free API key to prevent automated spam. "
                    "Getting a key is 100% free, unlimited, and instant!\n\n"
                    "How to fix this in 3 easy steps:\n"
                    "1. Visit https://enter.pollinations.ai and log in with your GitHub account to get your free API key.\n"
                    "2. In your PyFirst IDE, click the '⚙ Settings' button in the top-right of this AI Assistant pane.\n"
                    "3. Paste your free API key (the one starting with 'sk_') and click 'SAVE CONFIG'."
                )
            elif "localhost" in url or "127.0.0.1" in url:
                err_msg += "\n\n💡 Tip: Is Ollama running on your machine? Open your terminal and run 'ollama run qwen2.5:1.5b' to start it locally."
            elif "gemini" in url and not api_key:
                err_msg += "\n\n💡 Tip: Google Gemini requires an API key from Google AI Studio. You can get one for free and paste it in ⚙ AI Settings!"
            
            self._write_ai_output(f"\n❌ Connection Error: {err_msg}\n", tag="error")

    def _render_ai_response(self, text: str) -> None:
        self.ai_output.configure(state="normal")
        parts = text.split("```")
        for i, part in enumerate(parts):
            if i % 2 == 1: 
                code_text = part
                lines = part.split("\n")
                if lines and lines[0] in ("python", "py", "javascript", "js", "html", "css", "bash"):
                    code_text = "\n".join(lines[1:])
                self.ai_output.insert("end", f"\n{code_text.strip()}\n", "code")
            else:
                self.ai_output.insert("end", part)
        self.ai_output.insert("end", "\n\n")
        self.ai_output.see("end")
        self.ai_output.configure(state="disabled")

    # ── Editor event handlers ─────────────────────────────────────────────────

    def _on_key_release(self, event: tk.Event) -> None:
        if event.keysym not in (
            "Left", "Right", "Up", "Down",
            "Control_L", "Control_R", "Shift_L", "Shift_R",
            "Alt_L", "Alt_R", "Caps_Lock",
        ):
            self._show_autocomplete()

        self._trigger_highlight(event)
        if self.line_nums:
            self.line_nums.redraw()
        self._update_cursor()

    def _on_key_press(self, event: tk.Event):
        char = event.char
        if not char or not self.editor:
            return None

        PAIRS = {"(": ")", "[": "]", "{": "}", '"': '"', "'": "'"}
        CLOSING = set(PAIRS.values())

        if char in CLOSING:
            try:
                nxt = self.editor.get("insert", "insert + 1 chars")
                if nxt == char:
                    self.editor.mark_set("insert", "insert + 1 chars")
                    self._update_cursor()
                    return "break"
            except tk.TclError:
                pass

        if char in PAIRS:
            closing = PAIRS[char]
            self.editor.insert("insert", char + closing)
            self.editor.mark_set("insert", "insert - 1 chars")
            self._trigger_highlight()
            if self.line_nums:
                self.line_nums.redraw()
            self._update_cursor()
            return "break"

        return None

    def _on_backspace(self, event: tk.Event):
        PAIRS = {"(": ")", "[": "]", "{": "}", '"': '"', "'": "'"}
        if not self.editor:
            return
        try:
            prev = self.editor.get("insert - 1 chars", "insert")
            nxt  = self.editor.get("insert", "insert + 1 chars")
            if prev in PAIRS and nxt == PAIRS[prev]:
                self.editor.delete("insert - 1 chars", "insert + 1 chars")
                if self.line_nums:
                    self.line_nums.redraw()
                self._update_cursor()
                return "break"
        except tk.TclError:
            pass

    def _on_editor_click(self, _event: tk.Event) -> None:
        self._ac_hide()
        self.root.after(10, self._update_cursor)

    def _on_return_pressed(self, event: tk.Event) -> str:
        """Handles smart auto-indentation and autocomplete selection on pressing Enter."""
        if self._ac_visible():
            self._ac_insert()
            return "break"

        editor = event.widget
        try:
            cursor_idx = editor.index("insert")
            line_num = int(cursor_idx.split(".")[0])
            line_content = editor.get(f"{line_num}.0", "insert")

            whitespace_match = re.match(r"^([ \t]*)", line_content)
            leading_whitespace = whitespace_match.group(1) if whitespace_match else ""

            no_comment = re.sub(r"#.*$", "", line_content).rstrip()

            if no_comment.endswith(":"):
                new_indent = leading_whitespace + "    "
            else:
                new_indent = leading_whitespace

            editor.insert("insert", "\n" + new_indent)
            editor.see("insert")

            if self.line_nums:
                self.line_nums.redraw()
            self._trigger_highlight()
            self._update_cursor()
            return "break"
        except Exception:
            return None

    # ── Cursor position indicator ─────────────────────────────────────────────

    def _update_cursor(self) -> None:
        if not self.editor:
            return
        try:
            line, col = self.editor.index("insert").split(".")
            self._cursor_label.config(text=f"Ln {line}, Col {col}")
        except tk.TclError:
            pass

    # ── Autocomplete ──────────────────────────────────────────────────────────

    def _ac_word_at_cursor(self) -> tuple[str, str | None]:
        if not self.editor:
            return "", None
        try:
            line_idx, col_idx = map(int, self.editor.index("insert").split("."))
            line_text = self.editor.get(f"{line_idx}.0", f"{line_idx}.{col_idx}")
            m = re.search(r'\b[a-zA-Z_]\w*$', line_text)
            if m:
                word  = m.group(0)
                start = f"{line_idx}.{col_idx - len(word)}"
                return word, start
        except (tk.TclError, ValueError):
            pass
        return "", None

    def _ac_visible(self) -> bool:
        try:
            return bool(self._popup.winfo_viewable())
        except tk.TclError:
            pass
        return False

    def _ac_hide(self) -> None:
        try:
            if self._ac_visible():
                self._popup.withdraw()
        except tk.TclError:
            pass

    def _show_autocomplete(self) -> None:
        if not self.editor:
            return
        word, _ = self._ac_word_at_cursor()
        if not word:
            self._ac_hide()
            return

        matches = [w for w in AUTOCOMPLETE_WORDS if w.lower().startswith(word.lower())]
        if not matches or (len(matches) == 1 and matches[0] == word):
            self._ac_hide()
            return

        self._popup_list.delete(0, "end")
        for item in matches:
            self._popup_list.insert("end", item)
        self._popup_list.selection_set(0)
        self._popup_list.configure(height=min(len(matches), 7))

        try:
            bbox = self.editor.bbox("insert")
            if bbox:
                x, y, _w, h = bbox
                rx = self.editor.winfo_rootx() + x
                # Increased vertical buffer to 12px ensuring the menu is rendered safely below the typing text
                ry = self.editor.winfo_rooty() + y + h + 12
                self._popup.geometry(f"+{rx}+{ry}")
                self._popup.deiconify()
                self._popup.lift()
        except tk.TclError:
            pass

    def _ac_insert(self) -> None:
        if not self.editor:
            return
        sel = self._popup_list.curselection()
        if not sel:
            return
        chosen = self._popup_list.get(sel[0])
        word, start = self._ac_word_at_cursor()
        if start:
            end = self.editor.index("insert")
            self.editor.delete(start, end)
            self.editor.insert(start, chosen)
        self._ac_hide()
        self._highlight()
        if self.line_nums:
            self.line_nums.redraw()
        self._update_cursor()

    # Autocomplete navigation bindings
    def _ac_up(self, _event):
        if not self._ac_visible():
            return None
        sel = self._popup_list.curselection()
        if sel and sel[0] > 0:
            self._popup_list.selection_clear(sel[0])
            self._popup_list.selection_set(sel[0] - 1)
            self._popup_list.see(sel[0] - 1)
        elif not sel:
            self._popup_list.selection_set(0)
        return "break"

    def _ac_down(self, _event):
        if not self._ac_visible():
            return None
        sel  = self._popup_list.curselection()
        last = self._popup_list.size() - 1
        if sel and sel[0] < last:
            self._popup_list.selection_clear(sel[0])
            self._popup_list.selection_set(sel[0] + 1)
            self._popup_list.see(sel[0] + 1)
        elif not sel:
            self._popup_list.selection_set(0)
        return "break"

    def _ac_tab(self, _event):
        if self._ac_visible():
            self._ac_insert()
            return "break"
        return None

    def _ac_escape(self, _event):
        if self._ac_visible():
            self._ac_hide()
            return "break"
        return None

    # ── Font size controls ────────────────────────────────────────────────────

    def _change_editor_font(self, delta: int) -> None:
        """Scales Code Editor context text independently."""
        self.editor_font_size = max(FONT_MIN, min(FONT_MAX, self.editor_font_size + delta))
        for t in self.tabs:
            t.editor.configure(font=(FONT_FAMILY, self.editor_font_size))
            t.line_nums.redraw()
        self._popup_list.configure(font=(FONT_FAMILY, self.editor_font_size))

    def _change_console_font(self, delta: int) -> None:
        """Scales Console Terminal output text independently."""
        self.console_font_size = max(FONT_MIN, min(FONT_MAX, self.console_font_size + delta))
        self.console.configure(font=(FONT_FAMILY, self.console_font_size))
        self.ai_output.configure(font=(FONT_FAMILY, self.console_font_size))

    def _editor_mousewheel(self, event: tk.Event) -> str:
        self._change_editor_font(+1 if event.delta > 0 else -1)
        return "break"

    def _console_mousewheel(self, event: tk.Event) -> str:
        self._change_console_font(+1 if event.delta > 0 else -1)
        return "break"

    def _scroll_widget(self, widget: tk.Text, direction: int) -> str:
        """Scrolls the specified text widget up or down in units on arrow press."""
        widget.yview_scroll(direction, "units")
        return "break"

    # ── File management ───────────────────────────────────────────────────────

    def file_new(self, _event=None):
        self.add_tab(file_path="", content="# Start coding here!\n")
        self._set_status("Created empty file tab.")
        return "break"

    def file_open(self, _event=None):
        path = filedialog.askopenfilename(
            filetypes=[("Python Files", "*.py"), ("All Files", "*.*")],
            title="Open a Python File",
        )
        if path:
            for idx, tab in enumerate(self.tabs):
                if tab.file_path == path:
                    self.editor_notebook.select(tab.frame)
                    self._set_status(f"Switched to: {os.path.basename(path)}")
                    return "break"

            try:
                with open(path, "r", encoding="utf-8") as fh:
                    content = fh.read()

                active = self.active_tab
                if active and not active.file_path and active.editor.get("1.0", "end-1c").strip() == "":
                    active.file_path = path
                    active.last_saved_content = content
                    active.editor.delete("1.0", "end")
                    active.editor.insert("1.0", content)
                    self.editor_notebook.tab(active.frame, text=f" 🐍 {os.path.basename(path)}   ")
                    self._highlight()
                    active.line_nums.redraw()
                else:
                    self.add_tab(file_path=path, content=content)

                self._set_status(f"Opened: {os.path.basename(path)}")
            except Exception as exc:
                messagebox.showerror("Open Error", f"Could not open file:\n{exc}")
        return "break"

    def file_save(self, _event=None):
        if not self.current_file_path:
            return self.file_save_as()
        self._do_save(self.current_file_path)
        return "break"

    def file_save_as(self, _event=None):
        path = filedialog.asksaveasfilename(
            defaultextension=".py",
            filetypes=[("Python Files", "*.py"), ("All Files", "*.*")],
            title="Save As…",
        )
        if path:
            self.current_file_path = path
            self._do_save(path)
            self._refresh_title()
        return "break"

    def _do_save(self, path: str) -> None:
        if not self.editor:
            return
        try:
            content = self.editor.get("1.0", "end-1c")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(content)
            self.last_saved_content = content

            tab = self.active_tab
            if tab:
                self.editor_notebook.tab(tab.frame, text=f" 🐍 {os.path.basename(path)}   ")
        except Exception as exc:
            self._set_status(f"⚠️  Save failed: {exc}")

    def _auto_save_tick(self) -> None:
        if self.auto_save_enabled.get():
            autosaved_count = 0
            for tab in self.tabs:
                if tab.file_path:
                    content = tab.editor.get("1.0", "end-1c")
                    if content != tab.last_saved_content:
                        try:
                            with open(tab.file_path, "w", encoding="utf-8") as fh:
                                fh.write(content)
                            tab.last_saved_content = content
                            autosaved_count += 1
                        except Exception:
                            pass
            if autosaved_count > 0:
                self._set_status(f"⏱ Auto-saved {autosaved_count} file(s) at {time.strftime('%H:%M:%S')}")
        self.root.after(AUTO_SAVE_MS, self._auto_save_tick)

    # ── Status / title helpers ────────────────────────────────────────────────

    def _set_status(self, msg: str) -> None:
        self.mistakes_label.config(text=msg, fg=COLORS["accent_cyan"])

    def _refresh_title(self) -> None:
        tab = self.active_tab
        if tab and tab.file_path:
            name = os.path.basename(tab.file_path)
            self.root.title(f"🐍 PyFirst — {name}")
            self._active_file_lbl.config(text=f"🐍 {name}")
        elif tab:
            self.root.title(APP_NAME)
            self._active_file_lbl.config(text="🐍 unsaved_file.py")
        else:
            self.root.title(APP_NAME)
            self._active_file_lbl.config(text="🐍 No files open")

    # ── Lesson templates ──────────────────────────────────────────────────────

    def _apply_template(self, _event=None) -> None:
        key  = self._template_var.get()
        code = TEMPLATES.get(key)
        if not code:
            return
            
        self.add_tab(file_path="", content=code)
        self._set_status(f"📚 Loaded Lesson: {key}")
        self._template_var.set("")   

    def _load_welcome(self) -> None:
        self.add_tab(file_path="", content=WELCOME_CODE)

    # ── Settings Gear popup dropdown ──────────────────────────────────────────

    def show_settings_popup(self, event) -> None:
        """Post-cascading popup menu mapping top level items inside Settings button."""
        menu_cfg = dict(
            bg=COLORS["bg_sidebar"],
            fg=COLORS["text_light"],
            activebackground=COLORS["accent_cyan"],
            activeforeground="#0e0f17",
            tearoff=0,
            relief="flat",
        )
        popup_menu = tk.Menu(self.root, **menu_cfg)

        # File Subcategory
        file_sub = tk.Menu(popup_menu, **menu_cfg)
        file_sub.add_command(label="📄  New Tab",         command=self.file_new)
        file_sub.add_command(label="📂  Open File…",      command=self.file_open)
        file_sub.add_command(label="💾  Save Current",    command=self.file_save)
        file_sub.add_command(label="💾  Save As…",        command=self.file_save_as)
        file_sub.add_command(label="❌  Close Tab",       command=self.close_active_tab)
        popup_menu.add_cascade(label="📂 File Operations", menu=file_sub)

        # Dark Mode Subcategory
        dark_sub = tk.Menu(popup_menu, **menu_cfg)
        dark_sub.add_checkbutton(
            label="🌙  Dark Mode Boundary (Title Bar)",
            variable=self.dark_mode_var,
            command=self.toggle_dark_mode_border,
        )
        popup_menu.add_cascade(label="🌙 Theme Settings", menu=dark_sub)

        # Help Subcategory
        help_sub = tk.Menu(popup_menu, **menu_cfg)
        help_sub.add_command(label="⌨  Keyboard Shortcuts", command=self._show_shortcuts)
        help_sub.add_command(label="ℹ  About PyFirst",      command=self._show_about)
        popup_menu.add_cascade(label="ℹ Help & About", menu=help_sub)

        popup_menu.post(event.x_root, event.y_root)

    # ── Help dialogs ─────────────

    def _show_shortcuts(self) -> None:
        msg = (
            "⌨  Keyboard Shortcuts\n"
            "─────────────────────────────\n"
            "F11             Toggle Fullscreen\n"
            "Ctrl+R          Run code\n"
            "Ctrl+F          Find text\n"
            "Ctrl+S          Save file\n"
            "Ctrl+Shift+S    Save As…\n"
            "Ctrl+N          New file tab\n"
            "Ctrl+O          Open file\n"
            "Ctrl+W          Close current tab\n"
            "Ctrl+= / Ctrl+- Zoom editor font\n"
            "Ctrl+Scroll     Zoom editor font\n"
            "Ctrl+Shift+=/-  Zoom console font\n"
            "Tab / Enter     Accept autocomplete\n"
            "Escape          Dismiss autocomplete\n"
        )
        messagebox.showinfo("Keyboard Shortcuts", msg)

    def _show_about(self) -> None:
        msg = (
            f"🐍 PyFirst IDE  {APP_VERSION}\n\n"
            "A beginner-friendly Python editor designed\n"
            "to help you learn Python step by step.\n\n"
            "Features:\n"
            "  • Smart auto-indentation inside code blocks\n"
            "  • VS Code-inspired Multiple File Workspace\n"
            "  • Out-of-the-box Free AI Assistant\n"
            "  • Syntax highlighting & Mistake Finder\n"
            "  • Autocomplete for Python keywords\n"
            "  • Switchable Utility Panel (Output & AI Assistant)\n"
            "  • Independent editor & output font zoom\n"
            "  • Auto-save & bracket auto-pairing\n"
        )
        messagebox.showinfo("About PyFirst", msg)

    # ── Theme toggles ─────────────────────────────────────────────────────────

    def toggle_dark_mode_border(self) -> None:
        try:
            import ctypes as ct
            self.root.update()
            hwnd = ct.windll.user32.GetParent(self.root.winfo_id())
            if not hwnd:
                hwnd = self.root.winfo_id()
            
            val = 2 if self.dark_mode_var.get() else 0
            value = ct.c_int(val)
            
            for attr in (20, 19):
                ct.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, attr, ct.byref(value), ct.sizeof(value)
                )
        except Exception:
            pass

    # ── Application close ─────────────────────────────────────────────────────

    def _on_close(self) -> None:
        unsaved_tabs = []
        for tab in self.tabs:
            current = tab.editor.get("1.0", "end-1c")
            if current != tab.last_saved_content:
                name = os.path.basename(tab.file_path) if tab.file_path else "unsaved_file.py"
                unsaved_tabs.append((tab, name))
                
        if unsaved_tabs:
            msg = "The following tabs have unsaved changes:\n"
            for _, name in unsaved_tabs:
                msg += f"  • {name}\n"
            msg += "\nDo you want to save them before exiting?"
            
            answer = messagebox.askyesnocancel("Unsaved Changes", msg)
            if answer is None: 
                return
            if answer:         
                old_active = self.active_tab
                for tab, _ in unsaved_tabs:
                    self.editor_notebook.select(tab.frame)
                    self.file_save()
                if old_active and old_active in self.tabs:
                    self.editor_notebook.select(old_active.frame)

        if self.process:
            try:
                self.process.terminate()
            except Exception:
                pass
        self.root.destroy()


# ---------------------------------------------------------------------------
# Entry Point / Secure Splash Launcher
# ---------------------------------------------------------------------------

def show_splash_screen(root, on_complete_callback):
    """
    Renders a centered, secure password screen on startup.
    Uses window transparent properties on Windows OS to render rounded borders.
    """
    splash = tk.Toplevel(root)
    splash.overrideredirect(True)
    set_app_icon(splash)
    
    # Enable window-level color transparency for rounded corners
    splash.configure(bg="#010101")
    try:
        splash.attributes("-transparentcolor", "#010101")
    except Exception:
        pass
    
    width, height = 520, 420
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    x = (screen_w - width) // 2
    y = (screen_h - height) // 2
    splash.geometry(f"{width}x{height}+{x}+{y}")
    
    # Custom rounded frame container with a bright cyan outline border
    content = RoundedFrame(
        splash, 
        bg="#010101", 
        fill_color=COLORS["bg_editor"], 
        radius=25, 
        outline=COLORS["accent_cyan"], 
        outline_width=2
    )
    content.pack(expand=True, fill=tk.BOTH)
    
    # Functional exit / minimize helper routines for Splash context
    def close_splash():
        root.destroy()
        
    def minimize_splash():
        splash.withdraw()
        root.iconify()
        # Restores the splash window when the host is unminimized
        def on_deiconify(event):
            if root.state() == "normal":
                splash.deiconify()
                root.unbind("<Map>")
        root.bind("<Map>", on_deiconify)

    # Decorative macOS-style window control dots (Red, Yellow, Green) on top margin
    dots_container = tk.Frame(content, bg=COLORS["bg_editor"])
    dots_container.place(x=24, y=24) # Margins shifted slightly down/right to naturally align inside curves
    create_mac_dots(
        dots_container, 
        COLORS["bg_editor"], 
        size=16, 
        on_close=close_splash, 
        on_minimize=minimize_splash
    ).pack()
    
    # Render snake logo glyph colored to your light green accent colour
    logo_lbl = tk.Label(
        content,
        text="🐍",
        font=("Segoe UI Emoji", 48),
        bg=COLORS["bg_editor"],
        fg=COLORS["accent_green"]
    )
    logo_lbl.pack(pady=(45, 5))
    
    title_lbl = tk.Label(
        content,
        text="PyFirst",
        font=(FONT_FAMILY, 28, "bold"),
        bg=COLORS["bg_editor"],
        fg=COLORS["accent_cyan"]
    )
    title_lbl.pack()
    
    sub_lbl = tk.Label(
        content,
        text="Your Python Playground",
        font=(FONT_FAMILY, 11, "italic"),
        bg=COLORS["bg_editor"],
        fg=COLORS["text_muted"] # Softened text contrast
    )
    sub_lbl.pack(pady=(2, 5))

    tagline_lbl = tk.Label(
        content,
        text="BUILT FOR BEGINNERS",
        font=(FONT_FAMILY, 10, "bold"),
        bg=COLORS["bg_editor"],
        fg="#475569" # Softened tagline to build a clean aesthetic hierarchy
    )
    tagline_lbl.pack(pady=(5, 10))

    credit_frame = tk.Frame(content, bg=COLORS["bg_editor"])
    credit_frame.pack(pady=(0, 10))

    made_by_lbl = tk.Label(
        credit_frame,
        text="MADE BY ",
        font=(FONT_FAMILY, 9, "bold"),
        bg=COLORS["bg_editor"],
        fg="#475569" # Softened credit label
    )
    made_by_lbl.pack(side=tk.LEFT)

    name_lbl = tk.Label(
        credit_frame,
        text="SAMYAK JAIN",
        font=(FONT_FAMILY, 10, "bold"),
        bg=COLORS["bg_editor"],
        fg=COLORS["accent_cyan"]
    )
    name_lbl.pack(side=tk.LEFT)
    
    # Secure Entry and Validation container blocks stacked vertically
    form_frame = tk.Frame(content, bg=COLORS["bg_editor"])
    form_frame.pack(pady=(5, 5))

    pwd_lbl = tk.Label(
        form_frame,
        text="ENTER PASSWORD",
        font=(FONT_FAMILY, 8, "bold"),
        bg=COLORS["bg_editor"],
        fg=COLORS["text_muted"]
    )
    pwd_lbl.pack(anchor="w", padx=2, pady=(0, 2))

    entry_bg = RoundedFrame(form_frame, bg=COLORS["bg_editor"], fill_color=COLORS["bg_dark"], radius=8, width=240, height=36)
    entry_bg.pack(pady=(0, 10))
    entry_bg.pack_propagate(False)

    pwd_entry = tk.Entry(
        entry_bg,
        bg=COLORS["bg_dark"],
        fg=COLORS["text_light"],
        insertbackground=COLORS["accent_cyan"],
        font=(FONT_FAMILY, 10),
        show="*",
        bd=0,
        highlightthickness=0,
    )
    pwd_entry.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)
    pwd_entry.focus_set()

    err_lbl = tk.Label(
        content,
        text="",
        font=(FONT_FAMILY, 9),
        bg=COLORS["bg_editor"],
        fg=COLORS["accent_red"]
    )
    err_lbl.pack(pady=2)

    def dismiss_splash():
        try:
            alpha = 1.0
            def fade():
                nonlocal alpha
                alpha -= 0.08
                if alpha <= 0:
                    splash.destroy()
                    root.deiconify()
                    on_complete_callback()
                else:
                    splash.attributes("-alpha", alpha)
                    root.after(20, fade)
            fade()
        except Exception:
            splash.destroy()
            root.deiconify()
            on_complete_callback()

    def check_password(event=None):
        if pwd_entry.get() == "samyakjain":
            err_lbl.config(text="✅ Correct! Loading playground...", fg=COLORS["accent_green"])
            splash.after(300, dismiss_splash)
        else:
            err_lbl.config(text="❌ Incorrect password. Try again!", fg=COLORS["accent_red"])
            pwd_entry.delete(0, tk.END)

    pwd_entry.bind("<Return>", check_password)

    btn_enter = RoundedButton(
        form_frame, "Unlock Playground", check_password,
        COLORS["accent_cyan"], "#0d9488",
        width=240, height=36, radius=8, text_color="#000000", font_size=9
    )
    btn_enter.pack(pady=5)
    
    loading_lbl = tk.Label(
        content,
        text="Please enter password to start",
        font=(FONT_FAMILY, 9),
        bg=COLORS["bg_editor"],
        fg=COLORS["text_muted"]
    )
    loading_lbl.pack(side=tk.BOTTOM, pady=15)


if __name__ == "__main__":
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    root = tk.Tk()
    root.withdraw() # Conceal main window during splash display
    
    set_app_icon(root)
    app  = PyFirstIDE(root)
    
    show_splash_screen(root, lambda: app.toggle_dark_mode_border())
    
    root.mainloop()