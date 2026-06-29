# Conteneurisation — HealthAI Coach API

## Sommaire

1. [Vue d'ensemble](#1-vue-densemble)
2. [Dockerfile expliqué](#2-dockerfile-expliqué)
3. [Health Check](#3-health-check)
4. [Disponibilité de l'API](#4-disponibilité-de-lapi)
5. [Problème résolu — le training au build](#5-problème-résolu--le-training-au-build)
6. [Pourquoi pré-entraîner le modèle](#6-pourquoi-pré-entraîner-le-modèle)
7. [Cycle de vie du conteneur](#7-cycle-de-vie-du-conteneur)
8. [Déploiement Railway](#8-déploiement-railway)
9. [Variables d'environnement](#9-variables-denvironnement)
10. [Checklist de déploiement](#10-checklist-de-déploiement)

---

## 1. Vue d'ensemble

L'API HealthAI Coach est packagée dans un conteneur Docker **autonome** : une seule image contient le serveur FastAPI, le modèle ML pré-entraîné, et toutes les dépendances Python. Elle est conçue pour être déployée sur Railway (ou tout autre PaaS compatible Docker) sans configuration système particulière.

```
┌─────────────────────────────────────────────────────┐
│                  Conteneur Docker                   │
│                                                     │
│  ┌─────────────────┐     ┌──────────────────────┐  │
│  │   FastAPI        │     │  ml/models/          │  │
│  │   (uvicorn)      │────▶│  model.pkl (XGBoost) │  │
│  │   port 8000      │     │  encoder.pkl         │  │
│  └─────────────────┘     └──────────────────────┘  │
│           │                                         │
│  ┌─────────────────┐                                │
│  │  /health        │ ◀── HEALTHCHECK Docker         │
│  └─────────────────┘                                │
└─────────────────────────────────────────────────────┘
         │                        │
         ▼                        ▼
   PostgreSQL (externe)    Firebase (externe, optionnel)
```

---

## 2. Dockerfile expliqué

```dockerfile
FROM python:3.11-slim
```
Image de base légère (~50 MB vs ~900 MB pour l'image complète). Contient uniquement Python 3.11 et les outils système essentiels.

```dockerfile
WORKDIR /app
```
Tous les fichiers du projet seront dans `/app` à l'intérieur du conteneur. Évite les conflits de chemins.

```dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```
On copie **uniquement** `requirements.txt` en premier. Pourquoi ? Docker met en cache chaque instruction `RUN`/`COPY` sous forme de **layer**. Si le code change mais pas les dépendances, Docker réutilise le layer pip sans le recalculer — le build est beaucoup plus rapide.

```dockerfile
COPY . .
```
Copie tout le reste du projet (code source, `ml/models/`, etc.) dans `/app`.

```dockerfile
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
```
- `PYTHONDONTWRITEBYTECODE=1` : ne génère pas de fichiers `.pyc` (inutiles dans un conteneur)
- `PYTHONUNBUFFERED=1` : les logs Python s'affichent en temps réel dans Railway (sans cette option, les logs sont bufférisés et apparaissent en retard)

```dockerfile
EXPOSE 8000
```
Déclare que le conteneur écoute sur le port 8000. Indicatif uniquement — Railway mappe ce port automatiquement.

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1
```
Voir section suivante.

```dockerfile
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```
Commande de démarrage. `--host 0.0.0.0` est obligatoire pour que le port soit accessible depuis l'extérieur du conteneur (sans ça, uvicorn n'écoute que sur `localhost` interne et le conteneur est inaccessible).

---

## 3. Health Check

### Qu'est-ce qu'un health check ?

C'est une vérification automatique que Docker lance **à l'intérieur du conteneur** à intervalle régulier pour savoir si l'application est vivante et fonctionnelle. Si le check échoue plusieurs fois de suite, Docker marque le conteneur comme `unhealthy` — Railway peut alors le redémarrer automatiquement.

### Configuration

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1
```

| Paramètre | Valeur | Signification |
|-----------|--------|---------------|
| `--interval` | 30s | Vérifie toutes les 30 secondes |
| `--timeout` | 10s | Si pas de réponse en 10s → échec |
| `--start-period` | 15s | Laisse 15s au conteneur pour démarrer avant de commencer les checks |
| `--retries` | 3 | 3 échecs consécutifs → conteneur `unhealthy` |

### La route `/health`

```python
@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0.0"}
```

Cette route répond instantanément sans accès à la base de données ni au modèle ML. Elle confirme simplement que le processus uvicorn est en vie et capable de traiter des requêtes.

### États possibles du conteneur

```
démarrage → starting (15s de grâce)
              │
              ▼
          /health répond 200 → healthy ✅
              │
              ▼ (si échec 3× consécutifs)
          unhealthy ❌ → Railway redémarre le conteneur
```

---

## 4. Disponibilité de l'API

### Chargement du modèle au démarrage

Le modèle ML est chargé **une seule fois au démarrage** de l'application via le pattern Singleton :

```python
# app/main.py — exécuté au démarrage d'uvicorn
service = FitnessService()  # ← charge model.pkl et encoder.pkl ici

# app/service.py
class FitnessService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._model   = joblib.load(MODELS_DIR / "model.pkl")
            cls._instance._encoder = joblib.load(MODELS_DIR / "encoder.pkl")
        return cls._instance
```

**Conséquence :** la première requête `/recommend` répond aussi vite que les suivantes. Il n'y a pas de "cold start" par requête.

### Temps de démarrage typique

| Étape | Durée estimée |
|-------|---------------|
| Import des modules Python | ~2s |
| Chargement model.pkl (747 KB, XGBoost) | ~1s |
| Chargement encoder.pkl (608 bytes) | <0,1s |
| Uvicorn prêt à accepter des connexions | ~3-4s total |

Le `start-period` de 15s dans le HEALTHCHECK est donc largement suffisant.

### Dépendances externes

L'API dépend de services externes pour certaines routes :

| Route | Dépendance | Comportement si indisponible |
|-------|-----------|------------------------------|
| `/health` | Aucune | Toujours disponible |
| `/recommend` | PostgreSQL + Firebase | 500 si DB indispo, Firebase échoue silencieusement |
| `/nutrition/meals` | PostgreSQL | 500 si DB indispo |
| `/nutrition/calories` | Aucune | Toujours disponible (calcul pur) |
| `/sessions/exercises` | PostgreSQL | 500 si DB indispo |
| `/logs/feedback` | Firebase | 503 avec message explicite |
| `/logs/comparison` | Firebase | 503 avec message explicite |

---

## 5. Problème résolu — le training au build

### L'ancien Dockerfile (problématique)

```dockerfile
# ❌ AVANT — ce code était dans le Dockerfile
RUN python ml/data/generate_dataset.py && \
    python ml/src/training/train.py
```

### Pourquoi c'était lent

Le script `train.py` compare 3 algorithmes (Random Forest, Gradient Boosting, XGBoost) avec une recherche d'hyperparamètres exhaustive :

```python
RandomizedSearchCV(
    estimator=pipeline,
    param_distributions=param_grid,
    n_iter=50,    # 50 combinaisons testées
    cv=5,         # validation croisée 5 folds
    scoring="f1_macro",
)
```

Ça représente **50 × 5 = 250 entraînements** par modèle, soit **750 entraînements** au total pour les 3 modèles. Sur 2000 données avec feature engineering, ça prend **10 à 15 minutes**.

### Impact sur Railway

À chaque `git push` → Railway reconstruit l'image Docker → le training re-tournait → **15 minutes d'attente avant que le nouveau conteneur soit disponible**. Pendant ce temps, Railway gardait l'ancien conteneur actif, mais le déploiement était bloqué.

### La solution appliquée

Les modèles sont maintenant **entraînés une fois en local** et **commités dans git** :

```
ml/
└── models/
    ├── model.pkl    (747 KB — XGBoost, F1-macro=0.86)
    └── encoder.pkl  (608 bytes — LabelEncoder, 6 classes)
```

Le Dockerfile fait juste un `COPY . .` qui inclut ces fichiers — **aucun calcul au build**.

### Comparaison avant / après

| | Avant | Après |
|-|-------|-------|
| Durée du `docker build` | ~15 min | ~2 min (pip install uniquement) |
| Temps avant déploiement disponible | ~18 min | ~3 min |
| Training par deploy | Oui (inutile) | Non |
| Modèle reproductible | Non garanti (seed aléatoire) | Oui (même fichier commité) |

---

## 6. Pourquoi pré-entraîner le modèle

### Le modèle ne change pas à chaque déploiement

Le modèle ML apprend à partir de **données synthétiques générées avec une seed fixe** (`seed=42`). Ces données ne changent pas entre les déploiements — re-entraîner le modèle à chaque build produirait **exactement le même résultat**, pour un coût de 15 minutes.

### Quand faut-il re-entraîner ?

Re-entraîner est nécessaire uniquement dans ces cas :

- **Les données d'entraînement changent** (nouvelles données réelles, correction des données synthétiques)
- **L'algorithme ou les hyperparamètres changent** (modification de `train.py`)
- **Les features changent** (modification de `engineer.py`)
- **Un bug dans le preprocessing est corrigé**

Dans tous ces cas, la procédure est simple :

```bash
# 1. En local
python ml/data/generate_dataset.py
python ml/src/training/train.py

# 2. Committer les nouveaux modèles
git add ml/models/model.pkl ml/models/encoder.pkl
git commit -m "chore: re-entraînement modèle (raison)"
git push
```

### Avantages du modèle commité

- **Reproductibilité** : tous les environnements (local, Railway, CI) utilisent exactement le même modèle
- **Traçabilité** : `git log ml/models/model.pkl` montre quand et pourquoi le modèle a changé
- **Rapidité** : builds Docker de ~2 minutes au lieu de ~15 minutes
- **Stabilité** : pas de risque qu'un deploy change silencieusement les prédictions

---

## 7. Cycle de vie du conteneur

```
git push
    │
    ▼
Railway détecte le push
    │
    ▼
docker build (~2 min)
  ├── pip install -r requirements.txt
  └── COPY . .  (inclut model.pkl)
    │
    ▼
docker run
  └── uvicorn app.main:app --host 0.0.0.0 --port 8000
        │
        ▼
  Import de app.main
        │
        ▼
  FitnessService() → charge model.pkl + encoder.pkl (~1s)
        │
        ▼
  Uvicorn prêt (port 8000)
        │
        ▼
  HEALTHCHECK toutes les 30s → GET /health → {"status": "ok"}
        │
        ▼
  Conteneur healthy ✅ — Railway redirige le trafic
```

---

## 8. Déploiement Railway

Railway détecte automatiquement le `Dockerfile` à la racine du projet et construit l'image à chaque push sur `main`.

### Variables d'environnement à configurer dans Railway

Voir section suivante.

### Vérifier le déploiement

Après un push, dans les logs Railway :

```
✅ Build succeeded
✅ Deploy succeeded
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Si le HEALTHCHECK échoue, Railway affiche `unhealthy` et peut redémarrer le conteneur automatiquement.

---

## 9. Variables d'environnement

| Variable | Obligatoire | Description |
|----------|-------------|-------------|
| `DATABASE_URL` | Oui | URL PostgreSQL (`postgresql://user:pass@host:5432/db`) |
| `FIREBASE_CREDENTIALS_B64` | Non | Credentials Firebase en base64 (pour les logs de prédictions) |
| `FIREBASE_CREDENTIALS` | Non | Chemin vers le fichier JSON Firebase (alternatif au B64) |

Sans `DATABASE_URL`, les routes `/nutrition/meals` et `/sessions/exercises` retourneront des erreurs 500. La route `/health` et `/nutrition/calories` fonctionneront toujours.

Sans Firebase, les routes `/logs/feedback` et `/logs/comparison` retourneront des erreurs 503, mais le reste de l'API est intact.

---

## 10. Checklist de déploiement

### Déploiement normal (pas de changement de modèle)

- [ ] `git push origin main`
- [ ] Vérifier les logs Railway (build ~2 min, démarrage ~15s)
- [ ] Tester `GET /health` → `{"status": "ok"}`

### Déploiement avec nouveau modèle

- [ ] Modifier les données ou le code ML si nécessaire
- [ ] `python ml/data/generate_dataset.py`
- [ ] `python ml/src/training/train.py`
- [ ] Vérifier les métriques dans les logs (F1-macro, accuracy)
- [ ] `git add ml/models/model.pkl ml/models/encoder.pkl`
- [ ] `git commit -m "chore: re-entraînement modèle — [raison]"`
- [ ] `git push origin main`
- [ ] Vérifier les logs Railway
- [ ] Tester `POST /recommend` avec un cas de test connu
