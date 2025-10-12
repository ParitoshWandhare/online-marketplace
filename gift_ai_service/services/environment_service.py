"""
environment_service.py

Provides a small EnvironmentService used by the Gift AI pipeline.
- returns mock environment/context data (time, weather, festival hints)
- optional: logs context snapshots to MongoDB if MONGO_URI present in env
"""

from datetime import datetime
import random
import os
from typing import Dict, Any, Optional

try:
    from pymongo import MongoClient
except Exception:
    MongoClient = None  # optional dependency; service still works without it

ENV_COLLECTION = os.getenv("ENV_COLLECTION", "environment_context")
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB", "gift_ai_service")


class EnvironmentService:
    """
    Generates environment/context information used to personalize gift bundles.

    - get_environment_context() returns a dict with timestamp, location, weather,
      temperature, festival hints, and simple user-activity hint.
    - If MONGO_URI is set and pymongo is installed, the service can persist
      context snapshots to Mongo (method: persist_context()).
    """

    def __init__(self, enable_persistence: bool = True):
        self.sources = ["weather_api", "calendar_service", "user_activity_logs"]
        self.enable_persistence = enable_persistence and MONGO_URI and MongoClient is not None
        self._mongo_client = None
        if self.enable_persistence:
            try:
                self._mongo_client = MongoClient(MONGO_URI)
                self._db = self._mongo_client[MONGO_DB]
                # ensure collection exists (no-op if exists)
                self._db[ENV_COLLECTION].create_index("timestamp")
            except Exception:
                # disable persistence if mongo connection fails
                self.enable_persistence = False
                self._mongo_client = None

    def get_environment_context(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns environment context. This is currently mocked, but the shape is stable.

        Args:
            user_id (str, optional): If provided, context may contain user-specific hints.

        Returns:
            dict: {
                "timestamp": str(ISO),
                "location": "City, Country",
                "weather": "Sunny" | "Rainy" | ...,
                "temperature_celsius": float,
                "festival_nearby": "Diwali" | "Holi" | "None",
                "time_of_day": "Morning"|"Afternoon"|"Evening"|"Night",
                "user_activity_hint": "bought_home_decor" | "browsing_tech" | None
            }
        """
        now = datetime.utcnow()
        hour = now.hour

        # mock values (replace with real API calls later)
        location = os.getenv("DEFAULT_LOCATION", "Pune, India")
        weather = random.choice(["Sunny", "Cloudy", "Rainy", "Clear", "Mist"])
        temperature_celsius = round(random.uniform(18.0, 33.0), 1)
        festival_nearby = random.choice(["Diwali", "Holi", "Ganesh Chaturthi", "None"])
        time_of_day = self._get_time_of_day(hour)
        user_activity_hint = self._mock_user_activity(user_id)

        context = {
            "timestamp": now.isoformat() + "Z",
            "location": location,
            "weather": weather,
            "temperature_celsius": temperature_celsius,
            "festival_nearby": festival_nearby,
            "time_of_day": time_of_day,
            "user_activity_hint": user_activity_hint,
        }

        # optionally persist
        if self.enable_persistence:
            try:
                self.persist_context(context, user_id)
            except Exception:
                # do not raise — logging persistence error should not break the pipeline
                pass

        return context

    def persist_context(self, context: Dict[str, Any], user_id: Optional[str] = None) -> None:
        """
        Persist a snapshot of the environment context to MongoDB.
        Non-blocking behavior is expected in production (we keep it simple here).
        """
        if not self.enable_persistence or self._mongo_client is None:
            return
        doc = {
            "timestamp": context.get("timestamp"),
            "user_id": user_id,
            "context": context,
        }
        # simple insert; in production do bulk writes / TTL indices etc.
        self._db[ENV_COLLECTION].insert_one(doc)

    def _get_time_of_day(self, hour: int) -> str:
        if 5 <= hour < 12:
            return "Morning"
        elif 12 <= hour < 17:
            return "Afternoon"
        elif 17 <= hour < 21:
            return "Evening"
        else:
            return "Night"

    def _mock_user_activity(self, user_id: Optional[str]) -> Optional[str]:
        """
        Returns a simple user activity hint based on optional user_id.
        Replace this with real user-history lookups later.
        """
        if not user_id:
            return random.choice([None, "browsing_home_decor", "looking_for_tech", None])
        # deterministic-ish hint for a user_id: simple hash mod
        try:
            val = sum(ord(c) for c in str(user_id)) % 4
        except Exception:
            val = random.randint(0, 3)
        mapping = {
            0: None,
            1: "browsing_home_decor",
            2: "purchased_clothing_recently",
            3: "interested_in_kitchen"
        }
        return mapping.get(val, None)
