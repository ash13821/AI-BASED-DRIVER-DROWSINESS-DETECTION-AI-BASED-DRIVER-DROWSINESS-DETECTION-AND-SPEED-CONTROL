"""
simulation/vehicle.py

Defines the Vehicle class used for the player's car. Handles speed,
gradual acceleration/deceleration towards a target speed, and rendering.

This module knows NOTHING about drowsiness, AI, or control decisions.
It only knows how to move a vehicle's speed towards whatever target speed
and rate it is given each frame. All "why" decisions belong to
control/vehicle_controller.py.
"""

import pygame

import config


class Vehicle:
    """Represents the player's vehicle in the simulation."""

    def __init__(self, x: float, y: float, color=config.COLOR_PLAYER_VEHICLE):
        self.x = x
        self.y = y
        self.color = color

        self.width = config.PLAYER_VEHICLE_WIDTH
        self.height = config.PLAYER_VEHICLE_HEIGHT

        # Speed is tracked in km/h.
        self.current_speed = config.NORMAL_SPEED
        self.target_speed = config.NORMAL_SPEED

    def reset(self):
        """Reset the vehicle to its initial state (used on R press)."""
        self.current_speed = config.NORMAL_SPEED
        self.target_speed = config.NORMAL_SPEED

    def update(self, dt: float, target_speed: float, rate: float):
        """
        Move current_speed gradually towards target_speed.

        Args:
            dt: elapsed time in seconds since the last frame.
            target_speed: the speed (km/h) the controller wants us to reach.
            rate: how fast we may change speed, in km/h per second. This
                  value differs depending on whether we are accelerating
                  back to normal, gradually slowing due to drowsiness, or
                  emergency braking.
        """
        self.target_speed = target_speed

        if self.current_speed < target_speed:
            self.current_speed = min(target_speed, self.current_speed + rate * dt)
        elif self.current_speed > target_speed:
            self.current_speed = max(target_speed, self.current_speed - rate * dt)

        # Clamp to sane bounds.
        self.current_speed = max(config.MIN_SPEED, min(config.MAX_SPEED, self.current_speed))

    def draw(self, surface: pygame.Surface):
        """Draw the vehicle as a simple car shape, centered on self.x, self.y."""
        rect = pygame.Rect(0, 0, self.width, self.height)
        rect.center = (int(self.x), int(self.y))

        # Body
        pygame.draw.rect(surface, self.color, rect, border_radius=8)
        pygame.draw.rect(surface, (10, 10, 10), rect, width=2, border_radius=8)

        # Windshield (front, top of the car since car faces "up" the screen)
        windshield = pygame.Rect(0, 0, self.width - 14, 18)
        windshield.center = (int(self.x), int(self.y - self.height / 2 + 20))
        pygame.draw.rect(surface, (170, 210, 235), windshield, border_radius=4)

        # Rear window
        rear_window = pygame.Rect(0, 0, self.width - 14, 14)
        rear_window.center = (int(self.x), int(self.y + self.height / 2 - 16))
        pygame.draw.rect(surface, (170, 210, 235), rear_window, border_radius=4)

        # Headlights
        light_y = rect.top + 4
        pygame.draw.circle(surface, (255, 240, 180), (rect.left + 8, light_y), 3)
        pygame.draw.circle(surface, (255, 240, 180), (rect.right - 8, light_y), 3)
