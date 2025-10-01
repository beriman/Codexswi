"""Template rendering tests for Nusantarum components."""

from app.services.nusantarum_service import PerfumerListItem
from app.web.templates import template_engine


def test_perfumer_list_item_template_renders_curated_badge_and_stats() -> None:
    template = template_engine.env.get_template(
        "components/nusantarum/perfumer-list-item.html"
    )
    perfumer = PerfumerListItem(
        id="pfmr-1",
        display_name="Ayu Pratiwi",
        slug="ayu-pratiwi",
        city="Bandung",
        bio_preview="Perfumer indie dengan fokus aroma tropis…",
        signature_scent="Tropical jasmine",
        active_perfume_count=2,
        followers_count=1200,
        years_active=5,
        is_curated=True,
        perfumer_profile_username="ayu-pratiwi",
        highlight_perfume="Hutan Senja",
        highlight_brand="Langit Senja",
        last_synced_at=None,
    )

    html = template.render(perfumer=perfumer)

    assert "Kurasi Nusantarum" in html
    assert "📍" in html
    assert "👥" in html
    assert "🕰️" in html
    assert "Perfumer indie dengan fokus aroma tropis…" in html
