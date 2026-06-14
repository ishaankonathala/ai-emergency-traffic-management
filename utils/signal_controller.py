"""Signal state machine with density and emergency overrides."""

from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class SignalStatus:
    state: str
    time_left: int
    mode: str


class SignalController:
    """Controls RED/YELLOW/GREEN cycle with emergency prioritization."""

    def __init__(self, yellow_time: int = 4, red_time: int = 8):
        self.yellow_time = yellow_time
        self.red_time = red_time
        self.state = "RED"
        self.mode = "NORMAL"
        self.time_left = red_time
        self._last_tick = time.time()

    def _set_state(self, state: str, duration: int, mode: str = "NORMAL") -> None:
        self.state = state
        self.time_left = max(0, int(duration))
        self.mode = mode
        self._last_tick = time.time()

    def force_emergency_green(self, duration: int = 20) -> None:
        self._set_state("GREEN", duration, mode="EMERGENCY")

    def update(self, target_green_time: int, emergency_active: bool) -> SignalStatus:
        now = time.time()
        elapsed = now - self._last_tick
        if elapsed >= 1.0:
            dec = int(elapsed)
            self.time_left = max(0, self.time_left - dec)
            self._last_tick = now

        if emergency_active and self.mode != "EMERGENCY":
            self.force_emergency_green(duration=max(20, target_green_time))

        if self.time_left == 0:
            if self.mode == "EMERGENCY":
                self._set_state("YELLOW", self.yellow_time, mode="NORMAL")
            elif self.state == "GREEN":
                self._set_state("YELLOW", self.yellow_time)
            elif self.state == "YELLOW":
                self._set_state("RED", self.red_time)
            else:
                self._set_state("GREEN", target_green_time)

        return SignalStatus(state=self.state, time_left=self.time_left, mode=self.mode)
