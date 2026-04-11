#!/usr/bin/env python3
"""
Графический интерфейс в стиле J.A.R.V.I.S. (HUD).
Запуск: python3 jarvis_gui.py
"""
from __future__ import annotations

import math
import sys
import tkinter as tk
from tkinter import font as tkfont


BG = "#050810"
ACCENT = "#00e8ff"
ACCENT_DIM = "#006a78"
TEXT_MUTED = "#6b8a94"
RING_COUNT = 3


class JarvisHUD(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("J.A.R.V.I.S.")
        self.configure(bg=BG)
        self.minsize(720, 480)
        self.geometry("900x600")
        self._phase = 0.0
        self._pulse = 0.0

        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<q>", lambda e: self.destroy())
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        title_font = tkfont.Font(family="Helvetica", size=28, weight="bold")
        sub_font = tkfont.Font(family="Helvetica", size=13)
        mono_font = tkfont.Font(family="Menlo", size=11)

        header = tk.Frame(self, bg=BG)
        header.pack(fill=tk.X, pady=(24, 8))
        tk.Label(
            header,
            text="J.A.R.V.I.S.",
            font=title_font,
            fg=ACCENT,
            bg=BG,
        ).pack()
        tk.Label(
            header,
            text="Just A Rather Very Intelligent System",
            font=sub_font,
            fg=TEXT_MUTED,
            bg=BG,
        ).pack()

        self.canvas = tk.Canvas(
            self,
            bg=BG,
            highlightthickness=0,
            borderwidth=0,
        )
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=24, pady=12)

        self.status_var = tk.StringVar(value="Система онлайн · ожидание команд")
        footer = tk.Frame(self, bg=BG)
        footer.pack(fill=tk.X, side=tk.BOTTOM, pady=(0, 16))
        tk.Label(
            footer,
            textvariable=self.status_var,
            font=mono_font,
            fg=ACCENT,
            bg=BG,
        ).pack()
        tk.Label(
            footer,
            text="Esc или Q — закрыть",
            font=mono_font,
            fg=TEXT_MUTED,
            bg=BG,
        ).pack()

        self._tick()

    def _tick(self) -> None:
        self._phase += 0.04
        self._pulse += 0.08
        self._draw_hud()
        self.after(40, self._tick)

    def _draw_hud(self) -> None:
        c = self.canvas
        c.delete("all")
        w = max(c.winfo_width(), 400)
        h = max(c.winfo_height(), 300)
        cx, cy = w / 2, h / 2
        base = min(w, h) * 0.38

        pulse = 0.5 + 0.5 * math.sin(self._pulse)
        for i in range(RING_COUNT):
            r = base * (0.45 + i * 0.22) + pulse * 6
            start = math.degrees(self._phase + i * 0.7) % 360
            extent = 110 + 40 * math.sin(self._phase * 2 + i)
            c.create_arc(
                cx - r,
                cy - r,
                cx + r,
                cy + r,
                start=start,
                extent=extent,
                style=tk.ARC,
                outline=ACCENT if i == 0 else ACCENT_DIM,
                width=2 if i == 0 else 1,
            )

        for angle in range(0, 360, 45):
            rad = math.radians(angle + self._phase * 40)
            x1 = cx + base * 0.15 * math.cos(rad)
            y1 = cy + base * 0.15 * math.sin(rad)
            x2 = cx + base * 0.55 * math.cos(rad)
            y2 = cy + base * 0.55 * math.sin(rad)
            c.create_line(x1, y1, x2, y2, fill=ACCENT_DIM, width=1)

        tick = int(self._phase * 10) % 4
        dots = ["·", "··", "···", "··"][tick]
        self.status_var.set(f"Сканирование окружения {dots}  ·  все подсистемы в норме")


def run() -> None:
    app = JarvisHUD()
    app.mainloop()


def main() -> int:
    try:
        run()
    except tk.TclError as e:
        print(f"GUI error (tkinter): {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
