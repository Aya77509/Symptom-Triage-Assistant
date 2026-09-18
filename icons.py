"""
Small set of hand-authored, stroke-style SVG icons (no emoji, no external
icon font/library — everything here is self-contained so the app has no
extra dependency and no network call just to render an icon).

Every icon uses stroke="currentColor", so wrap icon(...) in an element with
a CSS `color` set and the icon inherits it automatically.
"""

_ICON_PATHS = {
    # Header / brand icon - a simple activity/pulse line
    "pulse": '<path d="M3 12h4l2-7 4 14 2-7h6"/>',
    # EMERGENCY - triangle with exclamation mark
    "alert_triangle": (
        '<path d="M12 3 2 20h20L12 3z"/>'
        '<line x1="12" y1="10" x2="12" y2="14"/>'
        '<circle cx="12" cy="17" r="0.5" fill="currentColor" stroke="none"/>'
    ),
    # URGENT - clock face
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 3"/>',
    # ROUTINE - calendar with a check mark
    "calendar_check": (
        '<rect x="3" y="5" width="18" height="16" rx="2"/>'
        '<line x1="3" y1="10" x2="21" y2="10"/>'
        '<line x1="8" y1="3" x2="8" y2="7"/>'
        '<line x1="16" y1="3" x2="16" y2="7"/>'
        '<path d="M8 15l2.5 2.5L16 12"/>'
    ),
    # SELF_CARE - simple house
    "home": '<path d="M4 11 12 4l8 7"/><path d="M6 10v10h12V10"/>',
    # Hybrid panel - shield with a check mark (verified)
    "shield_check": (
        '<path d="M12 3l7 3v6c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6l7-3z"/>'
        '<path d="M9 12l2 2 4-4"/>'
    ),
    # Baseline panel - question mark in a circle (unverified guess)
    "help_circle": (
        '<circle cx="12" cy="12" r="9"/>'
        '<path d="M9.5 9a2.5 2.5 0 1 1 3.5 2.3c-.8.4-1 .9-1 1.7"/>'
        '<circle cx="12" cy="17" r="0.5" fill="currentColor" stroke="none"/>'
    ),
    # Rule-fired label - a small checklist
    "list_check": (
        '<path d="M9 6h11"/><path d="M9 12h11"/><path d="M9 18h11"/>'
        '<path d="M4 6l1 1 2-2"/><path d="M4 12l1 1 2-2"/><path d="M4 18l1 1 2-2"/>'
    ),
    # Source citation label - a link
    "link": (
        '<path d="M9 15 15 9"/>'
        '<path d="M11 6l1-1a3.5 3.5 0 0 1 5 5l-1 1"/>'
        '<path d="M13 18l-1 1a3.5 3.5 0 0 1-5-5l1-1"/>'
    ),
    # Agreement banner - filled check circle outline
    "check_circle": '<circle cx="12" cy="12" r="9"/><path d="M8 12l2.5 2.5L16 9"/>',
    # Disagreement banner - octagon with exclamation
    "alert_octagon": (
        '<path d="M8 3h8l5 5v8l-5 5H8l-5-5V8l5-5z"/>'
        '<line x1="12" y1="8" x2="12" y2="13"/>'
        '<circle cx="12" cy="16" r="0.5" fill="currentColor" stroke="none"/>'
    ),
}


def icon(name: str, size: int = 18, stroke_width: float = 1.8) -> str:
    """Return an inline <svg> string for the named icon. Color is inherited
    from the CSS `color` of whatever wraps this (uses currentColor)."""
    path = _ICON_PATHS.get(name, "")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        f'stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round" '
        f'style="vertical-align:-3px;display:inline-block">{path}</svg>'
    )