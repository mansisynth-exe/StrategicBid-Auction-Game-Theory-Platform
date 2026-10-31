"""
metrics.py: KPI cards, formatting helpers, and presentation utilities for StrategicBid.
Ensures consistent currency formatting, statistical sample sizes, and limitation tags.
"""

from typing import Union, Optional, Dict, Any


def format_currency(value: Union[float, int, None]) -> str:
    """Formats numeric value as USD currency string."""
    if value is None or (isinstance(value, float) and (value != value)):  # NaN check
        return "N/A"
    return f"${value:,.2f}"


def format_percentage(value: Union[float, int, None], decimals: int = 1) -> str:
    """Formats decimal or float value as percentage."""
    if value is None or (isinstance(value, float) and (value != value)):
        return "N/A"
    return f"{value:.{decimals}f}%"


def format_integer(value: Union[int, float, None]) -> str:
    """Formats integer with commas."""
    if value is None or (isinstance(value, float) and (value != value)):
        return "N/A"
    return f"{int(value):,}"


def build_kpi_card(
    label: str,
    value: str,
    subtitle: Optional[str] = None,
    delta: Optional[str] = None,
    help_text: Optional[str] = None
) -> Dict[str, Any]:
    """Constructs a structured KPI dictionary for UI display."""
    return {
        "label": label,
        "value": value,
        "subtitle": subtitle,
        "delta": delta,
        "help_text": help_text
    }
