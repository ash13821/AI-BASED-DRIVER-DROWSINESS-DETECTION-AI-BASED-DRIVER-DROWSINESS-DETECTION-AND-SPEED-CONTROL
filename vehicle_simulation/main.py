"""
main.py

Entry point for the AI Vehicle Safety Simulation.

Architecture
------------

    Driver-state source            Vehicle Controller           Simulation
   (keyboard today, AI later)  -->  (control/vehicle_          -->  (Pygame
                                      controller.py)                 rendering
                                                                      + physics)

Every frame:
    1. Read the driver_state.
       -> TODAY: from keyboard_input() (A/D keys) below.
       -> FUTURE: replace with `drowsiness_detector.get_state()`.
          See the "FUTURE AI INTEGRATION" note near get_driver_state().
    2. Feed driver_state + current_speed + obstacle_distance into
       VehicleController.update() to get a ControlDecision.
    3. Apply that ControlDecision to the Vehicle (speed/physics) and to
       the Dashboard (what to display).
    4. Render everything.

This file intentionally contains almost no "decision" logic itself - that
all lives in control/vehicle_controller.py so it can be reused, tested, or
eventually reused when talking to real hardware (see README section on
Arduino integration).
"""

import sys

import pygame

import config
from simulation.vehicle import Vehicle
from simulation.road import Road
from simulation.obstacles import Obstacle
from control.vehicle_controller import VehicleController
from ui.dashboard import Dashboard
from interface import SimulationOutput


class Simulation:
    """Owns all simulation objects and runs the main loop."""

    def __init__(self):
        pygame.init()
        pygame.display.set_caption(config.WINDOW_TITLE)
        self.screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()

        self.road = Road()
        self.player = Vehicle(
            x=config.SCREEN_WIDTH / 2,
            y=config.PLAYER_SCREEN_Y,
        )
        self.obstacle = Obstacle()
        self.controller = VehicleController()
        self.dashboard = Dashboard()

        # --------------------------------------------------------------
        # FUTURE AI INTEGRATION POINT
        # --------------------------------------------------------------
        # `self.driver_state` is the ONLY thing the rest of the simulation
        # cares about. It is a plain string: config.STATE_AWAKE or
        # config.STATE_DROWSY.
        #
        # Right now it is set by keyboard_input() below, using the A/D
        # keys as a stand-in for a real driver.
        #
        # Later, replace the keyboard_input() call site with:
        #
        #     sim.set_driver_state(drowsiness_detector.get_state())
        #
        # called once per frame from whatever module owns the frame loop.
        # No other file needs to change: VehicleController, Vehicle,
        # Obstacle, Road, and Dashboard only ever see the resulting
        # AWAKE / DROWSY string, never how it was obtained.
        #
        # See interface.py for the full input/output contract.
        # --------------------------------------------------------------
        self.driver_state = config.STATE_AWAKE

        self.running = True

    def reset(self):
        """Handle the R key: return everything to its initial state."""
        self.driver_state = config.STATE_AWAKE
        self.player.reset()
        self.obstacle.reset()
        self.road.reset()
        self.controller.reset()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False

                elif event.key == pygame.K_a:
                    self.keyboard_input(config.STATE_AWAKE)

                elif event.key == pygame.K_d:
                    self.keyboard_input(config.STATE_DROWSY)

                elif event.key == pygame.K_r:
                    self.reset()

                elif event.key == pygame.K_o:
                    # Demo-only: force the obstacle ahead to brake suddenly
                    # so the emergency-braking scenario can be shown live.
                    self.obstacle.trigger_braking_event()

    def keyboard_input(self, new_state: str):
        """
        Placeholder driver-state source.

        TODAY: called directly from key presses (A -> AWAKE, D -> DROWSY).

        FUTURE: this whole method can be deleted. The drowsiness-detection
        module should call set_driver_state() directly instead.
        """
        self.set_driver_state(new_state)

    def set_driver_state(self, state: str):
        """
        PUBLIC INTEGRATION POINT (input).

        The single entry point external modules should use to report the
        current driver state. See interface.py for the full contract.

        Raises:
            ValueError: if `state` isn't config.STATE_AWAKE or
                config.STATE_DROWSY, so a bad upstream reading fails
                loudly instead of being silently ignored.
        """
        if state not in (config.STATE_AWAKE, config.STATE_DROWSY):
            raise ValueError(
                f"Unknown driver_state {state!r}; expected "
                f"{config.STATE_AWAKE!r} or {config.STATE_DROWSY!r}"
            )
        self.driver_state = state

    def get_output_state(self) -> SimulationOutput:
        """
        PUBLIC INTEGRATION POINT (output).

        Returns a plain, pygame-free snapshot of the simulation's current
        state for any downstream module (logging/analytics, an alternate
        dashboard, a hardware bridge) that needs data without reaching
        into Simulation's internals. Call after update() for fresh values.
        """
        decision = self._last_decision
        return SimulationOutput(
            driver_state=self.driver_state,
            current_speed=self.player.current_speed,
            target_speed=decision.target_speed,
            obstacle_distance=self.obstacle.distance,
            controller_state=decision.controller_state,
            control_output=decision.control_output,
            brake_status=decision.brake_status,
            warning=decision.warning,
            status_text=decision.status_text,
        )

    def update(self, dt: float):
        # 1. Ask the controller what to do, given the current situation.
        decision = self.controller.update(
            driver_state=self.driver_state,
            current_speed=self.player.current_speed,
            obstacle_distance=self.obstacle.distance,
        )

        # 2. Apply the decision to the simulated vehicle.
        self.player.update(dt, target_speed=decision.target_speed, rate=decision.rate)

        # 3. Update the world around the vehicle.
        self.obstacle.update(dt, player_speed_kmh=self.player.current_speed)
        self.road.update(dt, current_speed_kmh=self.player.current_speed)
        self.dashboard.update(dt)

        # Store the latest decision so draw() can display it.
        self._last_decision = decision

    def draw(self):
        self.road.draw(self.screen)
        self.obstacle.draw(self.screen)
        self.player.draw(self.screen)

        decision = self._last_decision
        self.dashboard.draw(
            self.screen,
            driver_state=self.driver_state,
            current_speed=self.player.current_speed,
            target_speed=decision.target_speed,
            brake_status=decision.brake_status,
            obstacle_distance=self.obstacle.distance,
            status_text=decision.status_text,
            warning=decision.warning,
        )

        pygame.display.flip()

    def run(self):
        # Prime the first decision so draw() has something to show even
        # before the first update() call completes.
        self._last_decision = self.controller.update(
            driver_state=self.driver_state,
            current_speed=self.player.current_speed,
            obstacle_distance=self.obstacle.distance,
        )

        while self.running:
            dt = self.clock.tick(config.FPS) / 1000.0  # seconds since last frame
            self.handle_events()
            self.update(dt)
            self.draw()

        pygame.quit()
        sys.exit()


def main():
    sim = Simulation()
    sim.run()


if __name__ == "__main__":
    main()
