"""
Moteur de recommandation dynamique — interroge la BDD ETL HealthIA.
Mapping profil ML → filtres SQL sur exercises + foods.
"""
from __future__ import annotations

import os
import psycopg2
import psycopg2.extras
from dataclasses import dataclass

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "La variable d'environnement DATABASE_URL est requise.\n"
        "Exemple : export DATABASE_URL=postgresql://user:pass@host:port/healthai\n"
        "Voir .env.example pour le format."
    )

# ---------------------------------------------------------------------------
# Mapping profil → filtres BDD
# ---------------------------------------------------------------------------

_PROFILE_CONFIG: dict[str, dict] = {
    "prise_masse_confirme": {
        "sessions_per_week": 4,
        "session_duration_min": 60,
        "focus": "Hypertrophie — programme split push/pull",
        "intensity": "Élevée — 70-80% 1RM, 6-12 reps, surcharge progressive.",
        "weekly_volume_h": 4.0,
        "progression": "Périodisation ondulante : alterner semaines force (5×5) et hypertrophie (4×10).",
        "objective": "Hypertrophie musculaire avancée avec minimisation du gras pris.",
        "exercise_filters": {"difficulty": "avance", "categories": ["Strength", "Powerlifting", "Olympic Weightlifting"], "body_parts": ["Chest", "Lats", "Middle Back", "Shoulders", "Quadriceps", "Hamstrings", "Glutes", "Triceps", "Biceps"]},
        "food_filters": {"min_proteins_g": 25, "meal_types": ["breakfast", "lunch", "dinner"], "sort": "proteins_g DESC"},
        "nutrition_tip": "Surplus calorique de 300-400 kcal/j. Protéines 2.0-2.2 g/kg. Créatine monohydrate 5g/j.",
    },
    "prise_masse_debutant": {
        "sessions_per_week": 3,
        "session_duration_min": 50,
        "focus": "Renforcement musculaire fondamental — full body",
        "intensity": "Modérée-élevée — charge à 65-75% 1RM. Tempo contrôlé.",
        "weekly_volume_h": 2.5,
        "progression": "Programme linéaire : +2.5 kg chaque séance sur les exercices de base.",
        "objective": "Construction des bases musculaires — progression des charges toutes les séances.",
        "exercise_filters": {"difficulty": "debutant", "categories": ["Strength"], "body_parts": ["Chest", "Lats", "Quadriceps", "Abdominals", "Shoulders"]},
        "food_filters": {"min_proteins_g": 20, "meal_types": ["breakfast", "lunch", "dinner"], "sort": "proteins_g DESC"},
        "nutrition_tip": "Surplus calorique de 200-300 kcal/j. Protéines 1.8 g/kg. Glucides avant et après l'entraînement.",
    },
    "perte_poids_confirme": {
        "sessions_per_week": 4,
        "session_duration_min": 50,
        "focus": "HIIT + musculation + cardio soutenu",
        "intensity": "Élevée — 70-85% FCmax sur les séances HIIT.",
        "weekly_volume_h": 3.3,
        "progression": "Augmenter l'intensité HIIT après 3 semaines. Ajouter charge +5% sur musculation.",
        "objective": "Remodelage corporel — perte de graisse avec préservation musculaire.",
        "exercise_filters": {"difficulty": "avance", "categories": ["Cardio", "Plyometrics", "Strength"], "body_parts": ["Abdominals", "Quadriceps", "Hamstrings", "Glutes"]},
        "food_filters": {"max_calories": 400, "meal_types": ["breakfast", "lunch", "dinner", "snack"], "sort": "calories_kcal ASC"},
        "nutrition_tip": "Déficit calorique de 400-500 kcal/j. Protéines 1.8-2.0 g/kg. Timing : protéines post-workout dans les 2h.",
    },
    "perte_poids_debutant": {
        "sessions_per_week": 3,
        "session_duration_min": 40,
        "focus": "Cardio modéré + renforcement léger",
        "intensity": "Modérée — 55-65% FCmax (zone 2-3).",
        "weekly_volume_h": 2.0,
        "progression": "Ajouter 5 min de cardio chaque semaine. Après 4 semaines : passer à 4 séances.",
        "objective": "Perte de poids progressive — 0.5 kg/semaine est l'objectif réaliste.",
        "exercise_filters": {"difficulty": "debutant", "categories": ["Cardio", "Stretching"], "body_parts": ["Abdominals", "Quadriceps", "Glutes", "Calves"]},
        "food_filters": {"max_calories": 350, "meal_types": ["breakfast", "lunch", "dinner", "snack"], "sort": "calories_kcal ASC"},
        "nutrition_tip": "Déficit calorique de 300-400 kcal/j. Priorité aux protéines (1.6 g/kg). Éviter les ultra-transformés.",
    },
    "amelioration_cardio": {
        "sessions_per_week": 4,
        "session_duration_min": 45,
        "focus": "Développement VO2max et endurance cardio-vasculaire",
        "intensity": "Variable — 60-85% FCmax selon séance. Alternance easy/hard.",
        "weekly_volume_h": 3.0,
        "progression": "80% du volume en zone 2, 20% en zone 4-5 (polarized training). Volume +10%/semaine max.",
        "objective": "Baisser le BPM repos de 5-10 bpm en 8 semaines. Améliorer l'endurance générale.",
        "exercise_filters": {"difficulty": "intermediaire", "categories": ["Cardio", "Plyometrics"], "body_parts": ["Quadriceps", "Hamstrings", "Calves", "Abdominals"]},
        "food_filters": {"min_carbs_g": 30, "meal_types": ["breakfast", "lunch", "dinner"], "sort": "carbs_g DESC"},
        "nutrition_tip": "Glucides comme carburant principal sur les séances longues. Hydratation : 500ml/h d'effort.",
    },
    "maintien_bien_etre": {
        "sessions_per_week": 3,
        "session_duration_min": 45,
        "focus": "Équilibre forme physique et récupération",
        "intensity": "Légère à modérée — 50-65% FCmax. Plaisir et régularité prioritaires.",
        "weekly_volume_h": 2.25,
        "progression": "Maintenir le volume. Varier les activités pour éviter la monotonie.",
        "objective": "Maintenir la condition physique actuelle. Bien-être général et prévention du déconditionnement.",
        "exercise_filters": {"difficulty": "debutant", "categories": ["Stretching", "Cardio", "Strength"], "body_parts": ["Abdominals", "Shoulders", "Lats", "Quadriceps"]},
        "food_filters": {"meal_types": ["breakfast", "lunch", "dinner", "snack"], "sort": "proteins_g DESC"},
        "nutrition_tip": "Alimentation équilibrée. Pas de restriction. Hydratation et sommeil sont les leviers prioritaires.",
    },
}


# ---------------------------------------------------------------------------
# Requêtes BDD
# ---------------------------------------------------------------------------

def _get_exercises(cur, filters: dict, limit: int = 6) -> list[str]:
    categories_ph = ",".join(["%s"] * len(filters["categories"]))
    body_parts_ph = ",".join(["%s"] * len(filters["body_parts"]))
    params = [filters["difficulty"]] + filters["categories"] + filters["body_parts"] + [limit]
    cur.execute(
        f"""
        SELECT name, body_part, category
        FROM exercises
        WHERE difficulty = %s
          AND category   IN ({categories_ph})
          AND body_part  IN ({body_parts_ph})
        ORDER BY RANDOM()
        LIMIT %s
        """,
        params,
    )
    rows = cur.fetchall()
    return [f"{r['name']} ({r['body_part']} — {r['category']})" for r in rows]


def _get_foods(cur, filters: dict, limit: int = 5) -> list[str]:
    conditions = ["meal_type = ANY(%s)"]
    params: list = [filters["meal_types"]]

    if "min_proteins_g" in filters:
        conditions.append("proteins_g >= %s")
        params.append(filters["min_proteins_g"])
    if "max_calories" in filters:
        conditions.append("calories_kcal <= %s")
        params.append(filters["max_calories"])
    if "min_carbs_g" in filters:
        conditions.append("carbs_g >= %s")
        params.append(filters["min_carbs_g"])

    params.append(limit)
    where = " AND ".join(conditions)
    sort  = filters.get("sort", "proteins_g DESC")

    cur.execute(
        f"""
        SELECT name, calories_kcal, proteins_g, carbs_g, fats_g, meal_type
        FROM foods
        WHERE {where}
        ORDER BY {sort}
        LIMIT %s
        """,
        params,
    )
    rows = cur.fetchall()
    return [
        f"{r['name']} ({r['meal_type']}) — {r['calories_kcal']} kcal | P:{r['proteins_g']}g G:{r['carbs_g']}g L:{r['fats_g']}g"
        for r in rows
    ]


# ---------------------------------------------------------------------------
# Interface publique
# ---------------------------------------------------------------------------

@dataclass
class Program:
    profile: str
    sessions_per_week: int
    session_duration_min: int
    focus: str
    intensity: str
    weekly_volume_h: float
    progression: str
    nutrition_tip: str
    objective: str


def get_program(profile: str) -> Program:
    if profile not in _PROFILE_CONFIG:
        raise ValueError(f"Profil inconnu : {profile}. Valeurs valides : {list(_PROFILE_CONFIG.keys())}")

    cfg = _PROFILE_CONFIG[profile]

    return Program(
        profile=profile,
        sessions_per_week=cfg["sessions_per_week"],
        session_duration_min=cfg["session_duration_min"],
        focus=cfg["focus"],
        intensity=cfg["intensity"],
        weekly_volume_h=cfg["weekly_volume_h"],
        progression=cfg["progression"],
        nutrition_tip=cfg["nutrition_tip"],
        objective=cfg["objective"],
    )


def list_profiles() -> list[str]:
    return list(_PROFILE_CONFIG.keys())


def program_to_dict(program: Program) -> dict:
    return {
        "sessions_per_week":    program.sessions_per_week,
        "session_duration_min": program.session_duration_min,
        "focus":                program.focus,
        "intensity":            program.intensity,
        "weekly_volume_h":      program.weekly_volume_h,
        "progression":          program.progression,
        "nutrition_tip":        program.nutrition_tip,
        "objective":            program.objective,
    }
