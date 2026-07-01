"""
completeness.py
---------------
Calculates a metadata completeness score (0-100) for an asset.

Scoring grid (13 fields total, each worth ~7.7 points):

  Mandatory (6 fields, total 55 points):
    asset_name, asset_type, description, created_by, usage_rights, owner

  Business (4 fields, total 30 points):
    domain, use_case, audience, funnel_stage

  Content (3 fields, total 15 points):
    keywords (list), visual_elements (list), tone

Returns an integer 0-100 rounded.
"""

from typing import Any


# ---------------------------------------------------------------------------
# Weighted field definitions
# format: (section, key, weight, is_list)
# ---------------------------------------------------------------------------

_FIELDS = [
    # Mandatory — heavier weight
    ("mandatory", "asset_name",    10, False),
    ("mandatory", "asset_type",    10, False),
    ("mandatory", "description",   10, False),
    ("mandatory", "created_by",     8, False),
    ("mandatory", "usage_rights",   8, False),
    ("mandatory", "owner",          8, False),

    # Business
    ("business",  "domain",         8, False),
    ("business",  "use_case",       8, False),
    ("business",  "audience",       8, False),
    ("business",  "funnel_stage",   8, False),

    # Content
    ("content",   "keywords",       6, True),
    ("content",   "visual_elements", 6, True),
    ("content",   "tone",           2, False),
]

_TOTAL_WEIGHT = sum(w for _, _, w, _ in _FIELDS)   # 100


def _is_filled(value: Any, is_list: bool) -> bool:
    """Return True if the value is considered 'filled' (non-empty)."""
    if value is None:
        return False
    if is_list:
        return isinstance(value, (list, tuple)) and len(value) > 0
    return bool(str(value).strip())


def calculate_completeness(asset_metadata: dict) -> int:
    """
    Calculate a completeness score 0-100 for the given asset_metadata dict.

    Args:
        asset_metadata: The full JSONB blob from Asset.asset_metadata
                        (keys: mandatory, business, content, ai_enrichment)

    Returns:
        Integer 0-100.
    """
    if not asset_metadata:
        return 0

    earned = 0
    for section, key, weight, is_list in _FIELDS:
        section_data = asset_metadata.get(section) or {}
        value = section_data.get(key)
        if _is_filled(value, is_list):
            earned += weight

    score = round((earned / _TOTAL_WEIGHT) * 100)
    return min(100, max(0, score))
