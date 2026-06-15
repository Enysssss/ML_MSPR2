from fastapi import FastAPI

from app.schemas import RecommendInput, RecommendOutput, NutritionInput, NutritionOutput, CaloriesInput, CaloriesOutput, MealsInput, MealsOutput, SessionInput, SessionOutput
from app.service import FitnessService

app = FastAPI(
    title="HealthAI Coach — API ML",
    description="Recommandation de programmes sportifs personnalisés par Machine Learning.",
    version="2.0.0",
)

service = FitnessService()


@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0.0"}


@app.post("/recommend", response_model=RecommendOutput)
def recommend(data: RecommendInput) -> RecommendOutput:
    """
    Prédit le profil fitness de l'utilisateur et retourne un programme sportif personnalisé.
    """
    return service.recommend(data)


@app.get("/profiles")
def list_profiles():
    """Liste les profils fitness disponibles."""
    from ml.src.recommendation_engine.engine import list_profiles, _PROFILE_CONFIG
    return {
        "profiles": [
            {
                "id": p,
                "focus": _PROFILE_CONFIG[p]["focus"],
                "sessions_per_week": _PROFILE_CONFIG[p]["sessions_per_week"],
            }
            for p in list_profiles()
        ]
    }


@app.post("/nutrition/meals", response_model=MealsOutput)
def meals(data: MealsInput) -> MealsOutput:
    """
    Retourne 10 repas complets adaptés au profil fitness.
    Filtre optionnel par allergènes et par type de repas (breakfast/lunch/dinner/snack).
    """
    return service.get_meals(data)


@app.post("/nutrition/calories", response_model=CaloriesOutput)
def calories(data: CaloriesInput) -> CaloriesOutput:
    """
    Calcule l'objectif calorique journalier via Harris-Benedict,
    ajusté selon le poids cible, le délai souhaité et le profil fitness choisi.
    Aucun ML — calcul nutritionnel pur.
    """
    return service.calculate_calories(data)


@app.post("/sessions/exercises", response_model=SessionOutput)
def session_exercises(data: SessionInput) -> SessionOutput:
    """
    Retourne les séances d'entraînement complètes pour un profil fitness.
    Chaque séance contient la liste ordonnée des exercices avec sets/reps/repos.
    Filtre optionnel par type de séance (push, pull, legs, full_body, hiit, cardio, etc.).
    """
    return service.get_sessions(data)


# Rétrocompatibilité
@app.post("/nutrition/predict", response_model=NutritionOutput, deprecated=True)
def predict_legacy(data: NutritionInput) -> NutritionOutput:
    """Ancien endpoint — utiliser /recommend à la place."""
    return service.predict_legacy(data)
