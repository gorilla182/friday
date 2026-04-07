#!/usr/bin/env python3
import argparse
import ssl
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import webbrowser

import sounddevice as sd

try:
    import certifi
except ImportError:
    certifi = None

YOUTUBE_URL = "https://youtu.be/XgWUDbYfNe4?si=o0o-7qYQdI8f1mOt&t=5"
WEATHER_LOCATION = "Иваново, Россия"


def run_cmd(*cmd: str) -> int:
    return subprocess.run(list(cmd), check=False).returncode


def say(text: str, voice: str | None) -> None:
    run_cmd("say", *(["-v", voice] if voice else []), text)


def list_voices() -> set[str]:
    out = subprocess.run(
        ["say", "-v", "?"], capture_output=True, text=True, check=False
    ).stdout
    return {line.split()[0] for line in out.splitlines() if line.strip()}


def resolve_voice(value: str | None) -> str | None:
    if not value:
        return None
    if value.strip().lower() != "jarvis":
        return value
    installed = list_voices()
    return next((v for v in ("Yuri", "Milena", "Daniel") if v in installed), "Daniel")


def fetch_weather(location: str) -> str:
    ctx = ssl.create_default_context(cafile=certifi.where()) if certifi else ssl.create_default_context()
    query = urllib.parse.quote(location)
    req = urllib.request.Request(
        f"https://wttr.in/{query}?format=3&lang=ru",
        headers={"User-Agent": "Mozilla/5.0"},
    )
    with urllib.request.urlopen(req, timeout=8, context=ctx) as resp:
        return resp.read().decode("utf-8", "replace").strip()


def launch_apps() -> None:
    run_cmd("open", "-a", "Cursor")
    if run_cmd("open", "-a", "Postman") != 0:
        run_cmd("open", "/Applications/Postman.app")
    webbrowser.open(YOUTUBE_URL, new=2)


def speak_weather(location: str, voice: str | None) -> None:
    try:
        say(f"Погода на сегодня: {fetch_weather(location)}", resolve_voice(voice))
    except Exception as exc:
        print(f"Warning: weather/speech failed: {exc}", file=sys.stderr)


def run_detector(args: argparse.Namespace) -> None:
    frames = int(args.sample_rate * args.listen_window)
    first_clap_at: float | None = None
    last_clap_at = last_action_at = last_debug_at = 0.0
    started_at = time.time()

    with sd.InputStream(
        samplerate=args.sample_rate,
        blocksize=frames,
        channels=1,
        dtype="float32",
        device=args.input_device,
    ) as stream:
        print("Listening for double clap... Ctrl+C to stop.")
        while True:
            now = time.time()
            if args.timeout and (now - started_at) > args.timeout:
                return

            block, overflowed = stream.read(frames)
            if overflowed:
                continue

            rms = float((block.reshape(-1) ** 2).mean()) ** 0.5
            if args.debug_clap and (now - last_debug_at) >= 0.5:
                print(f"rms={rms:.4f} thr={args.clap_threshold:.4f}")
                last_debug_at = now

            if first_clap_at and (now - first_clap_at) > args.double_clap_window:
                first_clap_at = None
            if rms < args.clap_threshold or (now - last_clap_at) < 0.12:
                continue

            last_clap_at = now
            if first_clap_at is None:
                first_clap_at = now
                print("First clap detected.")
                continue

            if (now - first_clap_at) <= args.double_clap_window:
                if (now - last_action_at) < args.cooldown:
                    print("Double clap in cooldown.")
                    first_clap_at = None
                    continue
                print("Double clap detected. Opening Cursor, Postman and video...")
                launch_apps()
                if not args.no_weather:
                    speak_weather(args.weather_location, args.say_voice)
                last_action_at = now
                first_clap_at = None


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Launch apps by double clap.")
    p.add_argument("--sample-rate", type=int, default=16000)
    p.add_argument("--listen-window", type=float, default=0.12)
    p.add_argument("--cooldown", type=float, default=5.0)
    p.add_argument("--clap-threshold", type=float, default=0.06)
    p.add_argument("--double-clap-window", type=float, default=0.9)
    p.add_argument("--input-device", type=int, default=None)
    p.add_argument("--list-input-devices", action="store_true")
    p.add_argument("--debug-clap", action="store_true")
    p.add_argument("--timeout", type=float, default=None)
    p.add_argument("--weather-location", type=str, default=WEATHER_LOCATION)
    p.add_argument("--no-weather", action="store_true")
    p.add_argument("--say-voice", type=str, default="jarvis")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    if args.list_input_devices:
        print("Input devices:")
        for i, dev in enumerate(sd.query_devices()):
            if dev["max_input_channels"] > 0:
                print(f"[{i}] {dev['name']} (inputs={dev['max_input_channels']})")
        return 0

    if not (
        args.sample_rate > 0
        and args.listen_window > 0
        and args.cooldown >= 0
        and 0 < args.clap_threshold <= 1
        and args.double_clap_window > 0
    ):
        print("Invalid arguments.", file=sys.stderr)
        return 1

    try:
        run_detector(args)
    except sd.PortAudioError as exc:
        print(f"Microphone error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nStopped by user.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
