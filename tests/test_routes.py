"""
Tests de toutes les routes de l'API HealthAI Coach.

Stratégie de mock :
- DB (psycopg2) : mockée pour les routes /nutrition/meals et /sessions/exercises
- Firebase      : mockée pour les routes /logs/* et le log interne de /recommend
- Modèle ML     : chargé réellement depuis ml/models/model.pkl (pré-entraîné)
- get_program   : mockée (évite la dépendance DB dans /recommend)
"""

from unittest.mock import MagicMock, patch

import pytest

from ml.src.recommendation_engine.engine import Program

from tests.conftest import (
    MOCK_EXERCISE,
    MOCK_MEAL,
    MOCK_PROGRAM,
    MOCK_SESSION,
    VALID_USER,
    make_mock_conn,
    make_mock_cursor,
)

MOCK_PROGRAM_OBJ = Program(
    profile="prise_masse_confirme",
    **MOCK_PROGRAM,
)


# ─────────────────────────────────────────────
# GET /health
# ─────────────────────────────────────────────

class TestHealth:
    def test_returns_ok(self, client):
        r = client.get("/health")
        assert r.status_code == 200

    def test_response_structure(self, client):
        body = client.get("/health").json()
        assert body["status"] == "ok"
        assert "version" in body


# ─────────────────────────────────────────────
# GET /profiles
# ─────────────────────────────────────────────

class TestProfiles:
    def test_returns_200(self, client):
        assert client.get("/profiles").status_code == 200

    def test_returns_six_profiles(self, client):
        body = client.get("/profiles").json()
        assert len(body["profiles"]) == 6

    def test_profile_has_required_fields(self, client):
        profiles = client.get("/profiles").json()["profiles"]
        for p in profiles:
            assert "id" in p
            assert "focus" in p
            assert "sessions_per_week" in p

    def test_known_profile_ids(self, client):
        ids = {p["id"] for p in client.get("/profiles").json()["profiles"]}
        expected = {
            "prise_masse_confirme", "prise_masse_debutant",
            "perte_poids_confirme", "perte_poids_debutant",
            "amelioration_cardio", "maintien_bien_etre",
        }
        assert ids == expected


# ─────────────────────────────────────────────
# POST /recommend
# ─────────────────────────────────────────────

class TestRecommend:
    def _post(self, client, payload=None):
        return client.post("/recommend", json=payload or VALID_USER)

    @patch("app.service.get_program")
    @patch("app.firebase.log_prediction", return_value=None)
    def test_returns_200(self, mock_log, mock_prog, client):
        mock_prog.return_value = MOCK_PROGRAM_OBJ
        assert self._post(client).status_code == 200

    @patch("app.service.get_program")
    @patch("app.firebase.log_prediction", return_value=None)
    def test_response_structure(self, mock_log, mock_prog, client):
        mock_prog.return_value = MOCK_PROGRAM_OBJ
        body = self._post(client).json()
        assert "prediction_id" in body
        assert "profile" in body
        assert "confidence" in body
        assert "top_profiles" in body
        assert "bmi" in body
        assert "bmi_category" in body
        assert "program" in body

    @patch("app.service.get_program")
    @patch("app.firebase.log_prediction", return_value=None)
    def test_profile_is_valid(self, mock_log, mock_prog, client):
        mock_prog.return_value = MOCK_PROGRAM_OBJ
        valid_profiles = {
            "prise_masse_confirme", "prise_masse_debutant",
            "perte_poids_confirme", "perte_poids_debutant",
            "amelioration_cardio", "maintien_bien_etre",
        }
        body = self._post(client).json()
        assert body["profile"] in valid_profiles

    @patch("app.service.get_program")
    @patch("app.firebase.log_prediction", return_value=None)
    def test_confidence_between_0_and_1(self, mock_log, mock_prog, client):
        mock_prog.return_value = MOCK_PROGRAM_OBJ
        body = self._post(client).json()
        assert 0.0 <= body["confidence"] <= 1.0

    @patch("app.service.get_program")
    @patch("app.firebase.log_prediction", return_value=None)
    def test_top_profiles_count(self, mock_log, mock_prog, client):
        mock_prog.return_value = MOCK_PROGRAM_OBJ
        body = self._post(client).json()
        assert len(body["top_profiles"]) == 3

    @patch("app.service.get_program")
    @patch("app.firebase.log_prediction", return_value=None)
    def test_bmi_is_calculated(self, mock_log, mock_prog, client):
        mock_prog.return_value = MOCK_PROGRAM_OBJ
        body = self._post(client).json()
        expected_bmi = round(78.0 / (178.0 / 100) ** 2, 2)
        assert abs(body["bmi"] - expected_bmi) < 0.1

    def test_invalid_age_returns_422(self, client):
        payload = {**VALID_USER, "age": 10}
        assert self._post(client, payload).status_code == 422

    def test_invalid_gender_returns_422(self, client):
        payload = {**VALID_USER, "gender": "unknown"}
        assert self._post(client, payload).status_code == 422

    def test_invalid_experience_returns_422(self, client):
        payload = {**VALID_USER, "experience_level": "expert"}
        assert self._post(client, payload).status_code == 422

    def test_bmi_out_of_range_returns_422(self, client):
        # BMI très élevé : poids 200kg, taille 150cm → IMC ~88
        payload = {**VALID_USER, "weight_kg": 190.0, "height_cm": 141.0}
        assert self._post(client, payload).status_code == 422


# ─────────────────────────────────────────────
# POST /nutrition/calories
# ─────────────────────────────────────────────

class TestCalories:
    BASE = {
        "age": 30,
        "gender": "female",
        "weight_kg": 65.0,
        "height_cm": 165.0,
        "target_weight_kg": 60.0,
        "weeks_to_goal": 12,
        "profile": "perte_poids_debutant",
    }

    def test_returns_200(self, client):
        assert client.post("/nutrition/calories", json=self.BASE).status_code == 200

    def test_response_fields(self, client):
        body = client.post("/nutrition/calories", json=self.BASE).json()
        for field in ["bmr", "tdee", "daily_adjustment", "daily_calories_target",
                      "weekly_change_kg", "total_change_kg", "goal_type",
                      "protein_target_g", "note"]:
            assert field in body, f"Champ manquant : {field}"

    def test_goal_type_is_deficit_for_weight_loss(self, client):
        body = client.post("/nutrition/calories", json=self.BASE).json()
        assert body["goal_type"] == "deficit"

    def test_goal_type_is_surplus_for_mass_gain(self, client):
        payload = {**self.BASE, "target_weight_kg": 70.0, "profile": "prise_masse_debutant"}
        body = client.post("/nutrition/calories", json=payload).json()
        assert body["goal_type"] == "surplus"

    def test_deficit_capped_at_750(self, client):
        # Objectif agressif : -20 kg en 4 semaines → doit être clampé à -750
        payload = {**self.BASE, "target_weight_kg": 45.0, "weeks_to_goal": 4}
        body = client.post("/nutrition/calories", json=payload).json()
        assert body["daily_adjustment"] >= -750

    def test_surplus_capped_at_500(self, client):
        # Objectif agressif : +20 kg en 4 semaines → doit être clampé à +500
        payload = {**self.BASE, "target_weight_kg": 85.0, "weeks_to_goal": 4,
                   "profile": "prise_masse_confirme"}
        body = client.post("/nutrition/calories", json=payload).json()
        assert body["daily_adjustment"] <= 500

    def test_bmr_is_positive(self, client):
        body = client.post("/nutrition/calories", json=self.BASE).json()
        assert body["bmr"] > 0

    def test_invalid_profile_returns_422(self, client):
        payload = {**self.BASE, "profile": "profil_inexistant"}
        assert client.post("/nutrition/calories", json=payload).status_code == 422

    def test_missing_field_returns_422(self, client):
        payload = {k: v for k, v in self.BASE.items() if k != "weeks_to_goal"}
        assert client.post("/nutrition/calories", json=payload).status_code == 422


# ─────────────────────────────────────────────
# POST /nutrition/meals
# ─────────────────────────────────────────────

class TestMeals:
    BASE = {"profile": "prise_masse_confirme", "allergens_to_exclude": [], "meal_type": None}

    def _mock_db(self, rows):
        cur = make_mock_cursor(fetchall_return=rows)
        conn = make_mock_conn(cur)
        return conn

    @patch("psycopg2.connect")
    def test_returns_200(self, mock_connect, client):
        mock_connect.return_value = self._mock_db([MOCK_MEAL])
        with patch.dict("os.environ", {"DATABASE_URL": "postgresql://fake"}):
            r = client.post("/nutrition/meals", json=self.BASE)
        assert r.status_code == 200

    @patch("psycopg2.connect")
    def test_response_structure(self, mock_connect, client):
        mock_connect.return_value = self._mock_db([MOCK_MEAL])
        with patch.dict("os.environ", {"DATABASE_URL": "postgresql://fake"}):
            body = client.post("/nutrition/meals", json=self.BASE).json()
        assert "meals" in body
        assert "count" in body
        assert body["count"] == len(body["meals"])

    @patch("psycopg2.connect")
    def test_meal_has_required_fields(self, mock_connect, client):
        mock_connect.return_value = self._mock_db([MOCK_MEAL])
        with patch.dict("os.environ", {"DATABASE_URL": "postgresql://fake"}):
            meals = client.post("/nutrition/meals", json=self.BASE).json()["meals"]
        for m in meals:
            for field in ["name", "meal_type", "calories_kcal", "proteins_g", "carbs_g", "fats_g"]:
                assert field in m

    @patch("psycopg2.connect")
    def test_filter_by_meal_type(self, mock_connect, client):
        mock_connect.return_value = self._mock_db([MOCK_MEAL])
        payload = {**self.BASE, "meal_type": "breakfast"}
        with patch.dict("os.environ", {"DATABASE_URL": "postgresql://fake"}):
            r = client.post("/nutrition/meals", json=payload)
        assert r.status_code == 200

    @patch("psycopg2.connect")
    def test_empty_result_is_valid(self, mock_connect, client):
        mock_connect.return_value = self._mock_db([])
        with patch.dict("os.environ", {"DATABASE_URL": "postgresql://fake"}):
            body = client.post("/nutrition/meals", json=self.BASE).json()
        assert body["count"] == 0
        assert body["meals"] == []

    def test_invalid_profile_returns_422(self, client):
        payload = {**self.BASE, "profile": "inconnu"}
        assert client.post("/nutrition/meals", json=payload).status_code == 422

    def test_invalid_allergen_returns_422(self, client):
        payload = {**self.BASE, "allergens_to_exclude": ["pollen"]}
        assert client.post("/nutrition/meals", json=payload).status_code == 422

    def test_invalid_meal_type_returns_422(self, client):
        payload = {**self.BASE, "meal_type": "brunch"}
        assert client.post("/nutrition/meals", json=payload).status_code == 422

    def test_no_database_url_returns_500(self, client):
        from fastapi.testclient import TestClient
        from app.main import app
        with patch.dict("os.environ", {"DATABASE_URL": ""}):
            import os; os.environ.pop("DATABASE_URL", None)
            with TestClient(app, raise_server_exceptions=False) as c:
                r = c.post("/nutrition/meals", json=self.BASE)
        assert r.status_code == 500


# ─────────────────────────────────────────────
# POST /sessions/exercises
# ─────────────────────────────────────────────

class TestSessions:
    BASE = {"profile": "prise_masse_confirme", "session_type": None, "body_parts_to_exclude": []}

    def _mock_db_sessions(self):
        cur = make_mock_cursor()
        # Premier fetchall → sessions, deuxième → exercices
        cur.fetchall.side_effect = [[MOCK_SESSION], [MOCK_EXERCISE]]
        conn = make_mock_conn(cur)
        return conn

    @patch("psycopg2.connect")
    def test_returns_200(self, mock_connect, client):
        mock_connect.return_value = self._mock_db_sessions()
        with patch.dict("os.environ", {"DATABASE_URL": "postgresql://fake"}):
            r = client.post("/sessions/exercises", json=self.BASE)
        assert r.status_code == 200

    @patch("psycopg2.connect")
    def test_response_structure(self, mock_connect, client):
        mock_connect.return_value = self._mock_db_sessions()
        with patch.dict("os.environ", {"DATABASE_URL": "postgresql://fake"}):
            body = client.post("/sessions/exercises", json=self.BASE).json()
        assert "sessions" in body
        assert "count" in body
        assert body["count"] == len(body["sessions"])

    @patch("psycopg2.connect")
    def test_session_has_exercises(self, mock_connect, client):
        mock_connect.return_value = self._mock_db_sessions()
        with patch.dict("os.environ", {"DATABASE_URL": "postgresql://fake"}):
            sessions = client.post("/sessions/exercises", json=self.BASE).json()["sessions"]
        assert len(sessions) > 0
        assert "exercises" in sessions[0]

    @patch("psycopg2.connect")
    def test_exercise_has_required_fields(self, mock_connect, client):
        mock_connect.return_value = self._mock_db_sessions()
        with patch.dict("os.environ", {"DATABASE_URL": "postgresql://fake"}):
            sessions = client.post("/sessions/exercises", json=self.BASE).json()["sessions"]
        ex = sessions[0]["exercises"][0]
        for field in ["exercise_name", "sets", "reps", "rest_sec", "order_num"]:
            assert field in ex

    @patch("psycopg2.connect")
    def test_filter_by_session_type(self, mock_connect, client):
        mock_connect.return_value = self._mock_db_sessions()
        payload = {**self.BASE, "session_type": "push"}
        with patch.dict("os.environ", {"DATABASE_URL": "postgresql://fake"}):
            r = client.post("/sessions/exercises", json=payload)
        assert r.status_code == 200

    def test_invalid_profile_returns_422(self, client):
        payload = {**self.BASE, "profile": "inconnu"}
        assert client.post("/sessions/exercises", json=payload).status_code == 422

    def test_invalid_body_region_returns_422(self, client):
        payload = {**self.BASE, "body_parts_to_exclude": ["tete"]}
        assert client.post("/sessions/exercises", json=payload).status_code == 422

    def test_no_database_url_returns_500(self, client):
        from fastapi.testclient import TestClient
        from app.main import app
        with patch.dict("os.environ", {"DATABASE_URL": ""}):
            import os; os.environ.pop("DATABASE_URL", None)
            with TestClient(app, raise_server_exceptions=False) as c:
                r = c.post("/sessions/exercises", json=self.BASE)
        assert r.status_code == 500


# ─────────────────────────────────────────────
# POST /logs/feedback
# ─────────────────────────────────────────────

class TestFeedback:
    BASE = {
        "prediction_id": "abc-123",
        "chosen_profile": "prise_masse_confirme",
    }

    @patch("app.firebase.log_feedback")
    def test_returns_200(self, mock_fb, client):
        mock_fb.return_value = {
            "recommended_profile": "prise_masse_confirme",
            "chosen_profile": "prise_masse_confirme",
            "followed_recommendation": True,
        }
        r = client.post("/logs/feedback", json=self.BASE)
        assert r.status_code == 200

    @patch("app.firebase.log_feedback")
    def test_response_structure(self, mock_fb, client):
        mock_fb.return_value = {
            "recommended_profile": "prise_masse_debutant",
            "chosen_profile": "prise_masse_confirme",
            "followed_recommendation": False,
        }
        body = client.post("/logs/feedback", json=self.BASE).json()
        assert "prediction_id" in body
        assert "recommended_profile" in body
        assert "chosen_profile" in body
        assert "followed_recommendation" in body

    @patch("app.firebase.log_feedback")
    def test_followed_recommendation_true_when_same_profile(self, mock_fb, client):
        mock_fb.return_value = {
            "recommended_profile": "prise_masse_confirme",
            "chosen_profile": "prise_masse_confirme",
            "followed_recommendation": True,
        }
        body = client.post("/logs/feedback", json=self.BASE).json()
        assert body["followed_recommendation"] is True

    @patch("app.firebase.log_feedback", side_effect=ValueError("prediction introuvable"))
    def test_unknown_prediction_id_returns_404(self, mock_fb, client):
        r = client.post("/logs/feedback", json=self.BASE)
        assert r.status_code == 404

    def test_invalid_chosen_profile_returns_422(self, client):
        payload = {**self.BASE, "chosen_profile": "profil_inexistant"}
        assert client.post("/logs/feedback", json=payload).status_code == 422

    def test_missing_prediction_id_returns_422(self, client):
        payload = {"chosen_profile": "prise_masse_confirme"}
        assert client.post("/logs/feedback", json=payload).status_code == 422


# ─────────────────────────────────────────────
# GET /logs/comparison
# ─────────────────────────────────────────────

class TestComparison:
    MOCK_STATS = {
        "total_with_feedback": 42,
        "followed_recommendation": 30,
        "follow_rate_pct": 71.4,
        "by_profile": {
            "prise_masse_confirme": {"total": 10, "followed": 8},
        },
    }

    @patch("app.firebase.get_comparison_stats")
    def test_returns_200(self, mock_stats, client):
        mock_stats.return_value = self.MOCK_STATS
        assert client.get("/logs/comparison").status_code == 200

    @patch("app.firebase.get_comparison_stats")
    def test_response_structure(self, mock_stats, client):
        mock_stats.return_value = self.MOCK_STATS
        body = client.get("/logs/comparison").json()
        assert "total_with_feedback" in body
        assert "followed_recommendation" in body
        assert "follow_rate_pct" in body
        assert "by_profile" in body

    @patch("app.firebase.get_comparison_stats")
    def test_follow_rate_between_0_and_100(self, mock_stats, client):
        mock_stats.return_value = self.MOCK_STATS
        body = client.get("/logs/comparison").json()
        assert 0.0 <= body["follow_rate_pct"] <= 100.0

    @patch("app.firebase.get_comparison_stats", side_effect=Exception("Firebase down"))
    def test_firebase_error_returns_500(self, mock_stats, client):
        r = client.get("/logs/comparison")
        assert r.status_code == 500
