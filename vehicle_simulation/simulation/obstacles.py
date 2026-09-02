"""
simulation/obstacles.py

Defines the Obstacle class: another vehicle driving ahead of the player.
The obstacle keeps track of its distance from the player (in meters) and
its own speed. The distance changes based on the RELATIVE speed between
the player and the obstacle, which is what makes the scenario feel like
real driving (closing the gap when we're faster, falling back when we're
slower).

A manual "braking event" can be triggered (see main.py, the 'O' key) purely
for demonstration purposes, so the emergency-braking scenario can be shown
on demand instead of waiting for it to happen by chance.
"""

import random

import pygame

import config


class Obstacle:
    """Represents the vehicle ahead of the player."""

    def __init__(self):
        self.distance = config.INITIAL_OBSTACLE_DISTANCE
        self.speed = config.OBSTACLE_BASE_SPEED

        self._event_active = False
        self._event_timer = 0.0

        # Screen position is derived each frame from distance; x is fixed
        # to the same lane as the player for simplicity.
        self.x = config.SCREEN_WIDTH / 2
        self.y = 0.0

        self.width = config.OBSTACLE_VEHICLE_WIDTH
        self.height = config.OBSTACLE_VEHICLE_HEIGHT

    def reset(self):
        self.distance = config.INITIAL_OBSTACLE_DISTANCE
        self.speed = config.OBSTACLE_BASE_SPEED
        self._event_active = False
        self._event_timer = 0.0

    def trigger_braking_event(self):
        """Force the obstacle to suddenly slow down, closing the gap fast.

        This exists purely so the emergency-braking scenario (Scenario 4
        in the project spec) can be reliably demonstrated on demand.
        """
        self._event_active = True
        self._event_timer = config.OBSTACLE_EVENT_DURATION

    def update(self, dt: float, player_speed_kmh: float):
        # Determine the obstacle's current speed.
        if self._event_active:
            self.speed = config.OBSTACLE_BASE_SPEED * config.OBSTACLE_EVENT_SPEED_FACTOR
            self._event_timer -= dt
            if self._event_timer <= 0:
                self._event_active = False
        else:
            self.speed = config.OBSTACLE_BASE_SPEED

        # Relative speed determines how the gap changes.
        # If the obstacle is faster than the player, the gap grows.
        # If the obstacle is slower than the player, the gap shrinks.
        relative_speed_kmh = self.speed - player_speed_kmh
        relative_speed_m_per_s = relative_speed_kmh * (1000.0 / 3600.0)

        self.distance += relative_speed_m_per_s * dt

        # If the obstacle has drifted far ahead, bring a "new" obstacle
        # vehicle back into range so the demonstration keeps going.
        if self.distance > config.MAX_OBSTACLE_DISTANCE:
            self.distance = config.RESPAWN_DISTANCE

        # Never let the obstacle visually overlap/pass through the player.
        self.distance = max(config.MIN_OBSTACLE_DISTANCE, self.distance)

    def get_screen_y(self) -> float:
        """
        Map the obstacle's distance (meters) to a vertical screen position.

        Closer distance -> obstacle appears lower on screen (nearer the
        player). Farther distance -> obstacle appears higher up (further
        away), eventually leaving the top of the screen.
        """
        pixels_ahead = self.distance * config.PIXELS_PER_METER
        y = config.PLAYER_SCREEN_Y - pixels_ahead
        return y

    def draw(self, surface: pygame.Surface):
        self.y = self.get_screen_y()

        # Don't draw if it has scrolled off the top of the screen.
        if self.y < -self.height:
            return

        rect = pygame.Rect(0, 0, self.width, self.height)
        rect.center = (int(self.x), int(self.y))

        pygame.draw.rect(surface, config.COLOR_OBSTACLE_VEHICLE, rect, border_radius=8)
        pygame.draw.rect(surface, (10, 10, 10), rect, width=2, border_radius=8)

        # Rear window (facing the player, i.e. towards the bottom of screen)
        rear_window = pygame.Rect(0, 0, self.width - 14, 16)
        rear_window.center = (int(self.x), int(self.y + self.height / 2 - 16))
        pygame.draw.rect(surface, (60, 60, 65), rear_window, border_radius=4)

        # Taillights
        light_y = rect.bottom - 4
        pygame.draw.circle(surface, (255, 60, 60), (rect.left + 8, light_y), 3)
        pygame.draw.circle(surface, (255, 60, 60), (rect.right - 8, light_y), 3)
