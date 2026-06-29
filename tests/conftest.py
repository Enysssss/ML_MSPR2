import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

# engine.py lève RuntimeError à l'import si DATABASE_URL absent — on la fixe avant tout
os.environ.setdefault("DATABASE_URL", "postgresql://fake:fake@localhost/fake")


# Données communes réutilisées dans plusieurs tests
VALID_USER = {
    "age": 28,
    "gender": "male",
    "weight_kg": 78.0,
    "height_cm": 178.0,
    "body_fat_pct": 18.0,
    "resting_bpm": 65,
    "experience_level": "intermediate",
}

MOCK_PROGRAM = {
    "sessions_per_week": 4,
    "session_duration_min": 60,
    "focus": "Hypertrophie",
    "intensity": "Élevée",
    "weekly_volume_h": 4.0,
    "progression": "Surcharge progressive",
    "nutrition_tip": "2g protéines/kg",
    "objective": "Prise de masse",
}

MOCK_MEAL = {
    "name": "Omelette protéinée",
    "meal_type": "breakfast",
    "calories_kcal": 350.0,
    "proteins_g": 30.0,
    "carbs_g": 10.0,
    "fats_g": 20.0,
    "allergens": ["oeufs"],
}

MOCK_SESSION = {
    "id": 1,
    "name": "Push Day A",
    "profile": "prise_masse_confirme",
    "session_type": "push",
    "total_duration_min": 60,
    "difficulty": "Élevée",
    "description": "Séance poussée",
    "objective": "Force et hypertrophie",
}

MOCK_EXERCISE = {
    "order_num": 1,
    "exercise_name": "Développé couché",
    "body_part": "Pectoraux",
    "category": "Force",
    "equipment": "Barre",
    "sets": 4,
    "reps": "8-10",
    "rest_sec": 90,
    "notes": None,
}


def make_mock_cursor(fetchall_return=None, fetchone_return=None):
    """Crée un curseur psycopg2 mocké."""
    cur = MagicMock()
    cur.fetchall.return_value = fetchall_return or []
    cur.fetchone.return_value = fetchone_return
    cur.__enter__ = lambda s: s
    cur.__exit__ = MagicMock(return_value=False)
    return cur


def make_mock_conn(cursor):
    """Crée une connexion psycopg2 mockée."""
    conn = MagicMock()
    conn.cursor.return_value = cursor
    conn.__enter__ = lambda s: s
    conn.__exit__ = MagicMock(return_value=False)
    return conn


@pytest.fixture
def client():
    from app.main import app
    with TestClient(app) as c:
        yield c
