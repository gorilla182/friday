#!/usr/bin/env python3
"""Teststand — training web app for UI and API test automation."""

import argparse

from flask import Flask

from api import api_bp
from config import SECRET_KEY
from database import init_db, reset_db, seed_data
from ui import ui_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = SECRET_KEY

    app.register_blueprint(ui_bp)
    app.register_blueprint(api_bp)

    return app


def main() -> None:
    parser = argparse.ArgumentParser(description="Teststand training web app")
    parser.add_argument(
        "--reset-db",
        action="store_true",
        help="Reset SQLite database to initial seed state and exit",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=5000, help="Port to bind (default: 5000)")
    args = parser.parse_args()

    if args.reset_db:
        reset_db()
        print("Database reset complete.")
        return

    init_db()
    seed_data()

    app = create_app()
    print(f"Teststand running at http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=True)


if __name__ == "__main__":
    main()
