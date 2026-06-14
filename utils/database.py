"""Database helpers for advanced emergency traffic detections."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path
from typing import Optional


DEFAULT_DB_PATH = Path("database/traffic.db")


def create_database(db_path: Path | str = DEFAULT_DB_PATH) -> None:
    """Create SQLite database and logs table if not present."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(path) as conn:
        with closing(conn.cursor()) as cursor:
            # We recreate the table for the new schema
            cursor.execute("DROP TABLE IF EXISTS logs")
            cursor.execute(
                """
                CREATE TABLE logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    camera_id TEXT NOT NULL,
                    vehicle_type TEXT,
                    confidence REAL,
                    action_taken TEXT NOT NULL,
                    junction_activated TEXT,
                    obstruction_severity TEXT
                )
                """
            )
        conn.commit()


def log_detection(
    event_type: str,
    camera_id: str,
    action_taken: str,
    vehicle_type: str = "",
    confidence: float = 0.0,
    junction_activated: str | None = None,
    obstruction_severity: str = "NONE",
    db_path: Path | str = DEFAULT_DB_PATH,
    event_time: Optional[datetime] = None,
) -> None:
    """Insert one advanced detection event into the logs table."""
    path = Path(db_path)
    timestamp = (event_time or datetime.now()).strftime("%Y-%m-%d %H:%M:%S")

    with sqlite3.connect(path) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute(
                """
                INSERT INTO logs (timestamp, event_type, camera_id, vehicle_type, confidence, action_taken, junction_activated, obstruction_severity)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (timestamp, event_type, camera_id, vehicle_type, float(confidence), action_taken, junction_activated, obstruction_severity),
            )
        conn.commit()


def get_recent_logs(limit: int = 50, db_path: Path | str = DEFAULT_DB_PATH) -> list[dict]:
    """Fetch the most recent detection logs."""
    path = Path(db_path)
    if not path.exists():
        return []

    with sqlite3.connect(path) as conn:
        conn.row_factory = sqlite3.Row
        with closing(conn.cursor()) as cursor:
            cursor.execute(
                """
                SELECT timestamp, event_type, camera_id, vehicle_type, confidence, action_taken, junction_activated, obstruction_severity
                FROM logs
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]


def get_analytics_summary(db_path: Path | str = DEFAULT_DB_PATH) -> dict:
    """Fetch analytics summary from the database."""
    path = Path(db_path)
    if not path.exists():
        return {
            "total_emergencies": 0,
            "total_obstructions": 0,
            "vehicle_counts": {"ambulance": 0, "police_car": 0, "fire_truck": 0},
            "action_counts": {}
        }

    with sqlite3.connect(path) as conn:
        conn.row_factory = sqlite3.Row
        with closing(conn.cursor()) as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM logs WHERE event_type = 'EMERGENCY_DETECTED'")
            total = cursor.fetchone()["count"]
            
            cursor.execute("SELECT COUNT(*) as count FROM logs WHERE event_type = 'OBSTRUCTION'")
            obs_total = cursor.fetchone()["count"]

            cursor.execute("SELECT vehicle_type, COUNT(*) as count FROM logs WHERE vehicle_type != '' GROUP BY vehicle_type")
            type_counts = {row["vehicle_type"]: row["count"] for row in cursor.fetchall()}

            cursor.execute("SELECT action_taken, COUNT(*) as count FROM logs GROUP BY action_taken")
            action_counts = {row["action_taken"]: row["count"] for row in cursor.fetchall()}

            return {
                "total_emergencies": total,
                "total_obstructions": obs_total,
                "vehicle_counts": {
                    "ambulance": type_counts.get("ambulance", 0),
                    "police_car": type_counts.get("police_car", 0),
                    "fire_truck": type_counts.get("fire_truck", 0)
                },
                "action_counts": action_counts
            }


