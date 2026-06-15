"""
Service Firebase Firestore — logging des prédictions et feedback utilisateur.
"""
import os
from pathlib import Path
from datetime import datetime, timezone

import firebase_admin
from firebase_admin import credentials, firestore

_db = None


def get_db():
    global _db
    if _db is not None:
        return _db

    if not firebase_admin._apps:
        cred_path = os.environ.get(
            "FIREBASE_CREDENTIALS",
            str(Path(__file__).parent.parent / "mlmspr2-firebase-adminsdk-fbsvc-9503215706.json"),
        )
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)

    _db = firestore.client()
    return _db


def log_prediction(prediction_id: str, recommended_profile: str, confidence: float, inputs: dict) -> None:
    """Enregistre une prédiction ML dans Firestore."""
    db = get_db()
    db.collection("predictions").document(prediction_id).set({
        "recommended_profile": recommended_profile,
        "confidence": confidence,
        "inputs": inputs,
        "chosen_profile": None,
        "timestamp": datetime.now(timezone.utc),
    })


def log_feedback(prediction_id: str, chosen_profile: str) -> dict:
    """
    Enregistre le profil choisi par l'utilisateur après la recommandation.
    Retourne le document mis à jour.
    """
    db = get_db()
    ref = db.collection("predictions").document(prediction_id)
    doc = ref.get()
    if not doc.exists:
        raise ValueError(f"Prédiction '{prediction_id}' introuvable.")

    ref.update({
        "chosen_profile": chosen_profile,
        "feedback_at": datetime.now(timezone.utc),
        "followed_recommendation": doc.get("recommended_profile") == chosen_profile,
    })
    return ref.get().to_dict()


def get_comparison_stats() -> dict:
    """
    Calcule les stats de comparaison recommandé vs choisi.
    Retourne uniquement les prédictions avec feedback.
    """
    db = get_db()
    docs = db.collection("predictions").where("chosen_profile", "!=", None).stream()

    total = 0
    followed = 0
    profile_stats: dict[str, dict] = {}

    for doc in docs:
        d = doc.to_dict()
        rec = d.get("recommended_profile")
        chosen = d.get("chosen_profile")
        total += 1
        if d.get("followed_recommendation"):
            followed += 1

        if rec not in profile_stats:
            profile_stats[rec] = {"recommended": 0, "followed": 0, "chosen_instead": {}}
        profile_stats[rec]["recommended"] += 1
        if rec == chosen:
            profile_stats[rec]["followed"] += 1
        else:
            profile_stats[rec]["chosen_instead"][chosen] = (
                profile_stats[rec]["chosen_instead"].get(chosen, 0) + 1
            )

    return {
        "total_with_feedback": total,
        "followed_recommendation": followed,
        "follow_rate_pct": round(followed / total * 100, 1) if total else 0,
        "by_profile": profile_stats,
    }
