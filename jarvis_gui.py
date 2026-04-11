#!/usr/bin/env python3
"""
J.A.R.V.I.S. HUD + чат (DeepSeek + GitHub).
Запуск: python3 jarvis_gui.py

Переменные окружения:
  DEEPSEEK_API_KEY
  GITHUB_TOKEN
"""
from __future__ import annotations

import math
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import font as tkfont
from tkinter import scrolledtext

try:
    import speech_recognition as sr
except ImportError:
    sr = None

from assistant_backend import chat_turn, load_keys

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
        self.minsize(960, 560)
        self.geometry("1024x640")
        self._phase = 0.0
        self._pulse = 0.0
        self._history: list[dict] = []
        self._busy = False

        ds, gh = load_keys()
        self._deepseek_key = ds
        self._github_token = gh

        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<q>", lambda e: self.destroy())
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        title_font = tkfont.Font(family="Helvetica", size=22, weight="bold")
        sub_font = tkfont.Font(family="Helvetica", size=11)
        mono_font = tkfont.Font(family="Menlo", size=10)

        header = tk.Frame(self, bg=BG)
        header.pack(fill=tk.X, pady=(12, 4))
        tk.Label(header, text="J.A.R.V.I.S.", font=title_font, fg=ACCENT, bg=BG).pack()
        tk.Label(
            header,
            text="Just A Rather Very Intelligent System · DeepSeek + GitHub",
            font=sub_font,
            fg=TEXT_MUTED,
            bg=BG,
        ).pack()

        paned = tk.PanedWindow(
            self,
            orient=tk.HORIZONTAL,
            sashrelief=tk.FLAT,
            bg=BG,
            sashwidth=6,
        )
        paned.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

        left = tk.Frame(paned, bg=BG, width=360)
        self.canvas = tk.Canvas(left, bg=BG, highlightthickness=0, borderwidth=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        paned.add(left)

        right = tk.Frame(paned, bg=BG)
        key_line = "Ключи: "
        if self._deepseek_key and self._github_token:
            key_line += "DeepSeek ✓ · GitHub ✓"
        else:
            key_line += (
                "задайте DEEPSEEK_API_KEY и GITHUB_TOKEN в окружении "
                "(export в терминале перед запуском)."
            )
        tk.Label(right, text=key_line, font=mono_font, fg=TEXT_MUTED, bg=BG, wraplength=520, justify=tk.LEFT).pack(
            anchor=tk.W, pady=(0, 6)
        )

        self.chat = scrolledtext.ScrolledText(
            right,
            height=18,
            font=mono_font,
            bg="#0a1018",
            fg=ACCENT,
            insertbackground=ACCENT,
            relief=tk.FLAT,
            wrap=tk.WORD,
        )
        self.chat.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
        self.chat.insert(tk.END, "Спроси про репозитории, PR, коммиты или попроси оставить комментарий к issue.\n\n")
        self.chat.configure(state=tk.DISABLED)

        row = tk.Frame(right, bg=BG)
        row.pack(fill=tk.X)
        self.entry = tk.Entry(
            row,
            font=mono_font,
            bg="#0a1018",
            fg=ACCENT,
            insertbackground=ACCENT,
            relief=tk.FLAT,
        )
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        self.entry.bind("<Return>", lambda e: self._on_send())

        tk.Button(row, text="Отправить", command=self._on_send, bg=ACCENT_DIM, fg=ACCENT, font=mono_font).pack(
            side=tk.LEFT, padx=2
        )
        if sr:
            tk.Button(row, text="🎤", command=self._on_mic, bg=ACCENT_DIM, fg=ACCENT, font=mono_font).pack(
                side=tk.LEFT, padx=2
            )

        self.speak_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            right,
            text="Озвучивать ответ (say)",
            variable=self.speak_var,
            font=mono_font,
            fg=TEXT_MUTED,
            bg=BG,
            selectcolor="#0a1018",
            activebackground=BG,
            activeforeground=ACCENT,
        ).pack(anchor=tk.W, pady=(8, 0))

        self.status_var = tk.StringVar(value="Готов")
        tk.Label(right, textvariable=self.status_var, font=mono_font, fg=ACCENT, bg=BG).pack(anchor=tk.W, pady=(6, 0))
        tk.Label(right, text="Esc / Q — закрыть", font=mono_font, fg=TEXT_MUTED, bg=BG).pack(anchor=tk.W)

        paned.add(right)
        paned.paneconfig(left, minsize=320)
        paned.paneconfig(right, minsize=480)

        self._tick()

    def _append_chat(self, who: str, text: str) -> None:
        self.chat.configure(state=tk.NORMAL)
        self.chat.insert(tk.END, f"{who}: {text}\n\n")
        self.chat.see(tk.END)
        self.chat.configure(state=tk.DISABLED)

    def _on_send(self) -> None:
        if self._busy:
            return
        text = self.entry.get().strip()
        if not text:
            return
        if not (self._deepseek_key and self._github_token):
            self._append_chat("Система", "Нет ключей DEEPSEEK_API_KEY или GITHUB_TOKEN.")
            return
        self.entry.delete(0, tk.END)
        self._append_chat("Вы", text)
        self._busy = True
        self.status_var.set("Запрос к DeepSeek / GitHub…")
        hist = list(self._history)

        def work() -> None:
            try:
                reply, new_hist = chat_turn(text, hist, self._deepseek_key, self._github_token)
            except Exception as exc:
                reply = f"Ошибка: {exc}"
                new_hist = hist + [
                    {"role": "user", "content": text},
                    {"role": "assistant", "content": reply},
                ]

            def done() -> None:
                self._busy = False
                self._history = new_hist
                self._append_chat("J.A.R.V.I.S.", reply)
                self.status_var.set("Готов")
                if self.speak_var.get() and reply and not reply.startswith("Ошибка:"):
                    snippet = reply[:800]
                    for voice in ("Yuri", "Milena", None):
                        cmd = ["say"] + (["-v", voice] if voice else []) + [snippet]
                        if subprocess.run(cmd, check=False).returncode == 0:
                            break

            self.after(0, done)

        threading.Thread(target=work, daemon=True).start()

    def _on_mic(self) -> None:
        if not sr or self._busy:
            return

        def listen() -> None:
            self.after(0, lambda: self.status_var.set("Слушаю микрофон…"))
            text: str | None = None
            err = ""
            try:
                r = sr.Recognizer()
                with sr.Microphone() as source:
                    r.adjust_for_ambient_noise(source, duration=0.4)
                    audio = r.listen(source, timeout=6, phrase_time_limit=20)
                text = sr.recognize_google(audio, language="ru-RU")
            except Exception as exc:
                err = str(exc)

            def finish() -> None:
                if text:
                    self.entry.delete(0, tk.END)
                    self.entry.insert(0, text)
                    self.status_var.set("Готов")
                else:
                    self.status_var.set(f"Голос: {err or 'не распознано'}")

            self.after(0, finish)

        threading.Thread(target=listen, daemon=True).start()

    def _tick(self) -> None:
        self._phase += 0.04
        self._pulse += 0.08
        self._draw_hud()
        self.after(40, self._tick)

    def _draw_hud(self) -> None:
        c = self.canvas
        c.delete("all")
        w = max(c.winfo_width(), 280)
        h = max(c.winfo_height(), 260)
        cx, cy = w / 2, h / 2
        base = min(w, h) * 0.36
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
