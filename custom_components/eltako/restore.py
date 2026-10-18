"""Validation for optional values restored from Home Assistant state history."""
from math import isfinite


def restore_number(value, *, minimum=None, maximum=None):
    """Return a finite saved number, or None for a missing value.

    Invalid values are rejected so a caller can discard a corrupt saved state
    without publishing strings, infinities or out-of-range positions to HA.
    """
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError("Boolean is not a numeric state")
    number = float(value)
    if not isfinite(number):
        raise ValueError("Non-finite saved state")
    if minimum is not None and number < minimum:
        raise ValueError("Saved state below minimum")
    if maximum is not None and number > maximum:
        raise ValueError("Saved state above maximum")
    return number
