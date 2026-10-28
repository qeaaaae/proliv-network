from bot.handlers.admin.nodes_geo import flag, render_location_block

TEXTS = {
    "admin_nodes_geo_mismatch": "Видят другую страну:",
    "admin_nodes_geo_all_match": "Все сервисы видят {cc}",
    "admin_nodes_geo_blocked": "Недоступно: {items}",
    "admin_nodes_geo_checked": "проверка {stamp} UTC",
    "admin_nodes_geo_reddit_guest": "Reddit без входа",
    "admin_nodes_geo_spotify_signup": "регистрация Spotify",
}


def _(key: str, **kwargs: object) -> str:
    return TEXTS[key].format(**kwargs)


def test_flag() -> None:
    assert flag("de") == "🇩🇪"
    assert flag("x") == ""


def test_location_block_groups_mismatches_blocked_and_cdn() -> None:
    geo = {
        "checked_at": 0,
        "primary": {
            "ifconfig.co": "US",
            "ipinfo.io": "DE",
            "ipapi.co": "Rate-limit",
            "ipapi.is": "null",
        },
        "custom": {
            "YouTube": "RU",
            "JetBrains": "US",
            "Google": "DE",
            "Reddit": "Denied",
            "Reddit (Guest Access)": "No",
            "Disney+": "null",
            "Disney+ Access": "No",
            "Gemini Supported": "Yes",
        },
        "cdn": {"Cloudflare CDN": "DE (FRA)", "YouTube CDN": "US (SFO)", "Netflix CDN": "N/A"},
    }
    out = render_location_block("🟢 🇩🇪 <b>Германия</b> · DE", ["📈 load 0.1"], "DE", geo, _)

    assert out.startswith("<blockquote>🟢 🇩🇪 <b>Германия</b> · DE\n📈 load 0.1\n")
    assert out.endswith("</blockquote>")
    assert '🇺🇸 US: <a href="https://ifconfig.co">ifconfig.co</a>, JetBrains' in out
    assert "🇷🇺 RU: YouTube" in out
    assert "ipinfo.io" not in out and "Google" not in out and "ipapi" not in out
    assert "Недоступно: Reddit, Reddit без входа, Disney+" in out
    assert "CDN: Cloudflare 🇩🇪 DE · YouTube 🇺🇸 US" in out
    assert "Netflix" not in out
    assert "проверка" not in out


def test_location_block_all_match_and_without_geo() -> None:
    geo = {"primary": {"ipinfo.io": "GB"}, "checked_at": 86400}
    out = render_location_block("UK", [], "GB", geo, _)
    assert "Все сервисы видят GB" in out
    assert "проверка 02.01 00:00 UTC" in out
    assert render_location_block("UK", ["x"], "GB", None, _) == "<blockquote>UK\nx</blockquote>"
