"""
interface.py

Formal input/output contract for this module (Vehicle Simulation) when
embedded in the larger 6-module system.

Other modules should depend ONLY on what is described here — not on
Simulation's internals (self.player, self.obstacle, etc.), which may
change without notice.

-------------------------------------------------------------------------
INPUT  (one call per frame, or whenever a new reading is available)
-------------------------------------------------------------------------
    Simulation.set_driver_state(state: str)
        state must be config.STATE_AWAKE or config.STATE_DROWSY.
        Raises ValueError on anything else, so a malformed upstream
        reading fails loudly instead of silently doing nothing.

        Typical caller: the drowsiness-detection module.
            sim.set_driver_state(drowsiness_detector.get_state())

-------------------------------------------------------------------------
OUTPUT (read any time after Simulation.update(dt) has been called)
-------------------------------------------------------------------------
    Simulation.get_output_state() -> SimulationOutput
        A plain, JSON-serializable snapshot. No pygame types included,
        so it's safe to log, pass over a queue/socket, or hand to a
        separate dashboard/hardware-bridge module.

-------------------------------------------------------------------------
Threading note
-------------------------------------------------------------------------
Simulation is not thread-safe. If the driver-state source lives on its
own thread (e.g. a camera-reading loop), have it write to a small
thread-safe buffer (e.g. queue.Queue(maxsize=1)) and have the main loop
drain that buffer once per frame before calling set_driver_state() —
don't call set_driver_state() directly from another thread.
"""

from dataclasses import dataclass


@dataclass
class SimulationOutput:
    """Snapshot of everything a downstream module might need."""
    driver_state: str          # AWAKE / DROWSY (echoed back for convenience)
    current_speed: float       # km/h
    target_speed: float        # km/h
    obstacle_distance: float   # meters
    controller_state: str      # NORMAL_DRIVING / DROWSINESS_SLOWDOWN / EMERGENCY_BRAKING
    control_output: str        # NORMAL / SLOW_DOWN / EMERGENCY_BRAKE
    brake_status: str          # OFF / ACTIVE / EMERGENCY
    warning: bool
    status_text: str
