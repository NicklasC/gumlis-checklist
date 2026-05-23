import flet as ft
from flet.controls.border import Border, BorderSide

# Visual design constants for Gumlis Checklista (Emerald & Mint Green Glassmorphism)

# Core Palette
BG_COLOR = "#0C100D"              # Midnight Forest (Extremely dark green-black)
SURFACE_COLOR = "#121A16"         # Dark Jade (Card background)
SURFACE_GLOW = "#182620"          # Lighter green-grey for hovered/active elements
SURFACE_GLASS = "#14241D"         # Translucent forest green base for glass containers

# Accents
EMERALD_GREEN = "#10B981"         # Vibrant Emerald Green (Primary)
MINT_GREEN = "#34D399"            # Bright Mint Green (Secondary/Accent)
GLOW_GREEN = "#059669"             # Rich green for shadows and highlights
MINT_LIGHT = "#A7F3D0"            # Very soft mint green for text highlights

# Text States
TEXT_PRIMARY = "#F3F4F6"          # Clean off-white
TEXT_MUTED = "#9CA3AF"            # Neutral slate gray
TEXT_SECONDARY = "#8E9E96"        # Sage green gray (subtle)
TEXT_DISABLED = "#4B5563"         # Darker gray for checked/inactive items

# Categories Colors (matching the pills)
CATEGORY_COLORS = {
    "Att göra": "#10B981",          # Emerald
    "Jobb": "#8B5CF6",              # Sleek Indigo/Purple for work
    "Packning & Förskola": "#3B82F6", # Sky Blue for kids
    "Inköp": "#F59E0B",             # Warm Amber for shopping
    "Planering": "#8B5CF6",         # Deep Purple for dates
    "Övrigt": "#6B7280"             # Neutral Gray
}

# Typography
FONT_FAMILY = "Outfit"             # Premium modern font (fallback to System)

def get_app_theme() -> ft.Theme:
    """Returns the central Theme configuration for Flet."""
    return ft.Theme(
        color_scheme=ft.ColorScheme(
            primary=EMERALD_GREEN,
            primary_container=GLOW_GREEN,
            secondary=MINT_GREEN,
            surface=SURFACE_COLOR,
            on_surface=TEXT_PRIMARY,
            outline=EMERALD_GREEN,
        ),
        font_family=FONT_FAMILY,
    )

def border_all(width: float, color) -> Border:
    """Replacement for the removed ft.border.all() helper."""
    side = BorderSide(width, color)
    return Border(top=side, right=side, bottom=side, left=side)

def glass_card_style(
    padding: float = 12,
    border_radius: float = 16,
    border_color: str = "#203028"
) -> dict:
    """Returns style configurations for a premium glassmorphic Flet container."""
    return {
        "bgcolor": ft.Colors.with_opacity(0.65, SURFACE_GLASS),
        "border": border_all(1.2, border_color),
        "border_radius": border_radius,
        "padding": padding,
        "shadow": ft.BoxShadow(
            spread_radius=1,
            blur_radius=8,
            color=ft.Colors.with_opacity(0.15, "#000000"),
            offset=ft.Offset(0, 4)
        )
    }

def active_item_style() -> dict:
    """Style configuration for a normal active checklist item row."""
    return {
        "bgcolor": ft.Colors.with_opacity(0.4, SURFACE_COLOR),
        "border": border_all(1, "#1B2A22"),
        "border_radius": 8,
        "padding": ft.Padding(left=8, top=6, right=8, bottom=6),
    }

def checked_item_style() -> dict:
    """Style configuration for a checked (completed) checklist item row."""
    return {
        "bgcolor": ft.Colors.with_opacity(0.1, EMERALD_GREEN),
        "border": border_all(1, ft.Colors.with_opacity(0.2, EMERALD_GREEN)),
        "border_radius": 8,
        "padding": ft.Padding(left=8, top=6, right=8, bottom=6),
        "animate_opacity": 250,
    }
