"""Tests for PaperclipClient."""

import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.fixture
def mock_response():
    """Create a mock httpx.Response."""
    def _make(json_data, status_code=200):
        resp = MagicMock(spec=httpx.Response)
        resp.status_code = status_code
        resp.json.return_value = json_data
        resp.raise_for_status = MagicMock()
        if status_code >= 400:
            resp.raise_for_status.side_effect = httpx.HTTPStatusError(
                "error", request=MagicMock(), response=resp
            )
        return resp
    return _make


@pytest.mark.asyncio
async def test_health(mock_response):
    """Test health endpoint returns parsed JSON."""
    from paperclip_client import PaperclipClient

    client = PaperclipClient(base_url="http://test:3100")
    expected = {"status": "ok"}

    with patch.object(client._client, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response(expected)
        result = await client.health()
        assert result == expected
        mock_get.assert_called_once_with("/api/health")

    await client.close()


@pytest.mark.asyncio
async def test_list_issues_with_filters(mock_response):
    """Test list_issues passes status/priority as query params."""
    from paperclip_client import PaperclipClient

    client = PaperclipClient(base_url="http://test:3100")
    client._company_id = "comp-1"

    issues = [{"id": "i1", "title": "Bug", "status": "open", "priority": "high"}]

    with patch.object(client._client, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response(issues)
        result = await client.list_issues(status="open", priority="high")
        assert result == issues
        mock_get.assert_called_once_with(
            "/api/companies/comp-1/issues",
            params={"status": "open", "priority": "high"},
        )

    await client.close()


@pytest.mark.asyncio
async def test_create_issue(mock_response):
    """Test create_issue sends correct payload."""
    from paperclip_client import PaperclipClient

    client = PaperclipClient(base_url="http://test:3100")
    client._company_id = "comp-1"

    created = {"id": "i2", "title": "New Bug", "status": "open", "priority": "medium"}

    with patch.object(client._client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response(created)
        result = await client.create_issue(title="New Bug", description="desc", priority="medium")
        assert result == created
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        assert call_kwargs[1]["json"]["title"] == "New Bug"

    await client.close()


@pytest.mark.asyncio
async def test_cid_auto_detection(mock_response):
    """Test company ID auto-detection from list_companies."""
    from paperclip_client import PaperclipClient

    client = PaperclipClient(base_url="http://test:3100")
    client._company_id = ""  # Force auto-detect

    companies = [{"id": "auto-1", "name": "Test Corp"}]

    with patch.object(client._client, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response(companies)
        cid = await client._cid()
        assert cid == "auto-1"

    await client.close()
