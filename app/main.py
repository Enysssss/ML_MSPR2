from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import RecommendInput, RecommendOutput, CaloriesInput, CaloriesOutput, MealsInput, MealsOutput, SessionInput, SessionOutput, FeedbackInput, FeedbackOutput, ComparisonOutput
from app.service import FitnessService

app = FastAPI(
    title="HealthAI Coach — API ML",
    description="Recommandation de programmes sportifs personnalisés par Machine Learning.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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


@app.post("/logs/feedback", response_model=FeedbackOutput)
def feedback(data: FeedbackInput) -> FeedbackOutput:
    """
    Enregistre le profil finalement choisi par l'utilisateur.
    Permet de comparer la recommandation ML avec le choix réel.
    Utilise le prediction_id retourné par /recommend.
    """
    from app.firebase import log_feedback
    doc = log_feedback(data.prediction_id, data.chosen_profile)
    return FeedbackOutput(
        prediction_id=data.prediction_id,
        recommended_profile=doc["recommended_profile"],
        chosen_profile=doc["chosen_profile"],
        followed_recommendation=doc["followed_recommendation"],
    )


@app.get("/logs/comparison", response_model=ComparisonOutput)
def comparison() -> ComparisonOutput:
    """
    Statistiques de comparaison : profil recommandé par le ML vs profil choisi par l'utilisateur.
    Indique le taux de suivi de la recommandation et les écarts par profil.
    """
    from app.firebase import get_comparison_stats
    stats = get_comparison_stats()
    return ComparisonOutput(**stats)


@app.post("/sessions/exercises", response_model=SessionOutput)
def session_exercises(data: SessionInput) -> SessionOutput:
    """
    Retourne les séances d'entraînement complètes pour un profil fitness.
    Chaque séance contient la liste ordonnée des exercices avec sets/reps/repos.
    Filtre optionnel par type de séance (push, pull, legs, full_body, hiit, cardio, etc.).
    """
    return service.get_sessions(data)


