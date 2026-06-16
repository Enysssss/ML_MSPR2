"""
Service Firebase Firestore — via REST HTTP (pas gRPC, compatible WSL2 et Railway).
"""
import glob
import os
import json
import base64
from datetime import datetime, timezone
from pathlib import Path

import requests
import google.auth.transport.requests
from google.oauth2 import service_account

_SCOPES = ["https://www.googleapis.com/auth/datastore"]
_creds = None
_project_id = None


def _get_creds():
    global _creds, _project_id

    if _creds is not None:
        return _creds, _project_id

    b64 = os.environ.get("FIREBASE_CREDENTIALS_B64")
    if b64:
        info = json.loads(base64.b64decode(b64).decode("utf-8"))
    else:
        # Cherche d'abord la variable d'env explicite
        cred_path = os.environ.get("FIREBASE_CREDENTIALS")
        if not cred_path:
            # Glob : trouve n'importe quel fichier firebase-adminsdk dans la racine du projet
            root = Path(__file__).parent.parent
            matches = glob.glob(str(root / "*firebase-adminsdk*.json"))
            if not matches:
                raise FileNotFoundError(
                    "Aucun fichier credentials Firebase trouvé. "
                    "Définissez FIREBASE_CREDENTIALS_B64 ou FIREBASE_CREDENTIALS, "
                    "ou placez le fichier *firebase-adminsdk*.json à la racine du projet."
                )
            cred_path = matches[0]
        with open(cred_path) as f:
            info = json.load(f)

    _project_id = info["project_id"]
    _creds = service_account.Credentials.from_service_account_info(info, scopes=_SCOPES)
    return _creds, _project_id


def _headers():
    creds, _ = _get_creds()
    creds.refresh(google.auth.transport.requests.Request())
    return {"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"}


def _base_url():
    _, project_id = _get_creds()
    return f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents"


def _to_firestore(value):
    if value is None:
        return {"nullValue": None}
    if isinstance(value, bool):
        return {"booleanValue": value}
    if isinstance(value, int):
        return {"integerValue": str(value)}
    if isinstance(value, float):
        return {"doubleValue": value}
    if isinstance(value, str):
        return {"stringValue": value}
    if isinstance(value, datetime):
        return {"timestampValue": value.isoformat().replace("+00:00", "Z")}
    if isinstance(value, dict):
        return {"mapValue": {"fields": {k: _to_firestore(v) for k, v in value.items()}}}
    return {"stringValue": str(value)}


def _from_firestore(fields: dict) -> dict:
    result = {}
    for k, v in fields.items():
        if "stringValue" in v:
            result[k] = v["stringValue"]
        elif "booleanValue" in v:
            result[k] = v["booleanValue"]
        elif "integerValue" in v:
            result[k] = int(v["integerValue"])
        elif "doubleValue" in v:
            result[k] = v["doubleValue"]
        elif "nullValue" in v:
            result[k] = None
        elif "timestampValue" in v:
            result[k] = v["timestampValue"]
        elif "mapValue" in v:
            result[k] = _from_firestore(v["mapValue"].get("fields", {}))
        else:
            result[k] = str(v)
    return result


def log_prediction(prediction_id: str, recommended_profile: str, confidence: float, inputs: dict) -> None:
    url = f"{_base_url()}/predictions/{prediction_id}"
    body = {
        "fields": {
            "recommended_profile": _to_firestore(recommended_profile),
            "confidence": _to_firestore(confidence),
            "inputs": _to_firestore(inputs),
            "chosen_profile": _to_firestore(None),
            "timestamp": _to_firestore(datetime.now(timezone.utc)),
        }
    }
    r = requests.patch(url, headers=_headers(), json=body, timeout=10)
    r.raise_for_status()


def log_feedback(prediction_id: str, chosen_profile: str) -> dict:
    url = f"{_base_url()}/predictions/{prediction_id}"
    r = requests.get(url, headers=_headers(), timeout=10)
    if r.status_code == 404:
        raise ValueError(f"Prédiction '{prediction_id}' introuvable.")
    r.raise_for_status()

    doc = _from_firestore(r.json().get("fields", {}))
    recommended_profile = doc.get("recommended_profile")
    followed = recommended_profile == chosen_profile

    body = {
        "fields": {
            **{k: _to_firestore(v) for k, v in doc.items()},
            "chosen_profile": _to_firestore(chosen_profile),
            "feedback_at": _to_firestore(datetime.now(timezone.utc)),
            "followed_recommendation": _to_firestore(followed),
        }
    }
    r2 = requests.patch(url, headers=_headers(), json=body, timeout=10)
    r2.raise_for_status()

    return {
        "recommended_profile": recommended_profile,
        "chosen_profile": chosen_profile,
        "followed_recommendation": followed,
    }


def get_comparison_stats() -> dict:
    url = f"{_base_url()}/predictions"
    r = requests.get(url, headers=_headers(), timeout=10)
    r.raise_for_status()

    docs = r.json().get("documents", [])
    total = 0
    followed = 0
    profile_stats: dict[str, dict] = {}

    for d in docs:
        fields = _from_firestore(d.get("fields", {}))
        chosen = fields.get("chosen_profile")
        if not chosen:
            continue
        rec = fields.get("recommended_profile")
        total += 1
        if fields.get("followed_recommendation"):
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
        "follow_rate_pct": round(followed / total * 100, 1) if total else 0.0,
        "by_profile": profile_stats,
    }
