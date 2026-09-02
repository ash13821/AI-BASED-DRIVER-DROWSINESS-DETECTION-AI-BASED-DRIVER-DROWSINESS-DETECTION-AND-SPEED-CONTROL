"""
control/vehicle_controller.py

This is the "brain" of the safety system. It receives:

    - driver_state       (AWAKE / DROWSY)   -- currently from keyboard,
                                                later from the AI drowsiness
                                                detector
    - current_speed       (km/h)
    - obstacle_distance    (meters)

...and decides what the vehicle should do. It does NOT touch pygame,
rendering, or physics directly - it only produces a ControlDecision that
describes the desired behaviour. That decision can be applied to the
Pygame simulation (as done in main.py) OR, in the future, sent to an
Arduino-based hardware prototype, without changing this file at all.

    Driver / Obstacle input
              |
              v
      VehicleController.update()
              |
              v
        ControlDecision
              |
        -------------
        |           |
        v           v
   Simulation     Arduino (future)
"""

from dataclasses import dataclass

import config


@dataclass
class ControlDecision:
    """The output produced by the controller each update.

    This is the single object that a downstream consumer (the Pygame
    simulation today, real vehicle hardware in the future) needs in order
    to act. It intentionally contains no Pygame-specific or simulation-
    specific types.
    """
    controller_state: str      # NORMAL_DRIVING / DROWSINESS_SLOWDOWN / EMERGENCY_BRAKING
    control_output: str        # NORMAL / SLOW_DOWN / EMERGENCY_BRAKE
    target_speed: float        # km/h
    rate: float                # km/h per second, how aggressively to reach target_speed
    brake_status: str          # OFF / ACTIVE / EMERGENCY
    warning: bool              # whether a warning should be shown to the driver
    status_text: str           # human-readable status for the dashboard


class VehicleController:
    """
    Decides vehicle behaviour from driver state and obstacle distance.

    Usage:
        controller = VehicleController()
        decision = controller.update(driver_state, current_speed, obstacle_distance)
    """

    def __init__(self):
        self.controller_state = config.NORMAL_DRIVING

    def reset(self):
        self.controller_state = config.NORMAL_DRIVING

    def update(self, driver_state: str, current_speed: float,
               obstacle_distance: float) -> ControlDecision:
        """
        Core decision logic.

        Safety priority order (highest first):
            1. Emergency braking - triggered any time the obstacle distance
               drops below EMERGENCY_DISTANCE, REGARDLESS of driver state.
               Collision avoidance always wins.
            2. Drowsiness slowdown - triggered whenever the driver is DROWSY
               and no emergency is in progress.
            3. Normal driving - driver is AWAKE and no obstacle danger.
        """

        # --- 1. Emergency braking always takes priority -------------------
        if obstacle_distance < config.EMERGENCY_DISTANCE:
            self.controller_state = config.EMERGENCY_BRAKING
            return ControlDecision(
                controller_state=config.EMERGENCY_BRAKING,
                control_output=config.CONTROL_EMERGENCY_BRAKE,
                target_speed=config.MIN_SPEED,
                rate=config.EMERGENCY_DECELERATION,
                brake_status=config.BRAKE_EMERGENCY,
                warning=True,
                status_text="EMERGENCY BRAKING",
            )

        # --- 2. Drowsiness slowdown ----------------------------------------
        if driver_state == config.STATE_DROWSY:
            self.controller_state = config.DROWSINESS_SLOWDOWN
            # While decelerating we're still above the safe speed; once we
            # reach it, keep holding it steady.
            reached_safe_speed = current_speed <= config.SAFE_SPEED + 0.5
            status_text = (
                "DROWSINESS DETECTED\nHOLDING SAFE SPEED"
                if reached_safe_speed
                else "DROWSINESS DETECTED\nSLOWING VEHICLE"
            )
            return ControlDecision(
                controller_state=config.DROWSINESS_SLOWDOWN,
                control_output=config.CONTROL_SLOW_DOWN,
                target_speed=config.SAFE_SPEED,
                rate=config.DECELERATION,
                brake_status=config.BRAKE_ACTIVE,
                warning=True,
                status_text=status_text,
            )

        # --- 3. Normal driving ----------------------------------------------
        self.controller_state = config.NORMAL_DRIVING
        return ControlDecision(
            controller_state=config.NORMAL_DRIVING,
            control_output=config.CONTROL_NORMAL,
            target_speed=config.NORMAL_SPEED,
            rate=config.ACCELERATION,
            brake_status=config.BRAKE_OFF,
            warning=False,
            status_text="NORMAL DRIVING",
        )
