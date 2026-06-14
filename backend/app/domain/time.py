"""Deterministic simulation clock derived from tick resolution."""

from dataclasses import dataclass
from enum import StrEnum


class TimeOfDayLabel(StrEnum):
    NIGHT = "night"
    MORNING_COMMUTE = "morning_commute"
    WORK_SCHOOL = "work_school"
    LUNCH = "lunch"
    AFTERNOON = "afternoon"
    EVENING_COMMUTE = "evening_commute"
    NIGHT_SOCIAL = "night_social"


@dataclass(frozen=True, slots=True)
class SimulationTime:
    """Calendar projection for a zero-based simulation tick."""

    tick: int
    tick_minutes: int
    day: int
    hour: int
    minute: int
    time_of_day_label: TimeOfDayLabel

    @classmethod
    def from_tick(cls, tick: int, tick_minutes: int) -> "SimulationTime":
        if tick < 0:
            raise ValueError("tick must be non-negative")
        if tick_minutes <= 0:
            raise ValueError("tick_minutes must be positive")
        elapsed_minutes = tick * tick_minutes
        day, minute_of_day = divmod(elapsed_minutes, 1440)
        hour, minute = divmod(minute_of_day, 60)
        return cls(
            tick=tick,
            tick_minutes=tick_minutes,
            day=day,
            hour=hour,
            minute=minute,
            time_of_day_label=cls._label_for_hour(hour),
        )

    @staticmethod
    def _label_for_hour(hour: int) -> TimeOfDayLabel:
        if 6 <= hour < 8:
            return TimeOfDayLabel.MORNING_COMMUTE
        if 8 <= hour < 12:
            return TimeOfDayLabel.WORK_SCHOOL
        if 12 <= hour < 14:
            return TimeOfDayLabel.LUNCH
        if 14 <= hour < 17:
            return TimeOfDayLabel.AFTERNOON
        if 17 <= hour < 19:
            return TimeOfDayLabel.EVENING_COMMUTE
        if 19 <= hour < 22:
            return TimeOfDayLabel.NIGHT_SOCIAL
        return TimeOfDayLabel.NIGHT
