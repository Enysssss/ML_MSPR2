from pydantic import BaseModel, Field, model_validator

class RecommendInput(BaseModel):
    age: int = Field(..., ge=18, le=65, description="Âge en années (18-65)")
    gender: str = Field(..., pattern="^(male|female)$", description="Genre : 'male' ou 'female'")
    weight_kg: float = Field(..., gt=30, lt=200, description="Poids en kg")
    height_cm: float = Field(..., gt=140, lt=215, description="Taille en cm")
    body_fat_pct: float = Field(..., ge=4, le=55, description="Taux de masse grasse (%)")
    resting_bpm: int = Field(..., ge=40, le=105, description="Fréquence cardiaque au repos (bpm)")
    experience_level: str = Field(
        ...,
        pattern="^(beginner|intermediate|advanced)$",
        description="Niveau d'expérience sportive",
    )

    @model_validator(mode="after")
    def check_bmi(self):
        bmi = self.weight_kg / (self.height_cm / 100) ** 2
        if bmi < 14 or bmi > 48:
            raise ValueError(
                f"IMC calculé ({bmi:.1f}) hors plage acceptable (14-48). "
                "Vérifiez poids_kg et taille_cm."
            )
        return self

    def gender_encoded(self) -> int:
        return 1 if self.gender == "male" else 0

    def experience_encoded(self) -> int:
        return {"beginner": 1, "intermediate": 2, "advanced": 3}[self.experience_level]


class ProgramOutput(BaseModel):
    sessions_per_week: int
    session_duration_min: int
    focus: str
    intensity: str
    weekly_volume_h: float
    progression: str
    nutrition_tip: str
    objective: str


class ProfileScore(BaseModel):
    profile: str
    confidence: float


class RecommendOutput(BaseModel):
    prediction_id: str
    profile: str
    confidence: float
    top_profiles: list[ProfileScore]
    bmi: float
    bmi_category: str
    program: ProgramOutput

VALID_PROFILES = [
    "perte_poids_debutant",
    "perte_poids_confirme",
    "prise_masse_debutant",
    "prise_masse_confirme",
    "amelioration_cardio",
    "maintien_bien_etre",
]

VALID_ALLERGENS = [
    "gluten", "lactose", "oeufs", "fruits_a_coque",
    "arachides", "soja", "poisson", "crustaces",
]

class CaloriesInput(BaseModel):
    age: int = Field(..., ge=18, le=65, description="Âge en années")
    gender: str = Field(..., pattern="^(male|female)$", description="'male' ou 'female'")
    weight_kg: float = Field(..., gt=30, lt=200, description="Poids actuel (kg)")
    height_cm: float = Field(..., gt=140, lt=215, description="Taille (cm)")
    target_weight_kg: float = Field(..., gt=30, lt=200, description="Poids cible (kg)")
    weeks_to_goal: int = Field(..., ge=1, le=104, description="Délai pour atteindre l'objectif (semaines)")
    profile: str = Field(..., description="Profil fitness choisi parmi les 6 disponibles")

    @model_validator(mode="after")
    def check_profile(self):
        if self.profile not in VALID_PROFILES:
            raise ValueError(f"Profil invalide. Valeurs acceptées : {VALID_PROFILES}")
        return self

class MealItem(BaseModel):
    name: str
    meal_type: str
    calories_kcal: float
    proteins_g: float
    carbs_g: float
    fats_g: float
    allergens: list[str]

class MealsInput(BaseModel):
    profile: str = Field(..., description="Un des 6 profils fitness")
    allergens_to_exclude: list[str] = Field(
        default=[],
        description=f"Allergènes à exclure. Valeurs possibles : {VALID_ALLERGENS}",
    )
    meal_type: str | None = Field(
        default=None,
        description="Filtrer par type : breakfast, lunch, dinner, snack. Null = tous types.",
    )

    @model_validator(mode="after")
    def validate_fields(self):
        if self.profile not in VALID_PROFILES:
            raise ValueError(f"Profil invalide. Valeurs acceptées : {VALID_PROFILES}")
        unknown = [a for a in self.allergens_to_exclude if a not in VALID_ALLERGENS]
        if unknown:
            raise ValueError(f"Allergènes inconnus : {unknown}. Valeurs acceptées : {VALID_ALLERGENS}")
        if self.meal_type and self.meal_type not in {"breakfast", "lunch", "dinner", "snack"}:
            raise ValueError("meal_type doit être : breakfast, lunch, dinner ou snack")
        return self

class MealsOutput(BaseModel):
    profile: str
    allergens_excluded: list[str]
    meal_type_filter: str | None
    count: int
    meals: list[MealItem]

class CaloriesOutput(BaseModel):
    bmr: float = Field(description="Métabolisme de base Harris-Benedict (kcal/j)")
    tdee: float = Field(description="Dépense énergétique totale avec activité (kcal/j)")
    daily_adjustment: float = Field(description="Déficit ou surplus journalier calculé (kcal/j)")
    daily_calories_target: float = Field(description="Objectif calorique final (kcal/j)")
    weekly_change_kg: float = Field(description="Variation de poids attendue par semaine (kg)")
    total_change_kg: float = Field(description="Variation totale à réaliser (kg)")
    goal_type: str = Field(description="'deficit' ou 'surplus'")
    protein_target_g: float = Field(description="Apport protéique recommandé (g/j)")
    note: str = Field(description="Conseil personnalisé selon le profil")

class SessionExerciseItem(BaseModel):
    order_num: int
    exercise_name: str
    body_part: str | None
    category: str | None
    equipment: str | None
    sets: int | None
    reps: str | None
    rest_sec: int | None
    notes: str | None

class WorkoutSessionOutput(BaseModel):
    session_id: int
    name: str
    profile: str
    session_type: str | None
    total_duration_min: int | None
    difficulty: str | None
    description: str | None
    objective: str | None
    exercises: list[SessionExerciseItem]

class FeedbackInput(BaseModel):
    prediction_id: str = Field(..., description="ID retourné par /recommend")
    chosen_profile: str = Field(..., description="Profil finalement choisi par l'utilisateur")

    @model_validator(mode="after")
    def validate_chosen(self):
        if self.chosen_profile not in VALID_PROFILES:
            raise ValueError(f"Profil invalide. Valeurs acceptées : {VALID_PROFILES}")
        return self

class FeedbackOutput(BaseModel):
    prediction_id: str
    recommended_profile: str
    chosen_profile: str
    followed_recommendation: bool

class ComparisonOutput(BaseModel):
    total_with_feedback: int
    followed_recommendation: int
    follow_rate_pct: float
    by_profile: dict

VALID_BODY_REGIONS = [
    "bras_droit", "bras_gauche", "bras",
    "jambe_droite", "jambe_gauche", "jambes",
    "dos", "epaules", "abdominaux", "pied", "nuque",
]

BODY_REGION_TO_PARTS: dict[str, list[str]] = {
    "bras_droit":   ["Biceps", "Triceps", "Épaules", "Avant-bras"],
    "bras_gauche":  ["Biceps", "Triceps", "Épaules", "Avant-bras"],
    "bras":         ["Biceps", "Triceps", "Épaules", "Avant-bras"],
    "jambe_droite": ["Quadriceps", "Ischio-jambiers", "Fessiers", "Mollets"],
    "jambe_gauche": ["Quadriceps", "Ischio-jambiers", "Fessiers", "Mollets"],
    "jambes":       ["Quadriceps", "Ischio-jambiers", "Fessiers", "Mollets"],
    "dos":          ["Dos"],
    "epaules":      ["Épaules"],
    "abdominaux":   ["Abdominaux"],
    "pied":         ["Mollets"],
    "nuque":        ["Trapèzes"],
}

class SessionInput(BaseModel):
    profile: str = Field(..., description="Un des 6 profils fitness")
    session_type: str | None = Field(
        default=None,
        description="Filtrer par type : push, pull, legs, full_body, hiit, cardio, stretching, mixed. Null = tous.",
    )
    body_parts_to_exclude: list[str] = Field(
        default=[],
        description=f"Zones corporelles à ne pas solliciter. Valeurs possibles : {VALID_BODY_REGIONS}",
    )

    @model_validator(mode="after")
    def validate_fields(self):
        if self.profile not in VALID_PROFILES:
            raise ValueError(f"Profil invalide. Valeurs acceptées : {VALID_PROFILES}")
        unknown = [r for r in self.body_parts_to_exclude if r not in VALID_BODY_REGIONS]
        if unknown:
            raise ValueError(f"Régions inconnues : {unknown}. Valeurs acceptées : {VALID_BODY_REGIONS}")
        return self

class SessionOutput(BaseModel):
    profile: str
    session_type_filter: str | None
    body_parts_excluded: list[str]
    count: int
    sessions: list[WorkoutSessionOutput]

class NutritionInput(BaseModel):
    age: int = Field(..., ge=18, le=65)
    poids_kg: float = Field(..., gt=20, lt=300)
    taille_cm: float = Field(..., gt=100, lt=250)
    taux_masse_grasse: float = Field(..., ge=4.0, le=55.0)

class NutritionOutput(BaseModel):
    imc: float
    imc_categorie: str
    label: str
    confidence: float
    message: str
