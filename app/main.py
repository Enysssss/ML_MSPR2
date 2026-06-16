import requests as _requests

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Union

from authorization import Authorization

from app.schemas import (
    RecommendInput, RecommendOutput,
    CaloriesInput, CaloriesOutput,
    MealsInput, MealsOutput,
    SessionInput, SessionOutput,
    FeedbackInput, FeedbackOutput,
    ComparisonOutput,
)
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

bearer_scheme = HTTPBearer()

service = FitnessService()

@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0.0"}
    
@app.post("/recommend", response_model=RecommendOutput)
def recommend(data: RecommendInput, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> Union[RecommendOutput, HTTPException]:
    if Authorization.verify_token(credentials.credentials):
        return service.recommend(data)
    else:
        raise HTTPException(status_code=401, detail="Invalid token")
    
@app.get("/profiles")
def list_profiles(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    if Authorization.verify_token(credentials.credentials):
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
    else:
        raise HTTPException(status_code=401, detail="Invalid token")
    

@app.post("/nutrition/meals", response_model=MealsOutput)
def meals(data: MealsInput, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> Union[MealsOutput, HTTPException]:
    if Authorization.verify_token(credentials.credentials):
        return service.get_meals(data)
    else:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    
@app.post("/nutrition/calories", response_model=CaloriesOutput)
def calories(data: CaloriesInput, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> Union[CaloriesOutput, HTTPException]:
    if Authorization.verify_token(credentials.credentials):
        return service.calculate_calories(data)
    else:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/logs/feedback", response_model=FeedbackOutput)
def feedback(data: FeedbackInput, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> Union[FeedbackOutput, HTTPException]:
    if Authorization.verify_token(credentials.credentials):
        from app.firebase import log_feedback
        try:
            doc = log_feedback(data.prediction_id, data.chosen_profile)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except _requests.exceptions.Timeout:
            raise HTTPException(
                status_code=503,
                detail="Firebase indisponible (timeout). Réessayez dans quelques secondes.",
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erreur Firebase: {e}")
        return FeedbackOutput(
            prediction_id=data.prediction_id,
            recommended_profile=doc["recommended_profile"],
            chosen_profile=doc["chosen_profile"],
            followed_recommendation=doc["followed_recommendation"],
        )
    else:
        raise HTTPException(status_code=401, detail="Invalid token")
    
@app.get("/logs/comparison", response_model=ComparisonOutput)
def comparison(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> Union[ComparisonOutput, HTTPException]:
    if Authorization.verify_token(credentials.credentials):
        from app.firebase import get_comparison_stats
        try:
            stats = get_comparison_stats()
        except _requests.exceptions.Timeout:
            raise HTTPException(
                status_code=503,
                detail="Firebase indisponible (timeout). Réessayez dans quelques secondes.",
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erreur Firebase: {e}")
        return ComparisonOutput(**stats)
    else:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/sessions/exercises", response_model=SessionOutput)
def session_exercises(data: SessionInput, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> Union[SessionOutput, HTTPException]:
    if Authorization.verify_token(credentials.credentials):
        return service.get_sessions(data)
    else:
        raise HTTPException(status_code=401, detail="Invalid token")
