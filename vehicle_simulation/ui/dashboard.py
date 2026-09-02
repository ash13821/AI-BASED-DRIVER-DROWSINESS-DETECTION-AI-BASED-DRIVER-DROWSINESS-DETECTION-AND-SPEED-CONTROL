"""
ui/dashboard.py

Draws the on-screen dashboard: title, driver state, current/target speed,
brake status, obstacle distance, system status, warnings, and control hints.

This module only reads data that is handed to it - it does not make any
decisions itself.
"""

import pygame

import config


class Dashboard:
    """Renders the heads-up dashboard panel."""

    def __init__(self):
        pygame.font.init()
        self.font_title = pygame.font.SysFont("consolas", 26, bold=True)
        self.font_label = pygame.font.SysFont("consolas", 20, bold=True)
        self.font_value = pygame.font.SysFont("consolas", 20)
        self.font_small = pygame.font.SysFont("consolas", 15)
        self.font_warning = pygame.font.SysFont("consolas", 24, bold=True)

        self._blink_timer = 0.0
        self._blink_on = True

    def update(self, dt: float):
        """Advance the blink timer used for flashing warnings."""
        self._blink_timer += dt
        if self._blink_timer >= 0.4:
            self._blink_timer = 0.0
            self._blink_on = not self._blink_on

    def _draw_label_value(self, surface, x, y, label, value, value_color):
        label_surf = self.font_label.render(label, True, config.COLOR_TEXT_DIM)
        surface.blit(label_surf, (x, y))
        value_surf = self.font_value.render(str(value), True, value_color)
        surface.blit(value_surf, (x, y + 22))

    def draw(self, surface: pygame.Surface, *, driver_state: str,
              current_speed: float, target_speed: float, brake_status: str,
              obstacle_distance: float, status_text: str, warning: bool):

        panel_width = 260
        panel = pygame.Rect(16, 16, panel_width, config.SCREEN_HEIGHT - 32)
        panel_surface = pygame.Surface((panel.width, panel.height), pygame.SRCALPHA)
        panel_surface.fill((*config.COLOR_PANEL_BG, 215))
        surface.blit(panel_surface, panel.topleft)
        pygame.draw.rect(surface, (70, 70, 78), panel, width=2, border_radius=10)

        x = panel.left + 18
        y = panel.top + 16

        title_surf = self.font_title.render("AI VEHICLE", True, config.COLOR_TEXT)
        surface.blit(title_surf, (x, y))
        y += 28
        title_surf2 = self.font_title.render("SAFETY SIM", True, config.COLOR_TEXT)
        surface.blit(title_surf2, (x, y))
        y += 44

        # Driver state
        driver_color = config.COLOR_GOOD if driver_state == config.STATE_AWAKE else config.COLOR_DANGER
        self._draw_label_value(surface, x, y, "Driver State:", driver_state, driver_color)
        y += 54

        # Speeds
        self._draw_label_value(surface, x, y, "Current Speed:",
                                f"{current_speed:5.1f} km/h", config.COLOR_TEXT)
        y += 54
        self._draw_label_value(surface, x, y, "Target Speed:",
                                f"{target_speed:5.1f} km/h", config.COLOR_TEXT_DIM)
        y += 54

        # Brake status
        if brake_status == config.BRAKE_OFF:
            brake_color = config.COLOR_GOOD
        elif brake_status == config.BRAKE_ACTIVE:
            brake_color = config.COLOR_WARNING
        else:
            brake_color = config.COLOR_DANGER
        self._draw_label_value(surface, x, y, "Brake:", brake_status, brake_color)
        y += 54

        # Obstacle distance
        if obstacle_distance < config.EMERGENCY_DISTANCE:
            dist_color = config.COLOR_DANGER
        elif obstacle_distance < config.SAFE_DISTANCE:
            dist_color = config.COLOR_WARNING
        else:
            dist_color = config.COLOR_TEXT
        self._draw_label_value(surface, x, y, "Obstacle Distance:",
                                f"{obstacle_distance:5.1f} m", dist_color)
        y += 60

        # System status
        status_label = self.font_label.render("System Status:", True, config.COLOR_TEXT_DIM)
        surface.blit(status_label, (x, y))
        y += 26
        for line in status_text.split("\n"):
            status_color = config.COLOR_DANGER if warning else config.COLOR_GOOD
            status_surf = self.font_value.render(line, True, status_color)
            surface.blit(status_surf, (x, y))
            y += 24

        # Controls hint at the bottom of the panel
        hint_y = panel.bottom - 130
        hints = [
            "Controls:",
            " A  -> Driver AWAKE",
            " D  -> Driver DROWSY",
            " O  -> Obstacle brakes",
            "      (demo trigger)",
            " R  -> Reset",
            " ESC -> Exit",
        ]
        for i, line in enumerate(hints):
            color = config.COLOR_TEXT_DIM if i > 0 else config.COLOR_TEXT
            hint_surf = self.font_small.render(line, True, color)
            surface.blit(hint_surf, (x, hint_y + i * 18))

        # Big flashing warning banner across the top of the road when active
        if warning and self._blink_on:
            self._draw_warning_banner(surface, status_text)

    def _draw_warning_banner(self, surface: pygame.Surface, status_text: str):
        banner_text = status_text.split("\n")[0]
        text_surf = self.font_warning.render(f"WARNING: {banner_text}", True, (255, 255, 255))

        banner_width = text_surf.get_width() + 40
        banner_height = text_surf.get_height() + 16
        banner_x = (config.SCREEN_WIDTH - banner_width) // 2 + 130
        banner_rect = pygame.Rect(banner_x, 20, banner_width, banner_height)

        banner_surface = pygame.Surface((banner_rect.width, banner_rect.height), pygame.SRCALPHA)
        banner_surface.fill((*config.COLOR_DANGER, 230))
        surface.blit(banner_surface, banner_rect.topleft)
        pygame.draw.rect(surface, (255, 255, 255), banner_rect, width=2, border_radius=6)

        text_rect = text_surf.get_rect(center=banner_rect.center)
        surface.blit(text_surf, text_rect)
