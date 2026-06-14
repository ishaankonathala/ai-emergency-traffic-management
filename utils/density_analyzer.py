"""Traffic density and lane-wise counting utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np


TRAFFIC_CLASSES = {"car", "bus", "motorcycle", "truck"}


@dataclass
class DensityStats:
    counts: Dict[str, int]
    total_vehicles: int
    density_level: str
    lane_counts: Dict[str, int]


class DensityAnalyzer:
    """Analyzes total and lane-wise traffic density from detections."""

    def __init__(self, frame_width: int, low_threshold: int = 10, high_threshold: int = 25):
        self.frame_width = frame_width
        self.low_threshold = low_threshold
        self.high_threshold = high_threshold

    def _lane_from_x(self, x_center: float) -> str:
        lane_width = self.frame_width / 3
        if x_center < lane_width:
            return "Lane 1"
        if x_center < 2 * lane_width:
            return "Lane 2"
        return "Lane 3"

    def analyze(self, detections: List[dict]) -> DensityStats:
        counts = {"car": 0, "bus": 0, "motorcycle": 0, "truck": 0}
        lane_counts = {"Lane 1": 0, "Lane 2": 0, "Lane 3": 0}

        for det in detections:
            label = det["label"]
            if label not in TRAFFIC_CLASSES:
                continue

            counts[label] += 1
            x1, _, x2, _ = det["bbox"]
            lane = self._lane_from_x((x1 + x2) / 2.0)
            lane_counts[lane] += 1

        total = int(np.sum(list(counts.values())))
        if total <= self.low_threshold:
            density = "LOW"
        elif total <= self.high_threshold:
            density = "MEDIUM"
        else:
            density = "HIGH"

        return DensityStats(
            counts=counts,
            total_vehicles=total,
            density_level=density,
            lane_counts=lane_counts,
        )

    @staticmethod
    def green_time_for_density(density_level: str) -> int:
        mapping = {"LOW": 15, "MEDIUM": 30, "HIGH": 45}
        return mapping.get(density_level, 15)
