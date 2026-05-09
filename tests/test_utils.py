"""Tests for utility modules: chunking, formatting, pagination, nlp."""

import pytest

from utils.chunking import chunk_text
from utils.formatting import format_issue, format_project, format_agent, format_health
from utils.pagination import paginate
from utils.nlp import parse_intent


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

class TestChunking:
    def test_short_text_single_chunk(self):
        result = chunk_text("hello", max_length=100)
        assert result == ["hello"]

    def test_splits_at_newline(self):
        text = "line1\nline2\nline3\nline4"
        result = chunk_text(text, max_length=12)
        assert len(result) >= 2
        for chunk in result:
            assert len(chunk) <= 12

    def test_hard_split_when_no_newline(self):
        text = "a" * 200
        result = chunk_text(text, max_length=50)
        assert len(result) == 4
        assert all(len(c) <= 50 for c in result)

    def test_empty_text(self):
        result = chunk_text("")
        assert result == [""]


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

class TestFormatting:
    def test_format_issue_contains_title(self):
        issue = {"id": "123", "title": "Test Bug", "status": "open", "priority": "high"}
        result = format_issue(issue)
        assert "Test Bug" in result
        assert "🟢" in result  # open status
        assert "123" in result

    def test_format_issue_html_escapes(self):
        issue = {"id": "1", "title": "<script>alert(1)</script>", "status": "open", "priority": "low"}
        result = format_issue(issue)
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_format_project(self):
        project = {"id": "p1", "name": "Project Alpha"}
        result = format_project(project)
        assert "Project Alpha" in result
        assert "p1" in result

    def test_format_agent(self):
        agent = {"id": "a1", "name": "Bot One", "role": "developer"}
        result = format_agent(agent)
        assert "Bot One" in result
        assert "developer" in result

    def test_format_health_ok(self):
        data = {"status": "ok", "uptime": "99.9%"}
        result = format_health(data)
        assert "✅" in result

    def test_format_health_down(self):
        data = {"status": "down"}
        result = format_health(data)
        assert "❌" in result


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------

class TestPagination:
    def test_single_page_no_keyboard(self):
        items = [{"id": str(i), "title": f"Item {i}", "status": "open", "priority": "low"} for i in range(5)]
        text, keyboard = paginate(items, page=0, prefix="test", formatter=format_issue)
        assert keyboard is None
        assert "Item 0" in text

    def test_multi_page_has_keyboard(self):
        items = [{"id": str(i), "title": f"Item {i}", "status": "open", "priority": "low"} for i in range(25)]
        text, keyboard = paginate(items, page=0, prefix="test", formatter=format_issue, page_size=10)
        assert keyboard is not None
        assert "Page 1/" in text
        # Should have Next button
        buttons = keyboard.inline_keyboard[0]
        assert any("Next" in b.text for b in buttons)

    def test_last_page_no_next_button(self):
        items = [{"id": str(i), "title": f"Item {i}", "status": "open", "priority": "low"} for i in range(15)]
        text, keyboard = paginate(items, page=1, prefix="test", formatter=format_issue, page_size=10)
        assert keyboard is not None
        buttons = keyboard.inline_keyboard[0]
        assert not any("Next" in b.text for b in buttons)
        assert any("Prev" in b.text for b in buttons)

    def test_empty_items(self):
        text, keyboard = paginate([], page=0, prefix="test", formatter=format_issue)
        assert text == ""
        assert keyboard is None


# ---------------------------------------------------------------------------
# NLP
# ---------------------------------------------------------------------------

class TestNLP:
    def test_list_issues_intent(self):
        intent = parse_intent("show me all issues")
        assert intent is not None
        assert intent.action == "list_issues"

    def test_list_issues_with_priority(self):
        intent = parse_intent("show me critical bugs")
        assert intent is not None
        assert intent.action == "list_issues"
        assert intent.filters.get("priority") == "critical"

    def test_list_issues_with_status(self):
        intent = parse_intent("list open tickets")
        assert intent is not None
        assert intent.action == "list_issues"
        assert intent.filters.get("status") == "open"

    def test_create_issue_intent(self):
        intent = parse_intent("create a new bug")
        assert intent is not None
        assert intent.action == "create_issue"

    def test_health_intent(self):
        intent = parse_intent("is the api alive?")
        assert intent is not None
        assert intent.action == "health"

    def test_help_intent(self):
        intent = parse_intent("help me please")
        assert intent is not None
        assert intent.action == "help"

    def test_no_match(self):
        intent = parse_intent("what is the meaning of life")
        assert intent is None

    def test_projects_intent(self):
        intent = parse_intent("show all projects")
        assert intent is not None
        assert intent.action == "list_projects"

    def test_members_intent(self):
        intent = parse_intent("list team members")
        assert intent is not None
        assert intent.action == "list_members"
