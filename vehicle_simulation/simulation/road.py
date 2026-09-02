"""
simulation/road.py

Renders the road: boundaries, lane markings, scrolling effect, and a simple
surrounding environment. The scroll speed is driven by the player's current
speed so faster driving visually feels faster.
"""

import pygame

import config


class Road:
    """Handles drawing and scrolling of the road surface and lane markings."""

    def __init__(self):
        self.scroll_offset = 0.0
        self.dash_period = config.DASH_LENGTH + config.DASH_GAP

    def reset(self):
        self.scroll_offset = 0.0

    def update(self, dt: float, current_speed_kmh: float):
        """Advance the scroll offset based on the vehicle's current speed."""
        speed_m_per_s = current_speed_kmh * (1000.0 / 3600.0)
        speed_px_per_s = speed_m_per_s * config.PIXELS_PER_METER
        self.scroll_offset = (self.scroll_offset + speed_px_per_s * dt) % self.dash_period

    def draw(self, surface: pygame.Surface):
        # Environment (grass background)
        surface.fill(config.COLOR_BACKGROUND)

        # A little bit of texture on the grass so it doesn't look flat -
        # simple static side "trees"/bushes as green circles.
        for side_x in (config.ROAD_LEFT - 60, config.ROAD_RIGHT + 60):
            for y in range(20, config.SCREEN_HEIGHT, 90):
                pygame.draw.circle(surface, (24, 74, 38), (side_x, y), 22)

        # Road surface
        road_rect = pygame.Rect(
            config.ROAD_LEFT, 0, config.ROAD_WIDTH, config.SCREEN_HEIGHT
        )
        pygame.draw.rect(surface, config.COLOR_ROAD, road_rect)

        # Road boundaries (solid edge lines)
        pygame.draw.rect(
            surface,
            config.COLOR_ROAD_BOUNDARY,
            (config.ROAD_LEFT - config.ROAD_BOUNDARY_WIDTH, 0,
             config.ROAD_BOUNDARY_WIDTH, config.SCREEN_HEIGHT),
        )
        pygame.draw.rect(
            surface,
            config.COLOR_ROAD_BOUNDARY,
            (config.ROAD_RIGHT, 0, config.ROAD_BOUNDARY_WIDTH, config.SCREEN_HEIGHT),
        )

        # Lane markings between lanes (dashed, scrolling downward to fake
        # forward motion of the player's vehicle).
        for lane_index in range(1, config.NUM_LANES):
            x = config.ROAD_LEFT + lane_index * config.LANE_WIDTH
            y = -self.dash_period + self.scroll_offset
            while y < config.SCREEN_HEIGHT:
                dash_rect = pygame.Rect(
                    int(x - config.DASH_WIDTH / 2), int(y),
                    config.DASH_WIDTH, config.DASH_LENGTH,
                )
                pygame.draw.rect(surface, config.COLOR_LANE_MARKING, dash_rect)
                y += self.dash_period
