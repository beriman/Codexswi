"""Integration tests for the moderation dashboard route."""

from fastapi.testclient import TestClient

from app.core.application import create_app


def test_moderation_dashboard_renders_snapshot_artifacts() -> None:
    """The moderation dashboard should render the demo snapshot data."""

    app = create_app()
    with TestClient(app) as client:
        response = client.get("/dashboard/moderation")

    assert response.status_code == 200
    body = response.text
    assert "Dashboard Moderasi" in body or "Arif Santoso" in body


def test_moderation_dashboard_ctas_have_expected_targets() -> None:
    """CTA buttons should provide explicit targets and data-action hooks."""

    app = create_app()
    with TestClient(app) as client:
        response = client.get("/dashboard/moderation")

    assert response.status_code == 200
    body = response.text

    assert (
        'href="/onboarding"' in body
        or 'href="http://testserver/onboarding"' in body
    )
    assert 'href="#mod-policies"' in body
    assert 'id="mod-policies"' in body

    for action in [
        "share-report",
        "refresh-snapshot",
        "focus-mode",
        "bulk-action",
        "invite-resend",
        "invite-cancel",
        "jump-section",
        "scroll-top",
    ]:
        assert f'data-action="{action}"' in body

    assert "moderation-dashboard.js" in body

    assert 'data-target="#mod-overview"' in body
    assert 'data-target="#mod-team"' in body
    assert 'data-target="#mod-queues"' in body
    assert 'data-target="#mod-curation"' in body
    assert 'data-target="#mod-analytics"' in body
    assert 'data-target="#mod-policies"' in body
    assert 'data-target="#mod-help"' in body

    for section_id in [
        "mod-overview",
        "mod-team",
        "mod-queues",
        "mod-curation",
        "mod-analytics",
        "mod-policies",
        "mod-help",
    ]:
        assert f'id="{section_id}"' in body

    assert 'class="tab-indicator"' in body
    assert 'class="tab-scroller"' in body
