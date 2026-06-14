"""Realistic multi-junction emergency green-corridor simulation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class CorridorSnapshot:
    corridor_active: bool
    junction_states: Dict[str, str]
    junction_timers: Dict[str, int]
    current_junction: Optional[str]
    next_junction: Optional[str]
    route_note: str
    eta_seconds: int
    marker_progress: float
    emergency_vehicle_type: Optional[str]


class EmergencyRouteManager:
    """Synchronizes a four-junction corridor for emergency movement."""

    def __init__(self, green_seconds: int = 15, yellow_seconds: int = 3):
        self.junctions: List[str] = ["Junction A", "Junction B", "Junction C", "Junction D"]
        self.green_seconds = green_seconds
        self.yellow_seconds = yellow_seconds
        self.reset_corridor()

    def activate_corridor(self, start_junction_index: int = 0, vehicle_type: str = "ambulance") -> CorridorSnapshot:
        safe_index = max(0, min(start_junction_index, len(self.junctions) - 1))
        self.corridor_active = True
        self.current_idx = safe_index
        self.current_phase = "GREEN"
        self.phase_timer = self.green_seconds
        self.marker_progress = 0.0
        self.emergency_vehicle_type = vehicle_type
        return self._build_snapshot("GREEN_CORRIDOR_ACTIVE")

    def update_corridor(self, dt_seconds: int = 1) -> CorridorSnapshot:
        if not self.corridor_active:
            return self._build_snapshot("Normal traffic operation")

        self.phase_timer = max(0, self.phase_timer - dt_seconds)
        phase_duration = self.green_seconds if self.current_phase == "GREEN" else self.yellow_seconds
        self.marker_progress = min(1.0, (phase_duration - self.phase_timer) / max(phase_duration, 1))

        if self.phase_timer == 0:
            if self.current_phase == "GREEN":
                self.current_phase = "YELLOW"
                self.phase_timer = self.yellow_seconds
                self.marker_progress = 0.0
            else:
                self.advance_junction()

        return self._build_snapshot("GREEN_CORRIDOR_ACTIVE")

    def advance_junction(self) -> CorridorSnapshot:
        if not self.corridor_active:
            return self._build_snapshot("Normal traffic operation")

        self.current_idx += 1
        self.current_phase = "GREEN"
        self.phase_timer = self.green_seconds
        self.marker_progress = 0.0

        if self.current_idx >= len(self.junctions):
            return self.reset_corridor("Emergency route cleared, normal cycle restored")
        return self._build_snapshot("GREEN_CORRIDOR_ACTIVE")

    def reset_corridor(self, note: str = "Normal traffic operation") -> CorridorSnapshot:
        self.corridor_active = False
        self.current_idx: Optional[int] = None
        self.current_phase = "RED"
        self.phase_timer = 0
        self.marker_progress = 0.0
        self.emergency_vehicle_type: Optional[str] = None
        return self._build_snapshot(note)

    def _build_snapshot(self, note: str) -> CorridorSnapshot:
        states = {j: "RED" for j in self.junctions}
        timers = {j: 0 for j in self.junctions}
        current_junction = None
        next_junction = None
        eta_seconds = 0

        if self.corridor_active and self.current_idx is not None and self.current_idx < len(self.junctions):
            current_junction = self.junctions[self.current_idx]
            states[current_junction] = self.current_phase
            timers[current_junction] = self.phase_timer

            if self.current_idx + 1 < len(self.junctions):
                next_junction = self.junctions[self.current_idx + 1]
                states[next_junction] = "PREPARE GREEN"

            remaining_junctions = len(self.junctions) - self.current_idx - 1
            eta_seconds = self.phase_timer + (remaining_junctions * (self.green_seconds + self.yellow_seconds))
        else:
            states = {j: "NORMAL" for j in self.junctions}

        return CorridorSnapshot(
            corridor_active=self.corridor_active,
            junction_states=states,
            junction_timers=timers,
            current_junction=current_junction,
            next_junction=next_junction,
            route_note=note,
            eta_seconds=eta_seconds,
            marker_progress=self.marker_progress,
            emergency_vehicle_type=self.emergency_vehicle_type,
        )
