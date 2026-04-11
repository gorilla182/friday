#!/usr/bin/env python3
"""
DeepSeek + GitHub: чат с function calling.
Переменные окружения:
  DEEPSEEK_API_KEY — ключ API DeepSeek
  GITHUB_TOKEN — fine-grained или classic PAT (repo, notifications при необходимости)
"""
from __future__ import annotations

import json
import os
import ssl
import urllib.error
import urllib.request
from typing import Any

try:
    import certifi
except ImportError:
    certifi = None

from github_client import GitHubClient, GitHubError

DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-chat"
MAX_TOOL_ROUNDS = 10


def _assistant_for_api(msg: dict[str, Any]) -> dict[str, Any]:
    """Убирает лишние поля ответа API, чтобы не ломать следующий запрос."""
    out: dict[str, Any] = {"role": "assistant", "content": msg.get("content")}
    if msg.get("tool_calls"):
        out["tool_calls"] = msg["tool_calls"]
    return out


GITHUB_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "github_list_my_repos",
            "description": "Список репозиториев текущего пользователя GitHub (недавно обновлённые).",
            "parameters": {
                "type": "object",
                "properties": {
                    "per_page": {"type": "integer", "description": "До 100", "default": 20},
                    "affiliation": {
                        "type": "string",
                        "description": "owner | collaborator | organization_member",
                        "default": "owner",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "github_list_issues",
            "description": "Issues в репозитории owner/repo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "owner": {"type": "string"},
                    "repo": {"type": "string"},
                    "state": {"type": "string", "description": "open, closed, all", "default": "open"},
                    "per_page": {"type": "integer", "default": 15},
                },
                "required": ["owner", "repo"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "github_list_pull_requests",
            "description": "Pull requests в репозитории owner/repo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "owner": {"type": "string"},
                    "repo": {"type": "string"},
                    "state": {"type": "string", "default": "open"},
                    "per_page": {"type": "integer", "default": 15},
                },
                "required": ["owner", "repo"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "github_list_commits",
            "description": "Последние коммиты в ветке репозитория (отслеживание изменений).",
            "parameters": {
                "type": "object",
                "properties": {
                    "owner": {"type": "string"},
                    "repo": {"type": "string"},
                    "per_page": {"type": "integer", "default": 15},
                    "sha": {"type": "string", "description": "Ветка или SHA, по умолчанию default branch"},
                },
                "required": ["owner", "repo"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "github_create_issue_comment",
            "description": "Оставить комментарий к issue или PR (номер совпадает). Только по явной просьбе пользователя.",
            "parameters": {
                "type": "object",
                "properties": {
                    "owner": {"type": "string"},
                    "repo": {"type": "string"},
                    "issue_number": {"type": "integer"},
                    "body": {"type": "string", "description": "Текст комментария на GitHub (markdown)"},
                },
                "required": ["owner", "repo", "issue_number", "body"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "github_list_notifications",
            "description": "Уведомления GitHub (активность, упоминания).",
            "parameters": {
                "type": "object",
                "properties": {
                    "per_page": {"type": "integer", "default": 20},
                    "all_notifications": {
                        "type": "boolean",
                        "description": "Показать прочитанные тоже",
                        "default": False,
                    },
                },
            },
        },
    },
]


def _post_deepseek(api_key: str, payload: dict[str, Any]) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        DEEPSEEK_URL,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    ctx = (
        ssl.create_default_context(cafile=certifi.where())
        if certifi
        else ssl.create_default_context()
    )
    try:
        with urllib.request.urlopen(req, timeout=120, context=ctx) as resp:
            return json.loads(resp.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", "replace")[:4000]
        raise RuntimeError(f"DeepSeek HTTP {e.code}: {err}") from e


def _tool_dispatch(client: GitHubClient, name: str, raw_args: str) -> str:
    try:
        args = json.loads(raw_args or "{}")
    except json.JSONDecodeError:
        args = {}
    try:
        if name == "github_list_my_repos":
            data = client.list_my_repos(
                per_page=int(args.get("per_page", 20)),
                affiliation=str(args.get("affiliation", "owner")),
            )
        elif name == "github_list_issues":
            data = client.list_issues(
                str(args["owner"]),
                str(args["repo"]),
                state=str(args.get("state", "open")),
                per_page=int(args.get("per_page", 15)),
            )
        elif name == "github_list_pull_requests":
            data = client.list_pulls(
                str(args["owner"]),
                str(args["repo"]),
                state=str(args.get("state", "open")),
                per_page=int(args.get("per_page", 15)),
            )
        elif name == "github_list_commits":
            sha = args.get("sha")
            data = client.list_commits(
                str(args["owner"]),
                str(args["repo"]),
                per_page=int(args.get("per_page", 15)),
                sha=str(sha) if sha else None,
            )
        elif name == "github_create_issue_comment":
            data = client.create_issue_comment(
                str(args["owner"]),
                str(args["repo"]),
                int(args["issue_number"]),
                str(args["body"]),
            )
        elif name == "github_list_notifications":
            data = client.list_notifications(
                per_page=int(args.get("per_page", 20)),
                all_notifications=bool(args.get("all_notifications", False)),
            )
        else:
            return json.dumps({"error": f"unknown_tool: {name}"}, ensure_ascii=False)
        return json.dumps(data, ensure_ascii=False)[:120_000]
    except (KeyError, ValueError, TypeError, GitHubError) as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


def build_system_prompt(github_login: str) -> str:
    return (
        "Ты голосовой ассистент J.A.R.V.I.S. Пользователь говорит по-русски — отвечай по-русски, кратко и по делу.\n"
        f"Аккаунт GitHub пользователя: {github_login}.\n"
        "У тебя есть инструменты GitHub: список репозиториев, issues, pull requests, коммиты, уведомления, "
        "и создание комментария к issue/PR. Создавай комментарии только если пользователь явно просит.\n"
        "Для owner/repo используй полные имена вида owner/repo из контекста или из списка репозиториев.\n"
        "Не выдумывай данные — если нужно, вызови инструмент."
    )


def chat_turn(
    user_text: str,
    history: list[dict[str, Any]],
    deepseek_key: str,
    github_token: str,
) -> tuple[str, list[dict[str, Any]]]:
    """Возвращает (ответ_ассистента, обновлённая_история для UI)."""
    gh = GitHubClient(github_token)
    login = gh.get_user_login()
    system = build_system_prompt(login)

    messages: list[dict[str, Any]] = [{"role": "system", "content": system}]
    for h in history[-24:]:
        messages.append(h)
    messages.append({"role": "user", "content": user_text})

    for _ in range(MAX_TOOL_ROUNDS):
        resp = _post_deepseek(
            deepseek_key,
            {
                "model": MODEL,
                "messages": messages,
                "tools": GITHUB_TOOLS,
                "tool_choice": "auto",
            },
        )
        choices = resp.get("choices")
        if not choices:
            raise RuntimeError(f"DeepSeek: нет choices: {resp}")
        msg = choices[0].get("message") or {}
        tool_calls = msg.get("tool_calls")

        if tool_calls:
            messages.append(_assistant_for_api(msg))
            for tc in tool_calls:
                fn = (tc.get("function") or {})
                name = fn.get("name", "")
                arguments = fn.get("arguments") or "{}"
                tid = tc.get("id", "")
                result = _tool_dispatch(gh, name, arguments)
                messages.append({"role": "tool", "tool_call_id": tid, "content": result})
            continue

        content = msg.get("content")
        if isinstance(content, str) and content.strip():
            assistant_reply = content.strip()
            new_hist = history + [
                {"role": "user", "content": user_text},
                {"role": "assistant", "content": assistant_reply},
            ]
            return assistant_reply, new_hist
        raise RuntimeError("DeepSeek: пустой ответ без tool_calls")

    raise RuntimeError("Слишком много раундов tool calls")


def load_keys() -> tuple[str | None, str | None]:
    return os.environ.get("DEEPSEEK_API_KEY"), os.environ.get("GITHUB_TOKEN")
