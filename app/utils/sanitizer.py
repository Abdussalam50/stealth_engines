"""
HTML Sanitization Utility
Uses bleach to prevent XSS attacks by cleaning user-generated HTML content
"""
import bleach
from typing import Optional

# Allowed HTML tags
ALLOWED_TAGS = [
    'p', 'br', 'strong', 'em', 'b', 'i', 'u', 's',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li',
    'a', 'blockquote', 'code', 'pre',
    'div', 'span', 'hr'
]

# Allowed attributes per tag
ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'rel'],
    'img': ['src', 'alt', 'title'],
    '*': ['class']  # Allow class on any tag
}

# Allowed URL protocols
ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']

def sanitize_html(content: Optional[str]) -> Optional[str]:
    """
    Sanitize HTML content to prevent XSS attacks
    
    Args:
        content: Raw HTML content from user input
        
    Returns:
        Sanitized HTML safe for rendering
    """
    if not content:
        return content
    
    cleaned = bleach.clean(
        content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True  # Strip disallowed tags instead of escaping
    )
    
    # Also run linkify to make URLs clickable but safe
    cleaned = bleach.linkify(
        cleaned,
        parse_email=True
    )
    
    return cleaned

def sanitize_text(content: Optional[str]) -> Optional[str]:
    """
    Sanitize plain text by escaping all HTML
    Use for fields that should never contain HTML (title, meta, etc.)
    
    Args:
        content: Text content
        
    Returns:
        Escaped text safe for rendering
    """
    if not content:
        return content
    
    return bleach.clean(content, tags=[], strip=True)
