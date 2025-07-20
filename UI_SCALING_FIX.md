# UI Scaling Fix - Reverted

## Problem
The console text in the nk2dl panel was appearing very small on high-DPI displays (1.5x scale and above) due to incorrect scaling logic.

## Initial Fix and Reversion
Initially, the font scaling logic was dividing the font size by the scale factor instead of multiplying by it. After fixing this, it was discovered that the 1.5x scaling was making the text too large.

## Final Solution
Removed all UI scaling functionality and reverted to using the base font size directly:

```python
# REMOVED: Scaling logic
# scaled_font_size = max(1, int(Fonts.CONSOLE_FONT_SIZE * scale_factor))

# FINAL: Use base font size directly
font_size = Fonts.CONSOLE_FONT_SIZE  # 10pt
```

## Files Modified

### 1. `nk2dl/gui/panel/views/console_view.py`
- Removed all scaling logic
- Removed `_get_ui_scale_factor()` method
- Console now uses base font size of 10pt directly

### 2. `nk2dl/gui/panel/__init__.py`
- Removed scaling logic from info label
- Removed `_get_ui_scale_factor()` method
- Info label uses fixed 12px font size

## Impact
- Console text uses consistent 10pt font size regardless of display scaling
- Info label uses consistent 12px font size
- Simpler, more predictable font sizing behavior 