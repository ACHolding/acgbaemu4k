# gbaemu0.1.py
# Python 3.14 / Tkinter / one file / embedded Cython core / files = off-ish
# Run: python3 gbaemu0.1.py
# Optional speed core: pip install cython setuptools

import os, sys, time, math, tempfile, importlib.util, subprocess
import tkinter as tk
from tkinter import filedialog, messagebox

APP_TITLE = "gbaemu0.1"
W, H = 600, 400
FPS = 60
FRAME_MS = int(1000 / FPS)

CYTHON_CORE = r'''
# cython: language_level=3
cdef class FastGBACore:
    cdef public int frame
    cdef public int running
    cdef public int pc
    cdef public int cycles

    def __cinit__(self):
        self.frame = 0
        self.running = 0
        self.pc = 0x08000000
        self.cycles = 0

    cpdef reset(self):
        self.frame = 0
        self.running = 1
        self.pc = 0x08000000
        self.cycles = 0

    cpdef step_frame(self):
        cdef int i
        for i in range(280896):   # rough GBA cycles/frame
            self.cycles += 1
        self.frame += 1
        return self.frame
'''

class PythonGBACore:
    def __init__(self):
        self.frame = 0
        self.running = False
        self.pc = 0x08000000
        self.cycles = 0

    def reset(self):
        self.frame = 0
        self.running = True
        self.pc = 0x08000000
        self.cycles = 0

    def step_frame(self):
        self.cycles += 280896
        self.frame += 1
        return self.frame

def load_embedded_cython():
    try:
        import pyximport
        build_dir = os.path.join(tempfile.gettempdir(), "gbaemu01_cython")
        os.makedirs(build_dir, exist_ok=True)

        pyx_path = os.path.join(build_dir, "mewgba_core.pyx")
        with open(pyx_path, "w", encoding="utf-8") as f:
            f.write(CYTHON_CORE)

        pyximport.install(build_dir=build_dir, language_level=3)
        sys.path.insert(0, build_dir)

        import mewgba_core
        return mewgba_core.FastGBACore(), "Cython embedded core loaded"
    except Exception as e:
        return PythonGBACore(), f"Python fallback core loaded: {e}"

class GBAEmuApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ac's gba emu 0.1")
        self.root.geometry(f"{W}x{H}")
        self.root.configure(bg="#001020")

        self.core, self.core_status = load_embedded_cython()
        self.rom = b""
        self.rom_name = "NO ROM"

        self.make_ui()
        self.loop()

    def make_ui(self):
        bar = tk.Frame(self.root, bg="#000000")
        bar.pack(fill="x")

        for text, cmd in [
            ("Load ROM", self.load_rom),
            ("Reset", self.reset),
            ("Pause", self.pause),
            ("Run", self.run),
            ("About", self.about),
        ]:
            tk.Button(
                bar,
                text=text,
                command=cmd,
                bg="black",
                fg="#2c7dff",
                activebackground="#001a33",
                activeforeground="#66aaff",
                relief="flat",
            ).pack(side="left", padx=3, pady=3)

        self.canvas = tk.Canvas(
            self.root,
            width=560,
            height=260,
            bg="#001a33",
            highlightbackground="#2c7dff",
        )
        self.canvas.pack(pady=10)

        self.status = tk.Label(
            self.root,
            text=self.core_status,
            bg="#001020",
            fg="#66aaff",
            anchor="w",
        )
        self.status.pack(fill="x", padx=10)

    def load_rom(self):
        path = filedialog.askopenfilename(
            title="Load GBA ROM",
            filetypes=[("GBA ROM", "*.gba"), ("All files", "*.*")]
        )
        if not path:
            return
        with open(path, "rb") as f:
            self.rom = f.read()
        self.rom_name = os.path.basename(path)
        self.core.reset()
        self.status.config(text=f"Loaded {self.rom_name} | {len(self.rom)} bytes | 60 FPS")

    def reset(self):
        self.core.reset()
        self.status.config(text="Reset | PC=08000000 | ARM7TDMI stub active")

    def pause(self):
        self.core.running = False
        self.status.config(text="Paused")

    def run(self):
        self.core.running = True
        self.status.config(text="Running | speed = gba | 60 FPS")

    def about(self):
        messagebox.showinfo(
            "gbaemu0.1",
            "AC GBA EMU 0.1\nTkinter 600x400\nBlue hue\nEmbedded Cython core\nPPU stub included"
        )

    def draw_ppu(self):
        self.canvas.delete("all")

        f = self.core.frame
        self.canvas.create_rectangle(20, 20, 540, 240, outline="#2c7dff", width=2)
        self.canvas.create_text(
            280, 45,
            text="GAME BOY ADVANCE",
            fill="#66aaff",
            font=("Courier", 20, "bold")
        )

        x = 80 + int(math.sin(f * 0.08) * 50)
        self.canvas.create_rectangle(x, 95, x + 400, 175, outline="#2c7dff", fill="#000814")
        self.canvas.create_text(
            280, 120,
            text=self.rom_name,
            fill="#66aaff",
            font=("Courier", 12, "bold")
        )
        self.canvas.create_text(
            280, 150,
            text=f"PPU MODE 3 STUB | FRAME {f}",
            fill="#2c7dff",
            font=("Courier", 11)
        )

        self.canvas.create_text(
            280, 215,
            text=f"PC={self.core.pc:08X}  CYCLES={self.core.cycles}",
            fill="#66aaff",
            font=("Courier", 10)
        )

    def loop(self):
        if self.core.running:
            self.core.step_frame()
        self.draw_ppu()
        self.root.after(FRAME_MS, self.loop)

if __name__ == "__main__":
    root = tk.Tk()
    app = GBAEmuApp(root)
    root.mainloop()