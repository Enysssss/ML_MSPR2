# HealthAI Coach — API ML

API FastAPI de recommandation de programmes sportifs personnalisés par Machine Learning.  
Un profil utilisateur (âge, poids, IMC…) entre, un programme fitness adapté sort.

**Stack** : FastAPI · scikit-learn / XGBoost · MLflow · pandas · Pydantic · PostgreSQL

## Dataset

Le dataset (`ml/data/processed/healthai_dataset.csv`) est fourni directement dans le repo.  
Il contient ~2000 profils utilisateurs synthétiques générés à partir de distributions cliniques publiées (ACSM, OMS, NHANES) avec des corrélations physiologiques réalistes (IMC/masse grasse, âge/BPM, etc.).  
La graine aléatoire est fixe (`seed=42`), le script de génération est disponible dans `ml/data/generate_dataset.py` pour référence ou reproduction.

---

## Lancer le projet (dans l'ordre)

### 1. Créer l'environnement virtuel et installer les dépendances

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configurer la base de données

Copier le fichier d'exemple et renseigner l'URL de connexion PostgreSQL :

```bash
cp .env.example .env
```

Éditer `.env` :

```
DATABASE_URL=postgresql://user:password@host:port/healthai
```

Puis charger les variables :

```bash
source .env  # ou : export $(cat .env | xargs)
```

### 3. Entraîner le modèle

```bash
python ml/src/training/train.py
```

> Entraîne et compare RF / GBM / XGBoost, sauvegarde le meilleur modèle via joblib + MLflow.

### 4. Lancer l'API

```bash
uvicorn app.main:app --reload
```

### 5. Accéder au Swagger

Ouvrir dans le navigateur :

```
http://127.0.0.1:8000/docs
```

---

## Endpoints principaux

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/health` | Statut de l'API |
| POST | `/recommend` | Recommandation fitness personnalisée (exercices + repas issus de la BDD) |
| GET | `/profiles` | Liste des 6 profils fitness disponibles |
