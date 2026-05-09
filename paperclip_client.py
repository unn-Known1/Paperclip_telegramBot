"""Async HTTP client for the local Paperclip API."""

from __future__ import annotations

import logging
from typing import Any

import httpx

import config

logger = logging.getLogger(__name__)


class PaperclipClient:
    """Thin async wrapper around the Paperclip REST API."""

    def __init__(self, base_url: str | None = None, timeout: float | None = None):
        self.base_url = (base_url or config.PAPERCLIP_API_URL).rstrip("/")
        _timeout = timeout or config.API_TIMEOUT

        # Retry transport with exponential backoff
        transport = httpx.AsyncHTTPTransport(retries=config.API_RETRIES)

        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=_timeout,
            headers={"Accept": "application/json"},
            transport=transport,
        )
        self._company_id: str = config.PAPERCLIP_COMPANY_ID

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    async def close(self) -> None:
        await self._client.aclose()

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------
    async def health(self) -> dict[str, Any]:
        """GET /api/health"""
        r = await self._client.get("/api/health")
        r.raise_for_status()
        return r.json()

    # ------------------------------------------------------------------
    # Company helpers
    # ------------------------------------------------------------------
    async def _cid(self) -> str:
        """Resolve the company ID, fetching it if not configured."""
        if self._company_id:
            return self._company_id
        companies = await self.list_companies()
        if not companies:
            raise RuntimeError("No companies found on this Paperclip instance")
        self._company_id = companies[0]["id"]
        return self._company_id

    async def list_companies(self) -> list[dict[str, Any]]:
        """GET /api/companies"""
        r = await self._client.get("/api/companies")
        r.raise_for_status()
        return r.json()

    async def get_company(self) -> dict[str, Any]:
        """GET /api/companies/{id} (via list and filter)."""
        cid = await self._cid()
        companies = await self.list_companies()
        for c in companies:
            if c["id"] == cid:
                return c
        raise RuntimeError(f"Company {cid} not found")

    # ------------------------------------------------------------------
    # Agents
    # ------------------------------------------------------------------
    async def list_agents(self) -> list[dict[str, Any]]:
        """GET /api/companies/{id}/agents"""
        cid = await self._cid()
        r = await self._client.get(f"/api/companies/{cid}/agents")
        r.raise_for_status()
        return r.json()

    # ------------------------------------------------------------------
    # Issues
    # ------------------------------------------------------------------
    async def list_issues(
        self,
        status: str | None = None,
        priority: str | None = None,
    ) -> list[dict[str, Any]]:
        """GET /api/companies/{id}/issues with optional filters."""
        cid = await self._cid()
        params: dict[str, str] = {}
        if status:
            params["status"] = status
        if priority:
            params["priority"] = priority
        r = await self._client.get(f"/api/companies/{cid}/issues", params=params)
        r.raise_for_status()
        return r.json()

    async def get_issue(self, issue_id: str) -> dict[str, Any]:
        """GET /api/companies/{cid}/issues/{iid}"""
        cid = await self._cid()
        r = await self._client.get(f"/api/companies/{cid}/issues/{issue_id}")
        r.raise_for_status()
        return r.json()

    async def create_issue(
        self,
        title: str,
        description: str = "",
        priority: str = "medium",
        assignee_agent_id: str | None = None,
        project_id: str | None = None,
    ) -> dict[str, Any]:
        """POST /api/companies/{id}/issues"""
        cid = await self._cid()
        payload: dict[str, Any] = {
            "title": title,
            "description": description,
            "priority": priority,
        }
        if assignee_agent_id:
            payload["assigneeAgentId"] = assignee_agent_id
        if project_id:
            payload["projectId"] = project_id
        r = await self._client.post(f"/api/companies/{cid}/issues", json=payload)
        r.raise_for_status()
        return r.json()

    async def update_issue(
        self,
        issue_id: str,
        *,
        title: str | None = None,
        description: str | None = None,
        status: str | None = None,
        priority: str | None = None,
    ) -> dict[str, Any]:
        """PATCH /api/companies/{cid}/issues/{iid}"""
        cid = await self._cid()
        payload: dict[str, Any] = {}
        if title is not None:
            payload["title"] = title
        if description is not None:
            payload["description"] = description
        if status is not None:
            payload["status"] = status
        if priority is not None:
            payload["priority"] = priority
        r = await self._client.patch(
            f"/api/companies/{cid}/issues/{issue_id}", json=payload
        )
        r.raise_for_status()
        return r.json()

    # ------------------------------------------------------------------
    # Projects
    # ------------------------------------------------------------------
    async def list_projects(self) -> list[dict[str, Any]]:
        """GET /api/companies/{id}/projects"""
        cid = await self._cid()
        r = await self._client.get(f"/api/companies/{cid}/projects")
        r.raise_for_status()
        return r.json()

    # ------------------------------------------------------------------
    # Environments
    # ------------------------------------------------------------------
    async def list_environments(self) -> list[dict[str, Any]]:
        """GET /api/companies/{id}/environments"""
        cid = await self._cid()
        r = await self._client.get(f"/api/companies/{cid}/environments")
        r.raise_for_status()
        return r.json()

    # ------------------------------------------------------------------
    # Members
    # ------------------------------------------------------------------
    async def list_members(self) -> dict[str, Any]:
        """GET /api/companies/{id}/members"""
        cid = await self._cid()
        r = await self._client.get(f"/api/companies/{cid}/members")
        r.raise_for_status()
        return r.json()

    # ------------------------------------------------------------------
    # Invites
    # ------------------------------------------------------------------
    async def list_invites(self) -> dict[str, Any]:
        """GET /api/companies/{id}/invites"""
        cid = await self._cid()
        r = await self._client.get(f"/api/companies/{cid}/invites")
        r.raise_for_status()
        return r.json()


# Module-level singleton (created lazily)
_client: PaperclipClient | None = None


def get_client() -> PaperclipClient:
    global _client
    if _client is None:
        _client = PaperclipClient()
    return _client
