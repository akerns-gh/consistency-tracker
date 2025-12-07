"""
HTML sanitization utilities using bleach.
"""

try:
    import bleach
    from bleach.css_sanitizer import CSSSanitizer
except ImportError:
    # Fallback if bleach is not available (shouldn't happen in Lambda layer)
    bleach = None
    CSSSanitizer = None


# Allowed HTML tags for content pages
ALLOWED_TAGS = [
    "p", "br", "strong", "em", "u", "h1", "h2", "h3", "h4", "h5", "h6",
    "ul", "ol", "li", "a", "img", "blockquote", "div", "span",
    "table", "thead", "tbody", "tr", "th", "td",
    "iframe",  # For embedded videos
]

# Allowed HTML attributes
ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", "target", "rel"],
    "img": ["src", "alt", "title", "width", "height"],
    "iframe": ["src", "width", "height", "frameborder", "allowfullscreen"],
    "div": ["class"],
    "span": ["class"],
    "p": ["class"],
    "table": ["class"],
    "th": ["class", "colspan", "rowspan"],
    "td": ["class", "colspan", "rowspan"],
}

# Allowed CSS properties (for style attributes)
ALLOWED_CSS = [
    "color", "background-color", "text-align", "font-size", "font-weight",
    "font-family", "margin", "padding", "border", "width", "height",
]

# Allowed URL schemes
ALLOWED_SCHEMES = ["http", "https", "mailto"]


def sanitize_html(html_content: str) -> str:
    """
    Sanitize HTML content to prevent XSS attacks.

    Args:
        html_content: Raw HTML content from user input

    Returns:
        Sanitized HTML content safe for display
    """
    if not html_content:
        return ""

    if bleach is None:
        # Fallback: strip all HTML tags if bleach is not available
        import re
        return re.sub(r"<[^>]+>", "", html_content)

    # Configure CSS sanitizer
    css_sanitizer = None
    if CSSSanitizer:
        css_sanitizer = CSSSanitizer(allowed_css_properties=ALLOWED_CSS)

    # Sanitize HTML
    sanitized = bleach.clean(
        html_content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        css_sanitizer=css_sanitizer,
        protocols=ALLOWED_SCHEMES,
        strip=True,  # Strip disallowed tags instead of escaping
    )

    return sanitized


def sanitize_text(text: str) -> str:
    """
    Sanitize plain text content (escape HTML).

    Args:
        text: Plain text content

    Returns:
        HTML-escaped text safe for display
    """
    if not text:
        return ""

    if bleach is None:
        # Fallback: basic HTML escaping
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#x27;")
        )

    return bleach.clean(text, tags=[], strip=True)

