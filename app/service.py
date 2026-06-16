import joblib
import numpy as np
import pandas as pd
import uuid
from pathlib import Path

from app.schemas import RecommendInput, RecommendOutput, ProgramOutput, ProfileScore
from app.schemas import NutritionInput, NutritionOutput
from app.schemas import CaloriesInput, CaloriesOutput, MealsInput, MealsOutput, MealItem
from app.schemas import SessionInput, SessionOutput, WorkoutSessionOutput, SessionExerciseItem, BODY_REGION_TO_PARTS

ROOT = Path(__file__).parent.parent
MODELS_DIR = ROOT / "ml" / "models"

sys_path_appended = False
try:
    import sys
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "ml"))
    from ml.src.preprocessing.engineer import engineer
    from ml.src.preprocessing.pipeline import get_feature_names
    from ml.src.recommendation_engine.engine import get_program, program_to_dict
    sys_path_appended = True
except Exception as e:
    sys_path_appended = False
    _IMPORT_ERROR = str(e)


_BMI_CATEGORIES = [
    (18.5, "Sous-poids"),
    (25.0, "Normal"),
    (30.0, "Surpoids"),
    (float("inf"), "Obésité"),
]

_LEGACY_MESSAGES = {
    "perte_poids": "Privilégiez un déficit calorique modéré et augmentez votre activité physique.",
    "maintien":    "Continuez sur votre lancée : alimentation équilibrée et activité régulière.",
    "prise_masse": "Augmentez votre apport calorique avec des protéines de qualité et un entraînement en résistance.",
}


def _bmi_category(bmi: float) -> str:
    for threshold, label in _BMI_CATEGORIES:
        if bmi < threshold:
            return label
    return "Obésité"


class FitnessService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._model   = joblib.load(MODELS_DIR / "model.pkl")
            cls._instance._encoder = joblib.load(MODELS_DIR / "encoder.pkl")
        return cls._instance

    def recommend(self, data: RecommendInput) -> RecommendOutput:
        if not sys_path_appended:
            raise RuntimeError(f"Import ML modules failed: {_IMPORT_ERROR}")

        bmi = data.weight_kg / (data.height_cm / 100) ** 2

        row = pd.DataFrame([{
            "age":              data.age,
            "gender":           data.gender_encoded(),
            "weight_kg":        data.weight_kg,
            "height_cm":        data.height_cm,
            "bmi":              round(bmi, 2),
            "body_fat_pct":     data.body_fat_pct,
            "resting_bpm":      data.resting_bpm,
            "experience_level": data.experience_encoded(),
        }])

        row = engineer(row)
        X = row[get_feature_names()]

        probas = self._model.predict_proba(X)[0]
        top3_idx = np.argsort(probas)[::-1][:3]
        top_profiles = [
            ProfileScore(
                profile=self._encoder.inverse_transform([i])[0],
                confidence=round(float(probas[i]), 4),
            )
            for i in top3_idx
        ]

        encoded    = self._model.predict(X)[0]
        profile    = self._encoder.inverse_transform([encoded])[0]
        confidence = float(probas[top3_idx[0]])

        try:
            prog = get_program(profile)
        except RuntimeError as e:
            raise RuntimeError(
                f"DATABASE_URL non configurée. "
                f"Lancez : export DATABASE_URL=postgresql://... avant de démarrer l'API. "
                f"Détail : {e}"
            )

        prediction_id = str(uuid.uuid4())

        # Log Firebase
        try:
            from app.firebase import log_prediction
            log_prediction(prediction_id, profile, round(confidence, 4), {
                "age": data.age, "gender": data.gender,
                "weight_kg": data.weight_kg, "height_cm": data.height_cm,
                "body_fat_pct": data.body_fat_pct, "resting_bpm": data.resting_bpm,
                "experience_level": data.experience_level,
            })
            print(f"[Firebase] ✓ prediction {prediction_id} sauvegardée")
        except Exception as e:
            print(f"[Firebase] ✗ ERREUR log_prediction : {type(e).__name__}: {e}")

        return RecommendOutput(
            prediction_id=prediction_id,
            profile=profile,
            confidence=round(confidence, 4),
            top_profiles=top_profiles,
            bmi=round(bmi, 2),
            bmi_category=_bmi_category(bmi),
            program=ProgramOutput(**program_to_dict(prog)),
        )

    def calculate_calories(self, data: CaloriesInput) -> CaloriesOutput:
        # Harris-Benedict (révision Mifflin-St Jeor, plus précise)
        if data.gender == "male":
            bmr = 88.362 + (13.397 * data.weight_kg) + (4.799 * data.height_cm) - (5.677 * data.age)
        else:
            bmr = 447.593 + (9.247 * data.weight_kg) + (3.098 * data.height_cm) - (4.330 * data.age)

        # Facteur d'activité selon le profil (sessions/semaine)
        _ACTIVITY = {
            "maintien_bien_etre":    1.375,  # 3 séances légères
            "perte_poids_debutant":  1.375,  # 3 séances modérées
            "amelioration_cardio":   1.55,   # 4 séances cardio
            "perte_poids_confirme":  1.55,   # 4 séances intenses
            "prise_masse_debutant":  1.375,  # 3 séances muscu
            "prise_masse_confirme":  1.55,   # 4 séances muscu
        }
        tdee = round(bmr * _ACTIVITY[data.profile], 1)

        # Variation totale et hebdomadaire nécessaire
        total_change = data.target_weight_kg - data.weight_kg  # négatif = perte, positif = prise
        weekly_change = total_change / data.weeks_to_goal
        # 1 kg de graisse ≈ 7700 kcal
        daily_adjustment = round((weekly_change * 7700) / 7, 1)

        # Clamp selon les recommandations de sécurité
        if total_change < 0:
            # Perte : déficit max 750 kcal/j (>750 = risque masse musculaire)
            daily_adjustment = max(daily_adjustment, -750)
            goal_type = "deficit"
        else:
            # Prise : surplus max 500 kcal/j (>500 = trop de gras pris)
            daily_adjustment = min(daily_adjustment, 500)
            goal_type = "surplus"

        daily_target = round(tdee + daily_adjustment, 0)

        # Protéines selon le profil
        _PROTEIN_RATIO = {
            "perte_poids_debutant":  1.6,
            "perte_poids_confirme":  2.0,
            "prise_masse_debutant":  1.8,
            "prise_masse_confirme":  2.2,
            "amelioration_cardio":   1.4,
            "maintien_bien_etre":    1.4,
        }
        protein_g = round(data.weight_kg * _PROTEIN_RATIO[data.profile], 0)

        _NOTES = {
            "perte_poids_debutant":  "Déficit modéré recommandé. Privilégier les protéines pour préserver le muscle. Éviter de descendre sous 1200 kcal/j.",
            "perte_poids_confirme":  "Déficit plus agressif possible grâce à l'expérience. Conserver l'entraînement en résistance pour limiter la perte musculaire.",
            "prise_masse_debutant":  "Surplus léger suffit pour un débutant (les gains novices sont efficaces). Augmenter progressivement si la balance ne bouge pas.",
            "prise_masse_confirme":  "Surplus contrôlé pour limiter la prise de gras. Créatine monohydrate 5g/j recommandée (evidence level A).",
            "amelioration_cardio":   "Maintien calorique ou léger déficit. Glucides importants comme carburant pour les séances longues.",
            "maintien_bien_etre":    "Objectif équilibre — pas de restriction. Hydratation et qualité alimentaire prioritaires.",
        }

        return CaloriesOutput(
            bmr=round(bmr, 1),
            tdee=tdee,
            daily_adjustment=daily_adjustment,
            daily_calories_target=daily_target,
            weekly_change_kg=round(weekly_change, 3),
            total_change_kg=round(total_change, 1),
            goal_type=goal_type,
            protein_target_g=protein_g,
            note=_NOTES[data.profile],
        )

    def get_meals(self, data: MealsInput) -> MealsOutput:
        import psycopg2, psycopg2.extras, os
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            raise RuntimeError("DATABASE_URL non configurée.")

        conditions = ["%s = ANY(profiles)"]
        params: list = [data.profile]

        if data.allergens_to_exclude:
            conditions.append("NOT allergens && %s::text[]")
            params.append(data.allergens_to_exclude)

        if data.meal_type:
            conditions.append("meal_type = %s")
            params.append(data.meal_type)

        where = " AND ".join(conditions)

        with psycopg2.connect(db_url, cursor_factory=psycopg2.extras.RealDictCursor) as conn:
            with conn.cursor() as cur:
                cur.execute('SET search_path TO "Data"')
                cur.execute(
                    f"""
                    SELECT name, meal_type, calories_kcal, proteins_g, carbs_g, fats_g, allergens
                    FROM meals
                    WHERE {where}
                    ORDER BY RANDOM()
                    LIMIT 10
                    """,
                    params,
                )
                rows = cur.fetchall()

        meals = [
            MealItem(
                name=r["name"],
                meal_type=r["meal_type"],
                calories_kcal=r["calories_kcal"],
                proteins_g=r["proteins_g"],
                carbs_g=r["carbs_g"],
                fats_g=r["fats_g"],
                allergens=r["allergens"],
            )
            for r in rows
        ]

        return MealsOutput(
            profile=data.profile,
            allergens_excluded=data.allergens_to_exclude,
            meal_type_filter=data.meal_type,
            count=len(meals),
            meals=meals,
        )

    def get_sessions(self, data: SessionInput) -> SessionOutput:
        import psycopg2, psycopg2.extras, os
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            raise RuntimeError("DATABASE_URL non configurée.")

        # Construire la liste des body_parts à exclure depuis les régions
        excluded_parts: set[str] = set()
        for region in data.body_parts_to_exclude:
            excluded_parts.update(BODY_REGION_TO_PARTS.get(region, []))

        conditions = ["ws.profile = %s"]
        params: list = [data.profile]

        if data.session_type:
            conditions.append("ws.session_type = %s")
            params.append(data.session_type)

        where = " AND ".join(conditions)

        with psycopg2.connect(db_url, cursor_factory=psycopg2.extras.RealDictCursor) as conn:
            with conn.cursor() as cur:
                cur.execute('SET search_path TO "Data"')
                cur.execute(
                    f"""
                    SELECT id, name, profile, session_type, total_duration_min,
                           difficulty, description, objective
                    FROM workout_sessions ws
                    WHERE {where}
                    ORDER BY id
                    """,
                    params,
                )
                sessions_rows = cur.fetchall()

                sessions = []
                for s in sessions_rows:
                    # Exclure les exercices qui sollicitent les zones blessées
                    if excluded_parts:
                        exclude_list = list(excluded_parts)
                        ex_params = (s["id"], exclude_list)
                        ex_sql = """
                            SELECT se.order_num, se.sets, se.reps, se.rest_sec, se.notes,
                                   we.name AS exercise_name, we.body_part, we.category, we.equipment
                            FROM session_exercises se
                            JOIN workout_exercises we ON we.id = se.exercise_id
                            WHERE se.session_id = %s
                              AND (we.body_part IS NULL OR we.body_part != ALL(%s::text[]))
                            ORDER BY se.order_num
                        """
                    else:
                        ex_params = (s["id"],)
                        ex_sql = """
                            SELECT se.order_num, se.sets, se.reps, se.rest_sec, se.notes,
                                   we.name AS exercise_name, we.body_part, we.category, we.equipment
                            FROM session_exercises se
                            JOIN workout_exercises we ON we.id = se.exercise_id
                            WHERE se.session_id = %s
                            ORDER BY se.order_num
                        """

                    cur.execute(ex_sql, ex_params)
                    ex_rows = cur.fetchall()

                    exercises = [
                        SessionExerciseItem(
                            order_num=e["order_num"],
                            exercise_name=e["exercise_name"],
                            body_part=e["body_part"],
                            category=e["category"],
                            equipment=e["equipment"],
                            sets=e["sets"],
                            reps=e["reps"],
                            rest_sec=e["rest_sec"],
                            notes=e["notes"],
                        )
                        for e in ex_rows
                    ]

                    sessions.append(
                        WorkoutSessionOutput(
                            session_id=s["id"],
                            name=s["name"],
                            profile=s["profile"],
                            session_type=s["session_type"],
                            total_duration_min=s["total_duration_min"],
                            difficulty=s["difficulty"],
                            description=s["description"],
                            objective=s["objective"],
                            exercises=exercises,
                        )
                    )

        return SessionOutput(
            profile=data.profile,
            session_type_filter=data.session_type,
            body_parts_excluded=data.body_parts_to_exclude,
            count=len(sessions),
            sessions=sessions,
        )

    def predict_legacy(self, data: NutritionInput) -> NutritionOutput:
        """Rétrocompatibilité avec l'ancien endpoint /nutrition/predict."""
        imc = data.poids_kg / (data.taille_cm / 100) ** 2

        # Mapping simple vers les 3 anciens labels via règle
        if imc >= 27.5:
            label = "perte_poids"
        elif imc < 22:
            label = "prise_masse"
        else:
            label = "maintien"

        return NutritionOutput(
            imc=round(imc, 2),
            imc_categorie=_bmi_category(imc),
            label=label,
            confidence=0.0,
            message=_LEGACY_MESSAGES[label],
        )
