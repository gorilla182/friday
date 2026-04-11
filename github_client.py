#!/usr/bin/env python3
"""Минимальный клиент GitHub REST API (только urllib). Токен: GITHUB_TOKEN."""
from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

try:
    import certifi
except ImportError:
    certifi = None


class GitHubError(Exception):
    pass


class GitHubClient:
    def __init__(self, token: str) -> None:
        if not token.strip():
            raise GitHubError("GITHUB_TOKEN пустой")
        self._token = token.strip()

    def _request(
        self,
        method: str,
        path: str,
        query: dict[str, str] | None = None,
        body: dict[str, Any] | None = None,
    ) -> Any:
        q = urllib.parse.urlencode(query) if query else ""
        url = f"https://api.github.com{path}" + (f"?{q}" if q else "")
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(
            url,
            data=data,
            method=method,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self._token}",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "Friday-Jarvis-Assistant",
                **({"Content-Type": "application/json"} if body is not None else {}),
            },
        )
        ctx = (
            ssl.create_default_context(cafile=certifi.where())
            if certifi
            else ssl.create_default_context()
        )
        try:
            with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
                raw = resp.read().decode("utf-8", "replace")
                if not raw:
                    return None
                return json.loads(raw)
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", "replace")[:2000]
            raise GitHubError(f"HTTP {e.code}: {err_body}") from e

    def get_user_login(self) -> str:
        u = self._request("GET", "/user")
        if not isinstance(u, dict):
            raise GitHubError("Некорректный ответ /user")
        return str(u.get("login", ""))

    def list_my_repos(self, per_page: int = 20, affiliation: str = "owner") -> list[dict[str, Any]]:
        # affiliation: owner, collaborator, organization_member
        r = self._request(
            "GET",
            "/user/repos",
            query={
                "per_page": str(min(max(per_page, 1), 100)),
                "affiliation": affiliation,
                "sort": "updated",
            },
        )
        if not isinstance(r, list):
            return []
        out = []
        for x in r:
            if not isinstance(x, dict):
                continue
            out.append(
                {
                    "full_name": x.get("full_name"),
                    "name": x.get("name"),
                    "private": x.get("private"),
                    "updated_at": x.get("updated_at"),
                    "default_branch": x.get("default_branch"),
                    "html_url": x.get("html_url"),
                }
            )
        return out

    def list_issues(
        self, owner: str, repo: str, state: str = "open", per_page: int = 15
    ) -> list[dict[str, Any]]:
        r = self._request(
            "GET",
            f"/repos/{owner}/{repo}/issues",
            query={
                "state": state,
                "per_page": str(min(max(per_page, 1), 100)),
            },
        )
        if not isinstance(r, list):
            return []
        out = []
        for x in r:
            if not isinstance(x, dict):
                continue
            out.append(
                {
                    "number": x.get("number"),
                    "title": x.get("title"),
                    "state": x.get("state"),
                    "user": (x.get("user") or {}).get("login") if isinstance(x.get("user"), dict) else None,
                    "html_url": x.get("html_url"),
                    "pull_request": bool(x.get("pull_request")),
                }
            )
        return out

    def list_pulls(
        self, owner: str, repo: str, state: str = "open", per_page: int = 15
    ) -> list[dict[str, Any]]:
        r = self._request(
            "GET",
            f"/repos/{owner}/{repo}/pulls",
            query={
                "state": state,
                "per_page": str(min(max(per_page, 1), 100)),
            },
        )
        if not isinstance(r, list):
            return []
        out = []
        for x in r:
            if not isinstance(x, dict):
                continue
            out.append(
                {
                    "number": x.get("number"),
                    "title": x.get("title"),
                    "state": x.get("state"),
                    "user": (x.get("user") or {}).get("login") if isinstance(x.get("user"), dict) else None,
                    "html_url": x.get("html_url"),
                    "head": (x.get("head") or {}).get("ref") if isinstance(x.get("head"), dict) else None,
                }
            )
        return out

    def list_commits(
        self, owner: str, repo: str, per_page: int = 15, sha: str | None = None
    ) -> list[dict[str, Any]]:
        q: dict[str, str] = {"per_page": str(min(max(per_page, 1), 100))}
        if sha:
            q["sha"] = sha
        r = self._request("GET", f"/repos/{owner}/{repo}/commits", query=q)
        if not isinstance(r, list):
            return []
        out = []
        for x in r:
            if not isinstance(x, dict):
                continue
            c = x.get("commit") if isinstance(x.get("commit"), dict) else {}
            msg = c.get("message") if isinstance(c, dict) else ""
            if isinstance(msg, str) and len(msg) > 200:
                msg = msg[:200] + "…"
            out.append(
                {
                    "sha": (x.get("sha") or "")[:7],
                    "message": msg,
                    "author": ((c.get("author") or {}).get("name") if isinstance(c.get("author"), dict) else None),
                    "date": ((c.get("author") or {}).get("date") if isinstance(c.get("author"), dict) else None),
                    "html_url": x.get("html_url"),
                }
            )
        return out

    def create_issue_comment(self, owner: str, repo: str, issue_number: int, body: str) -> dict[str, Any]:
        r = self._request(
            "POST",
            f"/repos/{owner}/{repo}/issues/{issue_number}/comments",
            body={"body": body},
        )
        return r if isinstance(r, dict) else {"raw": str(r)}

    def list_notifications(self, per_page: int = 20, all_notifications: bool = False) -> list[dict[str, Any]]:
        r = self._request(
            "GET",
            "/notifications",
            query={
                "per_page": str(min(max(per_page, 1), 100)),
                "all": "true" if all_notifications else "false",
            },
        )
        if not isinstance(r, list):
            return []
        out = []
        for x in r:
            if not isinstance(x, dict):
                continue
            repo = x.get("repository") if isinstance(x.get("repository"), dict) else {}
            out.append(
                {
                    "id": x.get("id"),
                    "reason": x.get("reason"),
                    "unread": x.get("unread"),
                    "updated_at": x.get("updated_at"),
                    "subject_title": (x.get("subject") or {}).get("title")
                    if isinstance(x.get("subject"), dict)
                    else None,
                    "subject_type": (x.get("subject") or {}).get("type")
                    if isinstance(x.get("subject"), dict)
                    else None,
                    "repository": repo.get("full_name"),
                }
            )
        return out
