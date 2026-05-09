"""Base class for internationalisation strings."""

from dataclasses import dataclass


@dataclass
class Strings:
    """All user-facing strings. Override values in locale files."""

    # Auth
    unauthorized: str = ""
    admin_only: str = ""
    rate_limited: str = ""

    # Errors
    error_generic: str = ""
    error_api_unreachable: str = ""
    error_api_timeout: str = ""
    error_not_found: str = ""
    error_api_unauthorized: str = ""
    error_api_server: str = ""

    # Basic commands
    welcome: str = ""
    help_text: str = ""

    # Empty states
    no_issues: str = ""
    no_projects: str = ""
    no_agents: str = ""
    no_environments: str = ""
    no_members: str = ""
    no_invites: str = ""
    no_companies: str = ""

    # Issue creation
    create_title_prompt: str = ""
    create_desc_prompt: str = ""
    create_priority_prompt: str = ""
    create_project_prompt: str = ""
    create_agent_prompt: str = ""
    create_confirm: str = ""
    create_success: str = ""
    create_cancelled: str = ""

    # Issue update
    update_select_field: str = ""
    update_enter_value: str = ""
    update_success: str = ""
    update_cancelled: str = ""
    update_issue_not_found: str = ""
    update_usage: str = ""

    # Admin
    broadcast_prompt: str = ""
    broadcast_sent: str = ""

    # Digest
    digest_header: str = ""
    digest_no_issues: str = ""

    # Misc
    unknown_command: str = ""
    skip: str = ""
    cancel: str = ""
    confirm: str = ""
    back: str = ""
    nlp_no_match: str = ""

    # --- UX Enhancements ---

    # Search
    search_prompt: str = ""
    search_no_results: str = ""
    search_results_header: str = ""

    # Status shortcuts
    close_success: str = ""
    reopen_success: str = ""
    close_usage: str = ""
    reopen_usage: str = ""

    # Bulk actions
    bulk_close_confirm: str = ""
    bulk_close_success: str = ""
    bulk_close_cancelled: str = ""
    bulk_close_usage: str = ""

    # Undo
    undo_prompt: str = ""
    undo_success: str = ""
    undo_expired: str = ""

    # Pin
    pin_success: str = ""
    pin_failed: str = ""

    # Onboarding
    onboarding_step1: str = ""
    onboarding_step2: str = ""
    onboarding_step3: str = ""
    onboarding_complete: str = ""

    # Notifications
    notify_usage: str = ""
    notify_updated: str = ""

    # Dashboard
    dashboard_refresh: str = ""
