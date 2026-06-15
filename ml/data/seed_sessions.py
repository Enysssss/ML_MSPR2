"""
Seed — tables exercises, workout_sessions, session_exercises.
Sessions construites selon les guidelines ACSM 2022 par profil fitness.
"""
import os
import psycopg2
import psycopg2.extras

DATABASE_URL = os.environ["DATABASE_URL"]

# ---------------------------------------------------------------------------
# EXERCICES
# ---------------------------------------------------------------------------
EXERCISES = [
    # ── FORCE / COMPOUND ────────────────────────────────────────────────────
    {"name": "Squat barre", "body_part": "Quadriceps", "category": "Strength", "difficulty": "intermediaire", "equipment": "barre", "description": "Squat avec barre sur les trapèzes, descente jusqu'aux cuisses parallèles au sol."},
    {"name": "Deadlift roumain", "body_part": "Ischio-jambiers", "category": "Strength", "difficulty": "intermediaire", "equipment": "barre", "description": "Descente contrôlée de la barre le long des jambes, dos droit, hanches en arrière."},
    {"name": "Développé couché barre", "body_part": "Pectoraux", "category": "Strength", "difficulty": "intermediaire", "equipment": "barre", "description": "Allongé sur le banc, descente de la barre jusqu'à effleurer la poitrine, poussée explosive."},
    {"name": "Rowing barre", "body_part": "Dos", "category": "Strength", "difficulty": "intermediaire", "equipment": "barre", "description": "Buste penché à 45°, tirer la barre vers le nombril en serrant les omoplates."},
    {"name": "Développé militaire", "body_part": "Épaules", "category": "Strength", "difficulty": "intermediaire", "equipment": "barre", "description": "Pousser la barre au-dessus de la tête depuis les clavicules, corps gainé."},
    {"name": "Soulevé de terre", "body_part": "Dos", "category": "Strength", "difficulty": "avance", "equipment": "barre", "description": "Soulever la barre depuis le sol jusqu'à la position debout, dos plat tout au long du mouvement."},
    {"name": "Tractions pronation", "body_part": "Dos", "category": "Strength", "difficulty": "intermediaire", "equipment": "barre_fixe", "description": "Tirer le corps jusqu'au menton au-dessus de la barre, descente contrôlée."},
    {"name": "Dips lestés", "body_part": "Triceps", "category": "Strength", "difficulty": "avance", "equipment": "barre_parallele", "description": "Descendre jusqu'à 90° aux coudes, pousser pour revenir. Lest supplémentaire si nécessaire."},
    {"name": "Leg press", "body_part": "Quadriceps", "category": "Strength", "difficulty": "debutant", "equipment": "machine", "description": "Pousser la plateforme avec les deux pieds, genoux à 90° au bas du mouvement."},
    {"name": "Curl biceps haltères", "body_part": "Biceps", "category": "Strength", "difficulty": "debutant", "equipment": "halteres", "description": "Flexion alternée des avant-bras, coudes stables contre le corps."},
    {"name": "Extension triceps poulie haute", "body_part": "Triceps", "category": "Strength", "difficulty": "debutant", "equipment": "machine", "description": "Pousser la corde vers le bas en dépliant les avant-bras, coudes fixes."},
    {"name": "Élévations latérales haltères", "body_part": "Épaules", "category": "Strength", "difficulty": "debutant", "equipment": "halteres", "description": "Monter les bras à l'horizontale en gardant les coudes légèrement fléchis."},
    {"name": "Fentes marchées haltères", "body_part": "Quadriceps", "category": "Strength", "difficulty": "intermediaire", "equipment": "halteres", "description": "Alterner les jambes en avançant, genou arrière frôle le sol."},
    {"name": "Hip thrust barre",           "body_part": "Fessiers",  "category": "Strength", "difficulty": "intermediaire", "equipment": "barre",    "description": "Poussée des hanches vers le haut, dos appuyé sur le banc, barre sur les hanches."},
    {"name": "Développé couché haltères", "body_part": "Pectoraux", "category": "Strength", "difficulty": "debutant",      "equipment": "halteres", "description": "Variante aux haltères du développé couché, amplitude plus grande."},
    {"name": "Tirage horizontal poulie basse", "body_part": "Dos", "category": "Strength", "difficulty": "debutant", "equipment": "machine", "description": "Tirer la poignée vers le ventre en gardant le dos droit et les coudes proches du corps."},
    {"name": "Squat goblet haltère", "body_part": "Quadriceps", "category": "Strength", "difficulty": "debutant", "equipment": "halteres", "description": "Squat tenu avec un seul haltère devant la poitrine, idéal pour les débutants."},
    {"name": "Curl marteau haltères", "body_part": "Biceps", "category": "Strength", "difficulty": "debutant", "equipment": "halteres", "description": "Flexion des avant-bras en prise neutre (pouce vers le haut)."},
    {"name": "Rowing unilatéral haltère", "body_part": "Dos", "category": "Strength", "difficulty": "debutant", "equipment": "halteres", "description": "Appui sur le banc, tirer l'haltère vers la hanche en engageant le grand dorsal."},

    # ── POIDS DE CORPS ──────────────────────────────────────────────────────
    {"name": "Pompes classiques", "body_part": "Pectoraux", "category": "Strength", "difficulty": "debutant", "equipment": "poids_corps", "description": "Corps gainé, descendre jusqu'à effleurer le sol, pousser."},
    {"name": "Gainage planche", "body_part": "Abdominaux", "category": "Strength", "difficulty": "debutant", "equipment": "poids_corps", "description": "Corps aligné sur les avant-bras et les orteils, maintenir la position."},
    {"name": "Mountain climbers", "body_part": "Abdominaux", "category": "Cardio", "difficulty": "intermediaire", "equipment": "poids_corps", "description": "En position de pompe, ramener alternativement les genoux vers la poitrine rapidement."},
    {"name": "Burpees", "body_part": "Corps entier", "category": "Plyometrics", "difficulty": "intermediaire", "equipment": "poids_corps", "description": "Pompe au sol, saut avec les mains en l'air. Enchaîner sans pause."},
    {"name": "Jump squats", "body_part": "Quadriceps", "category": "Plyometrics", "difficulty": "intermediaire", "equipment": "poids_corps", "description": "Squat suivi d'un saut explosif, atterrir en douceur et enchaîner."},
    {"name": "Crunchs abdominaux", "body_part": "Abdominaux", "category": "Strength", "difficulty": "debutant", "equipment": "poids_corps", "description": "Décoller les omoplates du sol en contractant les abdos, ne pas tirer sur la nuque."},
    {"name": "Chaise murale", "body_part": "Quadriceps", "category": "Strength", "difficulty": "debutant", "equipment": "poids_corps", "description": "Dos contre le mur, cuisses parallèles au sol, maintenir la position."},
    {"name": "Superman", "body_part": "Dos", "category": "Strength", "difficulty": "debutant", "equipment": "poids_corps", "description": "Allongé face au sol, soulever simultanément les bras et les jambes."},
    {"name": "High knees", "body_part": "Corps entier", "category": "Cardio", "difficulty": "debutant", "equipment": "poids_corps", "description": "Course sur place en montant les genoux le plus haut possible."},
    {"name": "Jumping jacks", "body_part": "Corps entier", "category": "Cardio", "difficulty": "debutant", "equipment": "poids_corps", "description": "Sauts avec écartement simultané des jambes et des bras."},

    # ── CARDIO ──────────────────────────────────────────────────────────────
    {"name": "Course à pied zone 2", "body_part": "Corps entier", "category": "Cardio", "difficulty": "debutant", "equipment": "aucun", "description": "Course à allure conversationnelle (60-70% FCmax), maintien de l'endurance de base."},
    {"name": "Vélo stationnaire zone 2", "body_part": "Corps entier", "category": "Cardio", "difficulty": "debutant", "equipment": "velo", "description": "Pédalage à résistance modérée, 60-70% FCmax, effort soutenu sans essoufflement."},
    {"name": "Intervalles course 3min/2min", "body_part": "Corps entier", "category": "Cardio", "difficulty": "intermediaire", "equipment": "aucun", "description": "3 min à 80-85% FCmax, 2 min récupération active. Répéter 6 fois."},
    {"name": "Rameur zone 3", "body_part": "Corps entier", "category": "Cardio", "difficulty": "intermediaire", "equipment": "rameur", "description": "Effort soutenu à 70-80% FCmax, technique : jambes, buste, bras dans cet ordre."},
    {"name": "Corde à sauter", "body_part": "Corps entier", "category": "Cardio", "difficulty": "debutant", "equipment": "corde", "description": "Saut à la corde, rythme modéré. Variante : doubles sauts pour l'intensité."},
    {"name": "Marche rapide inclinée", "body_part": "Corps entier", "category": "Cardio", "difficulty": "debutant", "equipment": "tapis", "description": "Marche à 5-6 km/h avec une inclinaison de 8-10%, excellent cardio low-impact."},
    {"name": "Natation crawl", "body_part": "Corps entier", "category": "Cardio", "difficulty": "intermediaire", "equipment": "piscine", "description": "Nager en crawl à allure modérée, excellent cardio sans impact articulaire."},

    # ── STRETCHING / MOBILITÉ ───────────────────────────────────────────────
    {"name": "Étirement ischio-jambiers debout", "body_part": "Ischio-jambiers", "category": "Stretching", "difficulty": "debutant", "equipment": "aucun", "description": "Jambe tendue posée sur un support à hauteur de hanche, incliner le buste vers l'avant."},
    {"name": "Pigeon yoga (fessiers)", "body_part": "Fessiers", "category": "Stretching", "difficulty": "debutant", "equipment": "tapis", "description": "Position du pigeon au sol, maintenir 45-60 secondes de chaque côté."},
    {"name": "Étirement quadriceps debout", "body_part": "Quadriceps", "category": "Stretching", "difficulty": "debutant", "equipment": "aucun", "description": "Plier le genou, attraper la cheville derrière soi, hanches droites."},
    {"name": "Rotation thoracique au sol", "body_part": "Dos", "category": "Stretching", "difficulty": "debutant", "equipment": "tapis", "description": "Allongé sur le côté, genoux fléchis, ouvrir le bras supérieur vers l'arrière."},
    {"name": "Cat-Cow (mobilité lombaire)", "body_part": "Dos", "category": "Stretching", "difficulty": "debutant", "equipment": "tapis", "description": "À quatre pattes, alterner l'arrondi et le creux du dos en respirant."},
    {"name": "Salutation au soleil (Yoga)", "body_part": "Corps entier", "category": "Stretching", "difficulty": "debutant", "equipment": "tapis", "description": "Enchaînement de postures de yoga fluidifiant tout le corps, 5 cycles."},
    {"name": "Foam roller dos et cuisses", "body_part": "Corps entier", "category": "Stretching", "difficulty": "debutant", "equipment": "foam_roller", "description": "Auto-massage myofascial : rouler lentement sur les zones tendues, 30-60 sec par zone."},
]

# ---------------------------------------------------------------------------
# SESSIONS (nom, profil, type, durée, difficulté, description, objectif)
# + exercises_list = [(nom_exercice, sets, reps, rest_sec, notes)]
# ---------------------------------------------------------------------------
SESSIONS = [
    # ════════════════════════════════════════════════════════════
    # PRISE DE MASSE — CONFIRMÉ (split push/pull/legs)
    # ════════════════════════════════════════════════════════════
    {
        "name": "Push Day — Pectoraux / Épaules / Triceps",
        "profile": "prise_masse_confirme",
        "session_type": "push",
        "total_duration_min": 65,
        "difficulty": "avance",
        "description": "Séance axée sur les muscles pousseurs. Charges lourdes, tempo contrôlé.",
        "objective": "Hypertrophie pectoraux, épaules antérieures et triceps.",
        "exercises": [
            ("Développé couché barre",      4, "6-8",  120, "Surcharge progressive — ajouter 2.5 kg si 8 reps réussies"),
            ("Développé couché haltères",   3, "10-12", 90, "Amplitude maximale pour étirement des pectoraux"),
            ("Développé militaire",         4, "8-10",  90, "Strict, pas de rebond avec les jambes"),
            ("Élévations latérales haltères", 3, "12-15", 60, "Monter lentement, descendre en 3 secondes"),
            ("Dips lestés",                 3, "8-10", 120, "Poids de corps + lest si possible"),
            ("Extension triceps poulie haute", 3, "12-15", 60, "Full extension, serrer les triceps en bas"),
        ],
    },
    {
        "name": "Pull Day — Dos / Biceps / Trapèzes",
        "profile": "prise_masse_confirme",
        "session_type": "pull",
        "total_duration_min": 65,
        "difficulty": "avance",
        "description": "Séance axée sur les muscles tireurs. Focus grand dorsal et biceps.",
        "objective": "Épaisseur et largeur du dos, volume des biceps.",
        "exercises": [
            ("Tractions pronation",         4, "6-8",  120, "Lest si > 8 reps en poids de corps"),
            ("Rowing barre",                4, "8-10", 120, "Buste à 45°, coudes écartés"),
            ("Tirage horizontal poulie basse", 3, "10-12", 90, "Serrer les omoplates en fin de mouvement"),
            ("Rowing unilatéral haltère",   3, "10-12", 75, "Dos plat, ne pas twister le buste"),
            ("Curl biceps haltères",        3, "10-12", 75, "Supination en fin de mouvement"),
            ("Curl marteau haltères",       3, "12",    60, "Prise neutre, coudes fixes"),
        ],
    },
    {
        "name": "Leg Day — Quadriceps / Ischio / Fessiers",
        "profile": "prise_masse_confirme",
        "session_type": "legs",
        "total_duration_min": 70,
        "difficulty": "avance",
        "description": "Séance jambes complète. La plus exigeante de la semaine — ne pas la zapper.",
        "objective": "Volume et force des membres inférieurs. Stimulation hormonale maximale.",
        "exercises": [
            ("Squat barre",                 5, "5-6",  180, "Périodisation : semaine A force (5×5), semaine B hypertrophie (4×10)"),
            ("Leg press",                   3, "12-15", 90, "Pieds écartés largeur d'épaules, genoux dans l'axe des orteils"),
            ("Deadlift roumain",            3, "10-12", 90, "Barre près des jambes, descendre jusqu'à mi-tibia"),
            ("Fentes marchées haltères",    3, "10/jambe", 75, "Pas long, torse droit"),
            ("Hip thrust barre",            3, "12",    75, "Full extension des hanches en haut, serrer les fessiers"),
            ("Gainage planche",             3, "45 sec", 45, "Corps parfaitement aligné"),
        ],
    },
    {
        "name": "Full Body — Récupération active / Volume",
        "profile": "prise_masse_confirme",
        "session_type": "full_body",
        "total_duration_min": 60,
        "difficulty": "intermediaire",
        "description": "Séance de volume plus légère en fin de semaine. Répéter les patrons moteurs.",
        "objective": "Maintien du volume hebdomadaire sans surcharger la récupération.",
        "exercises": [
            ("Squat goblet haltère",        3, "15",    60, "Charge modérée, focus technique"),
            ("Développé couché haltères",   3, "12-15", 75, "Amplitude complète"),
            ("Rowing unilatéral haltère",   3, "12",    60, "Tempo 2-1-2"),
            ("Développé militaire",         3, "12",    75, "Haltères ou barre, charges moyennes"),
            ("Curl biceps haltères",        2, "15",    60, "Pump — pas de repos excessif"),
            ("Extension triceps poulie haute", 2, "15", 60, "Pump — enchainer avec biceps en superset"),
            ("Crunchs abdominaux",          3, "20",    45, "Lent et contrôlé"),
        ],
    },

    # ════════════════════════════════════════════════════════════
    # PRISE DE MASSE — DÉBUTANT (full body 3x/semaine)
    # ════════════════════════════════════════════════════════════
    {
        "name": "Full Body A — Débutant Prise de Masse",
        "profile": "prise_masse_debutant",
        "session_type": "full_body",
        "total_duration_min": 50,
        "difficulty": "debutant",
        "description": "Séance A du programme full body. Mouvements fondamentaux, charges progressives.",
        "objective": "Apprentissage des mouvements de base. +2.5 kg à chaque séance si possible.",
        "exercises": [
            ("Squat barre",                 3, "8-12", 120, "Priorité : technique parfaite avant d'augmenter la charge"),
            ("Développé couché barre",      3, "8-12", 120, "Barre en ligne avec les yeux, descente contrôlée"),
            ("Rowing barre",                3, "8-12", 120, "Dos plat, tirer vers le nombril"),
            ("Gainage planche",             3, "30 sec", 60, "Ne pas laisser les hanches tomber"),
            ("Curl biceps haltères",        2, "12",    60, "Découverte du mouvement"),
        ],
    },
    {
        "name": "Full Body B — Débutant Prise de Masse",
        "profile": "prise_masse_debutant",
        "session_type": "full_body",
        "total_duration_min": 50,
        "difficulty": "debutant",
        "description": "Séance B — alterner avec la séance A. Patrons moteurs complémentaires.",
        "objective": "Renforcer les muscles antagonistes, équilibrer le développement.",
        "exercises": [
            ("Soulevé de terre",            3, "8",    180, "Commencer léger — la technique prime. Dos plat absolu."),
            ("Développé couché haltères",   3, "10-12", 90, "Plus accessible que la barre pour débuter"),
            ("Tirage horizontal poulie basse", 3, "10-12", 90, "Garder les coudes près du corps"),
            ("Développé militaire",         3, "10-12", 90, "Haltères recommandés pour les débutants"),
            ("Squat goblet haltère",        2, "15",    60, "Bonne alternative pour travailler la mobilité"),
        ],
    },
    {
        "name": "Full Body C — Accessoires Débutant",
        "profile": "prise_masse_debutant",
        "session_type": "full_body",
        "total_duration_min": 45,
        "difficulty": "debutant",
        "description": "Séance C — focus sur les muscles secondaires et la stabilité.",
        "objective": "Renforcer les muscles stabilisateurs, prévenir les blessures.",
        "exercises": [
            ("Leg press",                   3, "12-15", 75, "Alternative au squat barre si douleur ou manque de mobilité"),
            ("Pompes classiques",           3, "max",   75, "Jusqu'à l'échec technique"),
            ("Rowing unilatéral haltère",   3, "12",    75, "Focus sur le ressenti dans le dos"),
            ("Fentes marchées haltères",    3, "10/jambe", 75, "Maintenir l'équilibre"),
            ("Élévations latérales haltères", 3, "15",  60, "Léger, focus sur la brûlure"),
            ("Crunchs abdominaux",          3, "20",    45, "Pas d'élan"),
        ],
    },

    # ════════════════════════════════════════════════════════════
    # PERTE DE POIDS — CONFIRMÉ (HIIT + circuit training)
    # ════════════════════════════════════════════════════════════
    {
        "name": "HIIT Métabolique — Brûlage Calorique Max",
        "profile": "perte_poids_confirme",
        "session_type": "hiit",
        "total_duration_min": 45,
        "difficulty": "avance",
        "description": "30 sec effort / 30 sec repos × 10 rounds. Intensité maximale sur chaque round.",
        "objective": "Brûler 400-500 kcal, créer un effet afterburn (EPOC).",
        "exercises": [
            ("Burpees",           5, "30 sec effort / 30 sec repos", 30, "Répétitions maximales sur le temps imparti"),
            ("Jump squats",       5, "30 sec effort / 30 sec repos", 30, "Atterrir silencieusement, genoux dans l'axe"),
            ("Mountain climbers", 5, "30 sec effort / 30 sec repos", 30, "Rythme maximal, ventre rentré"),
            ("High knees",        5, "30 sec effort / 30 sec repos", 30, "Genoux à hauteur de hanche minimum"),
            ("Burpees",           5, "30 sec effort / 30 sec repos", 30, "Second passage — maintenir la qualité"),
        ],
    },
    {
        "name": "Circuit Musculaire — Remodelage Corporel",
        "profile": "perte_poids_confirme",
        "session_type": "circuit",
        "total_duration_min": 50,
        "difficulty": "avance",
        "description": "4 tours du circuit complet. Repos de 90 sec entre les tours seulement.",
        "objective": "Préserver la masse musculaire en déficit calorique.",
        "exercises": [
            ("Squat barre",          4, "15",   0,  "Enchaîner directement au suivant — pas de repos intra-circuit"),
            ("Rowing barre",         4, "15",   0,  "Garder un rythme soutenu"),
            ("Développé militaire",  4, "15",   0,  "Haltères légers à modérés"),
            ("Fentes marchées haltères", 4, "12/jambe", 0, "Rythme continu"),
            ("Mountain climbers",    4, "30 sec", 90, "Fin de tour — repos 90 sec avant de recommencer"),
        ],
    },
    {
        "name": "Cardio HIIT Vélo — Zone 3-4",
        "profile": "perte_poids_confirme",
        "session_type": "cardio",
        "total_duration_min": 40,
        "difficulty": "avance",
        "description": "Intervals sur vélo stationnaire. Alterner effort maximal et récupération active.",
        "objective": "Améliorer le VO2max et brûler des graisses en post-effort.",
        "exercises": [
            ("Vélo stationnaire zone 2",    1, "10 min échauffement", 0,  "60-65% FCmax"),
            ("Intervalles course 3min/2min", 6, "3 min sprint / 2 min récup", 0, "Sur vélo : résistance maximale / minimale"),
            ("Vélo stationnaire zone 2",    1, "10 min retour au calme", 0, "Récupération active 55-60% FCmax"),
        ],
    },
    {
        "name": "Force + Cardio Combinés",
        "profile": "perte_poids_confirme",
        "session_type": "mixed",
        "total_duration_min": 55,
        "difficulty": "avance",
        "description": "Alternance blocs de force (5 min) et cardio (3 min). Format EDT.",
        "objective": "Maximiser la dépense calorique tout en maintenant la masse musculaire.",
        "exercises": [
            ("Développé couché barre",  3, "8",    60, "Bloc force — charges modérées à lourdes"),
            ("Corde à sauter",          3, "3 min", 0,  "Cardio intermédiaire — rythme élevé"),
            ("Squat barre",             3, "10",   60, "Bloc force"),
            ("High knees",              3, "3 min", 0,  "Cardio intermédiaire"),
            ("Rowing barre",            3, "10",   60, "Bloc force"),
            ("Jumping jacks",           3, "3 min", 0,  "Cardio final"),
        ],
    },

    # ════════════════════════════════════════════════════════════
    # PERTE DE POIDS — DÉBUTANT (cardio doux + renforcement)
    # ════════════════════════════════════════════════════════════
    {
        "name": "Cardio Doux — Zone 2 Débutant",
        "profile": "perte_poids_debutant",
        "session_type": "cardio",
        "total_duration_min": 40,
        "difficulty": "debutant",
        "description": "Marche rapide ou vélo à intensité modérée. On doit pouvoir tenir une conversation.",
        "objective": "Brûler des graisses en zone 2, habituer le corps à l'effort continu.",
        "exercises": [
            ("Marche rapide inclinée", 1, "10 min échauffement", 0,   "Inclinaison 5%, vitesse 4 km/h"),
            ("Marche rapide inclinée", 1, "20 min effort",       0,   "Inclinaison 8-10%, vitesse 5-5.5 km/h"),
            ("Marche rapide inclinée", 1, "10 min retour calme", 0,   "Inclinaison 0%, étirements finaux"),
            ("Étirement quadriceps debout", 2, "30 sec/côté",    30,  "Fin de séance"),
            ("Étirement ischio-jambiers debout", 2, "30 sec/côté", 30, "Fin de séance"),
        ],
    },
    {
        "name": "Renforcement Corps Entier — Débutant",
        "profile": "perte_poids_debutant",
        "session_type": "full_body",
        "total_duration_min": 40,
        "difficulty": "debutant",
        "description": "Circuit léger en poids de corps ou machines. Priorité à la technique.",
        "objective": "Construire une base musculaire pour augmenter le métabolisme de repos.",
        "exercises": [
            ("Squat goblet haltère",   3, "12-15", 75, "Haltère léger, focus sur la descente"),
            ("Pompes classiques",      3, "8-12",  75, "Sur les genoux si nécessaire pour les débutants"),
            ("Tirage horizontal poulie basse", 3, "12", 75, "Résistance légère"),
            ("Chaise murale",          3, "30 sec", 60, "Contre le mur, cuisses parallèles"),
            ("Crunchs abdominaux",     3, "15",    60, "Lent, concentrer sur la contraction"),
            ("Gainage planche",        3, "20 sec", 45, "Augmenter la durée chaque semaine"),
        ],
    },
    {
        "name": "Cardio Varié + Étirements — Débutant",
        "profile": "perte_poids_debutant",
        "session_type": "cardio",
        "total_duration_min": 45,
        "difficulty": "debutant",
        "description": "Mélange de cardio doux et mobilité. Idéal pour la récupération active.",
        "objective": "Maintenir l'activité entre les séances de renforcement.",
        "exercises": [
            ("Vélo stationnaire zone 2", 1, "20 min",    0,  "60-65% FCmax, résistance légère"),
            ("Jumping jacks",            3, "1 min",    60,  "Cardio léger"),
            ("High knees",               3, "45 sec",   60,  "Modéré"),
            ("Cat-Cow (mobilité lombaire)", 3, "10 cycles", 30, "Respiration profonde"),
            ("Pigeon yoga (fessiers)",   2, "45 sec/côté", 30, "Étirement profond des fessiers"),
            ("Foam roller dos et cuisses", 1, "5 min",  0,   "Récupération myofasciale"),
        ],
    },

    # ════════════════════════════════════════════════════════════
    # AMÉLIORATION CARDIO (entraînement polarisé 80/20)
    # ════════════════════════════════════════════════════════════
    {
        "name": "Endurance Fondamentale — Zone 2",
        "profile": "amelioration_cardio",
        "session_type": "cardio",
        "total_duration_min": 50,
        "difficulty": "intermediaire",
        "description": "80% du volume hebdo en zone 2. Allure conversationnelle, jamais essoufflé.",
        "objective": "Développer les mitochondries, améliorer l'efficacité cardiaque à l'effort.",
        "exercises": [
            ("Course à pied zone 2",    1, "10 min échauffement",  0,  "60% FCmax, très facile"),
            ("Course à pied zone 2",    1, "30 min effort soutenu", 0, "65-70% FCmax, conversation possible"),
            ("Course à pied zone 2",    1, "10 min retour calme",  0,  "55-60% FCmax"),
            ("Étirement ischio-jambiers debout", 2, "45 sec/côté", 30, "Impératif après la course"),
            ("Rotation thoracique au sol", 2, "30 sec/côté",       30, "Mobilité dorsale"),
        ],
    },
    {
        "name": "Intervalles VO2max — Zone 4-5",
        "profile": "amelioration_cardio",
        "session_type": "hiit",
        "total_duration_min": 45,
        "difficulty": "avance",
        "description": "20% du volume en zone haute. 6 × 3 min à 80-85% FCmax, 2 min récup active.",
        "objective": "Repousser le seuil anaérobie, augmenter le VO2max.",
        "exercises": [
            ("Course à pied zone 2",     1, "10 min échauffement", 0,  "65% FCmax"),
            ("Intervalles course 3min/2min", 6, "3 min effort / 2 min récup", 0, "80-85% FCmax sur les efforts"),
            ("Course à pied zone 2",     1, "10 min retour calme", 0,  "60% FCmax"),
        ],
    },
    {
        "name": "Cross-Training Cardio — Vélo + Rameur",
        "profile": "amelioration_cardio",
        "session_type": "cardio",
        "total_duration_min": 50,
        "difficulty": "intermediaire",
        "description": "Alterner deux machines pour travailler différents groupes musculaires.",
        "objective": "Développer l'endurance cardiovasculaire sans impact sur les articulations.",
        "exercises": [
            ("Vélo stationnaire zone 2", 1, "15 min",   0, "65-70% FCmax, cadence 80-90 rpm"),
            ("Rameur zone 3",            1, "15 min",   0, "70-75% FCmax, focus technique"),
            ("Vélo stationnaire zone 2", 1, "10 min",   0, "Retour au calme"),
            ("Natation crawl",           1, "10 min",   0, "Alternative si piscine disponible"),
        ],
    },
    {
        "name": "Récupération Active Cardio",
        "profile": "amelioration_cardio",
        "session_type": "cardio",
        "total_duration_min": 35,
        "difficulty": "debutant",
        "description": "Séance légère entre deux séances intenses. Ne jamais se reposer complètement.",
        "objective": "Maintenir le flux sanguin pour accélérer la récupération.",
        "exercises": [
            ("Marche rapide inclinée",   1, "20 min",   0,  "55-60% FCmax, conversation aisée"),
            ("Salutation au soleil (Yoga)", 3, "5 cycles", 30, "Mobilité et étirements dynamiques"),
            ("Cat-Cow (mobilité lombaire)", 3, "10 cycles", 30, "Décontraction du dos"),
            ("Foam roller dos et cuisses",  1, "10 min",  0,  "Cibler les zones douloureuses"),
        ],
    },

    # ════════════════════════════════════════════════════════════
    # MAINTIEN BIEN-ÊTRE (équilibre, variété, plaisir)
    # ════════════════════════════════════════════════════════════
    {
        "name": "Yoga Fonctionnel — Équilibre & Souplesse",
        "profile": "maintien_bien_etre",
        "session_type": "stretching",
        "total_duration_min": 45,
        "difficulty": "debutant",
        "description": "Séance yoga orientée bien-être. Aucune performance recherchée.",
        "objective": "Améliorer la souplesse, réduire les tensions musculaires, détente mentale.",
        "exercises": [
            ("Salutation au soleil (Yoga)", 5, "5 cycles",     60, "Respiration profonde, aucun forçage"),
            ("Pigeon yoga (fessiers)",      2, "60 sec/côté",  30, "Relâcher complètement"),
            ("Cat-Cow (mobilité lombaire)", 3, "10 cycles",    30, "Synchroniser avec la respiration"),
            ("Rotation thoracique au sol",  2, "45 sec/côté",  30, "Regarder la main qui tourne"),
            ("Étirement ischio-jambiers debout", 2, "45 sec/côté", 30, "Ne pas forcer"),
            ("Foam roller dos et cuisses",  1, "10 min",        0, "Terminer par un moment de relaxation"),
        ],
    },
    {
        "name": "Renforcement Fonctionnel — Maintien",
        "profile": "maintien_bien_etre",
        "session_type": "full_body",
        "total_duration_min": 45,
        "difficulty": "debutant",
        "description": "Exercices fonctionnels à intensité modérée. Garder le plaisir avant tout.",
        "objective": "Maintenir la condition physique actuelle, prévenir le déconditionnement.",
        "exercises": [
            ("Squat goblet haltère",   3, "15",    60, "Charge confortable, focus sur la sensation"),
            ("Pompes classiques",      3, "10-15", 60, "Varier la largeur des mains"),
            ("Superman",               3, "12",    60, "Tenir 2 sec en haut"),
            ("Chaise murale",          3, "40 sec", 45, "Augmenter progressivement"),
            ("Gainage planche",        3, "30 sec", 45, "Variante côté si maîtrisé"),
            ("Crunchs abdominaux",     3, "20",    45, "Pas d'élan"),
        ],
    },
    {
        "name": "Cardio Plaisir — Jogging & Mobilité",
        "profile": "maintien_bien_etre",
        "session_type": "cardio",
        "total_duration_min": 45,
        "difficulty": "debutant",
        "description": "Sortie cardio légère suivie de mobilité. Écouter son corps.",
        "objective": "Maintenir l'endurance de base, décompresser.",
        "exercises": [
            ("Course à pied zone 2",    1, "25 min",       0,  "60-65% FCmax, allure confortable"),
            ("Corde à sauter",          3, "2 min",       60,  "Optionnel si envie"),
            ("Étirement quadriceps debout", 2, "40 sec/côté", 30, "Fin de séance"),
            ("Étirement ischio-jambiers debout", 2, "40 sec/côté", 30, ""),
            ("Foam roller dos et cuisses",  1, "5 min",    0,   "Récupération"),
        ],
    },
]


# ---------------------------------------------------------------------------
# CREATE & SEED
# ---------------------------------------------------------------------------

def create_tables(cur):
    cur.execute("""
        DROP TABLE IF EXISTS session_exercises CASCADE;
        DROP TABLE IF EXISTS workout_sessions CASCADE;
        DROP TABLE IF EXISTS workout_exercises CASCADE;

        CREATE TABLE workout_exercises (
            id          SERIAL PRIMARY KEY,
            name        VARCHAR(255) NOT NULL UNIQUE,
            body_part   VARCHAR(100),
            category    VARCHAR(100),
            difficulty  VARCHAR(50),
            equipment   VARCHAR(100),
            description TEXT,
            created_at  TIMESTAMP DEFAULT NOW()
        );

        CREATE TABLE workout_sessions (
            id                 SERIAL PRIMARY KEY,
            name               VARCHAR(255) NOT NULL,
            profile            VARCHAR(100) NOT NULL,
            session_type       VARCHAR(100),
            total_duration_min INT,
            difficulty         VARCHAR(50),
            description        TEXT,
            objective          TEXT,
            created_at         TIMESTAMP DEFAULT NOW()
        );
        CREATE INDEX idx_ws_profile ON workout_sessions(profile);

        CREATE TABLE session_exercises (
            id          SERIAL PRIMARY KEY,
            session_id  INT REFERENCES workout_sessions(id) ON DELETE CASCADE,
            exercise_id INT REFERENCES workout_exercises(id),
            order_num   INT NOT NULL,
            sets        INT,
            reps        VARCHAR(100),
            rest_sec    INT,
            notes       TEXT
        );
        CREATE INDEX idx_se_session ON session_exercises(session_id);
    """)


def seed_exercises(cur):
    ex_map = {}
    for ex in EXERCISES:
        cur.execute(
            """
            INSERT INTO workout_exercises (name, body_part, category, difficulty, equipment, description)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (name) DO UPDATE SET
                body_part = EXCLUDED.body_part,
                category  = EXCLUDED.category
            RETURNING id
            """,
            (
                ex["name"], ex.get("body_part"), ex.get("category"),
                ex.get("difficulty"), ex.get("equipment"), ex.get("description", ""),
            ),
        )
        ex_map[ex["name"]] = cur.fetchone()["id"]
    return ex_map


def seed_sessions(cur, ex_map):
    count_sessions = 0
    count_links = 0
    for s in SESSIONS:
        cur.execute(
            """
            INSERT INTO workout_sessions
                (name, profile, session_type, total_duration_min, difficulty, description, objective)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (s["name"], s["profile"], s["session_type"], s["total_duration_min"],
             s["difficulty"], s["description"], s["objective"]),
        )
        session_id = cur.fetchone()["id"]
        count_sessions += 1

        for order, (ex_name, sets, reps, rest_sec, notes) in enumerate(s["exercises"], start=1):
            ex_id = ex_map.get(ex_name)
            if ex_id is None:
                print(f"  [WARN] Exercice introuvable : '{ex_name}'")
                continue
            cur.execute(
                """
                INSERT INTO session_exercises (session_id, exercise_id, order_num, sets, reps, rest_sec, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (session_id, ex_id, order, sets, str(reps), rest_sec, notes),
            )
            count_links += 1

    return count_sessions, count_links


if __name__ == "__main__":
    with psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor) as conn:
        with conn.cursor() as cur:
            create_tables(cur)
            ex_map = seed_exercises(cur)
            n_sessions, n_links = seed_sessions(cur, ex_map)
        conn.commit()
    print(f"✓ {len(ex_map)} exercices insérés")
    print(f"✓ {n_sessions} sessions insérées")
    print(f"✓ {n_links} liens session↔exercice insérés")
