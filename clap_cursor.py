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
import speech_recognition as sr

try:
    import certifi
except ImportError:
    certifi = None


YOUTUBE_URL = "https://youtu.be/XgWUDbYfNe4?si=frflVg3XgSYnke13"
POSTMAN_APP_PATH = "/Applications/Postman.app"
TRIGGER_PHRASE = "просыпайся папочка вернулся"
WEATHER_LOCATION = "Иваново, Россия"


def open_apps_and_video(url: str) -> None:
    subprocess.run(["open", "-a", "Cursor"], check=False)
    postman_launch = subprocess.run(["open", "-a", "Postman"], check=False)
    if postman_launch.returncode != 0:
        # Fallback to explicit .app path if app name resolution fails.
        postman_launch = subprocess.run(["open", POSTMAN_APP_PATH], check=False)
        if postman_launch.returncode != 0:
            print(
                "Warning: failed to open Postman. "
                "Check app name/path and macOS permissions.",
                file=sys.stderr,
            )
    webbrowser.open(url, new=2)


def speak(text: str, voice: str | None = None) -> None:
    if not text.strip():
        return
    cmd = ["say"]
    if voice:
        cmd += ["-v", voice]
    cmd.append(text)
    subprocess.run(cmd, check=False)


def fetch_weather_summary(location: str) -> str:
    """
    Uses wttr.in for a quick human-readable summary.
    Example response for format=3:
      "Ivanovo: +7°C, Partly cloudy"
    """
    loc = urllib.parse.quote(location)
    url = f"https://wttr.in/{loc}?format=3&lang=ru"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (macOS) qa-clap-script"},
    )
    ssl_ctx = _build_ssl_context()
    with urllib.request.urlopen(req, timeout=8, context=ssl_ctx) as resp:
        return resp.read().decode("utf-8", errors="replace").strip()


def _build_ssl_context() -> ssl.SSLContext:
    if certifi is not None:
        return ssl.create_default_context(cafile=certifi.where())
    return ssl.create_default_context()


def normalize_text(text: str) -> str:
    return " ".join(text.lower().replace("ё", "е").strip().split())


def listen_for_phrase(
    trigger_phrase: str,
    sample_rate: int,
    listen_window_sec: float,
    cooldown_sec: float,
    weather_location: str,
    say_voice: str | None,
    speak_weather: bool,
    duration_sec: float | None = None,
) -> None:
    recognizer = sr.Recognizer()
    normalized_trigger = normalize_text(trigger_phrase)
    print("Listening for trigger phrase... Press Ctrl+C to stop.")
    print(f'Trigger phrase: "{trigger_phrase}"')
    last_action_at = 0.0
    started_at = time.time()

    try:
        while True:
            if duration_sec is not None and (time.time() - started_at) > duration_sec:
                print("Timeout reached, stopping.")
                return

            frames = int(sample_rate * listen_window_sec)
            audio_np = sd.rec(frames, samplerate=sample_rate, channels=1, dtype="int16")
            sd.wait()

            audio_data = sr.AudioData(
                frame_data=audio_np.tobytes(),
                sample_rate=sample_rate,
                sample_width=2,
            )

            try:
                heard_text = recognizer.recognize_google(audio_data, language="ru-RU")
                normalized_heard = normalize_text(heard_text)
                print(f"Heard: {heard_text}")

                now = time.time()
                if normalized_trigger in normalized_heard:
                    if (now - last_action_at) < cooldown_sec:
                        print("Phrase detected but still in cooldown.")
                        continue
                    print("Trigger phrase detected. Opening Cursor, Postman and video...")
                    open_apps_and_video(YOUTUBE_URL)
                    if speak_weather:
                        try:
                            summary = fetch_weather_summary(weather_location)
                            speak(f"Погода на сегодня: {summary}", voice=say_voice)
                        except ssl.SSLError as exc:
                            print(
                                "Warning: weather SSL error. "
                                "Install certifi (`pip install certifi`) or run "
                                "`Install Certificates.command` for your Python. "
                                f"Details: {exc}",
                                file=sys.stderr,
                            )
                        except Exception as exc:
                            print(f"Warning: failed to fetch/speak weather: {exc}", file=sys.stderr)
                    last_action_at = now
            except sr.UnknownValueError:
                # Nothing recognizable in this audio window.
                continue
            except sr.RequestError as exc:
                print(f"Speech recognition request failed: {exc}", file=sys.stderr)
                time.sleep(1.0)
    except KeyboardInterrupt:
        print("\nStopped by user.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Open Cursor/Postman/YouTube when trigger phrase is detected."
    )
    parser.add_argument(
        "--phrase",
        type=str,
        default=TRIGGER_PHRASE,
        help="Phrase that triggers action.",
    )
    parser.add_argument(
        "--sample-rate",
        type=int,
        default=16000,
        help="Microphone sample rate.",
    )
    parser.add_argument(
        "--listen-window",
        type=float,
        default=3.0,
        help="Seconds of audio per recognition cycle.",
    )
    parser.add_argument(
        "--cooldown",
        type=float,
        default=5.0,
        help="Minimum seconds between actions after trigger.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        help="Optional: stop listening after N seconds.",
    )
    parser.add_argument(
        "--weather-location",
        type=str,
        default=WEATHER_LOCATION,
        help='Weather location, e.g. "Иваново, Россия".',
    )
    parser.add_argument(
        "--no-weather",
        action="store_true",
        help="Disable speaking the weather on trigger.",
    )
    parser.add_argument(
        "--say-voice",
        type=str,
        default=None,
        help='Optional macOS voice for "say", e.g. "Milena".',
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.sample_rate <= 0:
        print("Error: --sample-rate must be > 0", file=sys.stderr)
        return 1
    if args.listen_window <= 0:
        print("Error: --listen-window must be > 0", file=sys.stderr)
        return 1
    if args.cooldown < 0:
        print("Error: --cooldown must be >= 0", file=sys.stderr)
        return 1

    listen_for_phrase(
        trigger_phrase=args.phrase,
        sample_rate=args.sample_rate,
        listen_window_sec=args.listen_window,
        cooldown_sec=args.cooldown,
        weather_location=args.weather_location,
        say_voice=args.say_voice,
        speak_weather=(not args.no_weather),
        duration_sec=args.timeout,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
