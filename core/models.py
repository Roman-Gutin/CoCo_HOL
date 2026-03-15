"""Data models for the second brain system."""

from pydantic import BaseModel
from datetime import datetime, time, date
from enum import Enum
from typing import Optional


class BlockCategory(str, Enum):
    FITNESS = "fitness"
    COMMUTE = "commute"
    FOOD_PREP = "food_prep"
    EATING = "eating"
    CHORE = "chore"
    RG_REVIEW = "rg_review"
    SOCIAL = "social"
    WORK = "work"
    CARDIO = "cardio"
    GROCERY = "grocery"


class TimeBlockRequest(BaseModel):
    """A request from a module to block time on the calendar."""
    category: BlockCategory
    title: str
    duration_minutes: int
    earliest: time
    latest: time
    priority: int  # 1=highest
    flexible: bool = True
    group_id: Optional[str] = None  # linked blocks share a group_id
    group_order: int = 0  # ordering within a group
    description: str = ""
    color_id: Optional[str] = None  # Google Calendar color


class TimeBlock(BaseModel):
    """A placed time block on the calendar."""
    id: str
    request: TimeBlockRequest
    date: date
    start: datetime
    end: datetime
    gcal_event_id: Optional[str] = None


class DailyPnL(BaseModel):
    """Trading PnL summary for a day."""
    date: str
    total_pnl: float = 0.0
    by_desk: dict[str, float] = {}
    open_positions: int = 0
    trades_executed: int = 0
    notes: str = ""


class Meal(BaseModel):
    """A planned meal."""
    name: str
    meal_type: str  # breakfast, lunch, dinner
    prep_minutes: int
    cook_minutes: int
    servings: int
    ingredients: dict[str, str] = {}


class WeeklyMealPlan(BaseModel):
    """A week's worth of meals."""
    week_start: date
    days: dict[str, dict[str, str]] = {}  # day -> {breakfast: meal_name, lunch: ..., dinner: ...}


class Workout(BaseModel):
    """A planned workout session."""
    name: str
    exercises: list[str] = []
    day: str = ""


class JournalEntry(BaseModel):
    """Daily journal entry."""
    date: str
    schedule_adherence: float = 0.0
    pnl: Optional[DailyPnL] = None
    workouts_completed: list[str] = []
    meals_cooked: list[str] = []
    chores_done: list[str] = []
    accomplishments: list[str] = []
    reflections: str = ""
    tomorrow_priorities: list[str] = []
