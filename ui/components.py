"""
components.py
-------------
Reusable UI component factory functions for the InventoryAI application.
Each function returns a Flet widget configured with the application's design system.
"""

import flet as ft
from ui.theme import (
    CARD_BACKGROUND,
    SURFACE_DARK,
    BORDER_DEFAULT,
    ACCENT_PRIMARY,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    COLOR_SUCCESS,
    COLOR_DANGER,
)


def build_card(
    card_content: ft.Control,
    card_padding=20,
    card_border_radius=16,
    card_background_color=CARD_BACKGROUND,
    should_expand=False,
    **extra_kwargs,
):
    return ft.Container(
        content=card_content,
        bgcolor=card_background_color,
        border_radius=card_border_radius,
        padding=card_padding,
        expand=should_expand,
        border=ft.Border.all(1, BORDER_DEFAULT),
        **extra_kwargs,
    )


def build_status_badge(badge_label, badge_color):
    return ft.Container(
        content=ft.Text(
            badge_label,
            size=11,
            color=badge_color,
            weight=ft.FontWeight.W_600,
        ),
        bgcolor=ft.Colors.with_opacity(0.15, badge_color),
        border_radius=20,
        padding=ft.Padding.symmetric(horizontal=10, vertical=4),
    )


def build_section_title(
    title_text,
    subtitle_text="",
):
    title_widgets = [
        ft.Text(title_text, size=22, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY)
    ]
    if subtitle_text:
        title_widgets.append(ft.Text(subtitle_text, size=13, color=TEXT_SECONDARY))
    return ft.Column(title_widgets, spacing=2)


def build_stat_card(
    stat_icon,
    stat_label,
    stat_value,
    trend_percentage=None,
    icon_color=ACCENT_PRIMARY,
):
    is_positive_trend = trend_percentage is not None and trend_percentage > 0
    trend_color = COLOR_SUCCESS if is_positive_trend else COLOR_DANGER
    trend_icon = ft.Icons.TRENDING_UP if is_positive_trend else ft.Icons.TRENDING_DOWN

    trend_widget = (
        ft.Row(
            [
                ft.Icon(trend_icon, size=14, color=trend_color),
                ft.Text(f"{abs(trend_percentage)}%", size=12, color=trend_color),
            ],
            spacing=2,
        )
        if trend_percentage is not None
        else ft.Container()
    )

    icon_container = ft.Container(
        ft.Icon(stat_icon, color=icon_color, size=22),
        bgcolor=ft.Colors.with_opacity(0.15, icon_color),
        border_radius=10,
        padding=10,
    )

    return build_card(
        ft.Column(
            [
                ft.Row(
                    [
                        icon_container,
                        ft.Container(expand=True),
                        trend_widget,
                    ]
                ),
                ft.Container(height=12),
                ft.Text(
                    str(stat_value),
                    size=28,
                    weight=ft.FontWeight.BOLD,
                    color=TEXT_PRIMARY,
                ),
                ft.Text(stat_label, size=13, color=TEXT_SECONDARY),
            ],
            spacing=0,
        ),
        card_padding=20,
    )


def build_page_header(
    header_title,
    header_subtitle,
    header_icon,
    action_buttons=None,
):
    header_items = [
        ft.Container(
            ft.Icon(header_icon, color=ACCENT_PRIMARY, size=26),
            bgcolor=ft.Colors.with_opacity(0.15, ACCENT_PRIMARY),
            border_radius=12,
            padding=10,
        ),
        ft.Column(
            [
                ft.Text(
                    header_title,
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=TEXT_PRIMARY,
                ),
                ft.Text(header_subtitle, size=13, color=TEXT_SECONDARY),
            ],
            spacing=2,
        ),
        ft.Container(expand=True),
    ]
    if action_buttons:
        header_items.extend(action_buttons)

    return ft.Row(
        header_items,
        spacing=14,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )


def build_data_table(
    column_labels,
    table_rows,
):
    data_columns = [
        ft.DataColumn(
            ft.Text(
                column_label,
                color=TEXT_SECONDARY,
                size=12,
                weight=ft.FontWeight.W_600,
            )
        )
        for column_label in column_labels
    ]

    return ft.DataTable(
        columns=data_columns,
        rows=table_rows,
        border=ft.Border.all(1, BORDER_DEFAULT),
        border_radius=12,
        horizontal_lines=ft.BorderSide(1, BORDER_DEFAULT),
        heading_row_color=ft.Colors.with_opacity(0.3, SURFACE_DARK),
        heading_row_height=44,
        data_row_max_height=52,
        column_spacing=20,
    )


def build_action_button(
    button_label,
    button_icon,
    on_click_handler=None,
    button_color=ACCENT_PRIMARY,
    is_filled=True,
):
    return ft.ElevatedButton(
        button_label,
        icon=button_icon,
        on_click=on_click_handler,
        bgcolor=button_color if is_filled else "transparent",
        color=TEXT_PRIMARY if is_filled else button_color,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            side=None if is_filled else ft.BorderSide(1, button_color),
        ),
    )


def build_mini_bar_chart(
    bar_values,
    bar_labels,
    bar_color=ACCENT_PRIMARY,
    chart_height=120,
):
    maximum_value = max(bar_values) if bar_values else 1
    bar_column_widgets = []

    for individual_value, individual_label in zip(bar_values, bar_labels):
        bar_fill_ratio = individual_value / maximum_value if maximum_value != 0 else 0
        bar_pixel_height = bar_fill_ratio * (chart_height - 30)

        bar_column = ft.Column(
            [
                ft.Text(
                    str(individual_value),
                    size=10,
                    color=TEXT_SECONDARY,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(
                    ft.Container(
                        bgcolor=bar_color,
                        border_radius=4,
                        height=bar_pixel_height,
                    ),
                    height=chart_height - 30,
                    alignment=ft.Alignment.BOTTOM_CENTER,
                ),
                ft.Text(
                    individual_label,
                    size=10,
                    color=TEXT_SECONDARY,
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=4,
            expand=True,
        )
        bar_column_widgets.append(bar_column)

    return ft.Row(
        bar_column_widgets,
        spacing=8,
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        expand=True,
    )


def build_auth_text_field(
    field_label: str,
    field_hint: str,
    field_prefix_icon: str,
    is_password_field: bool = False,
):
    from ui.theme import (
        SURFACE_DARK,
        BORDER_DEFAULT,
        ACCENT_PRIMARY,
        TEXT_PRIMARY,
        TEXT_SECONDARY,
    )

    return ft.TextField(
        label=field_label,
        hint_text=field_hint,
        prefix_icon=field_prefix_icon,
        password=is_password_field,
        can_reveal_password=is_password_field,
        bgcolor=SURFACE_DARK,
        border_color=BORDER_DEFAULT,
        focused_border_color=ACCENT_PRIMARY,
        color=TEXT_PRIMARY,
        label_style=ft.TextStyle(color=TEXT_SECONDARY),
        hint_style=ft.TextStyle(color=TEXT_SECONDARY),
        border_radius=12,
    )
