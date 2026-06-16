"""
Dataset synthétique HealthAI Coach
===================================
Génère ~2000 profils utilisateurs réalistes basés sur :
- Distributions cliniques publiées (ACSM, OMS, NHANES)
- Corrélations physiologiques réelles (BMI/fat%, âge/BPM, etc.)
- Règles de labeling issues des guidelines ACSM 2022

Features = uniquement ce qui est disponible à l'inscription (pas de leakage temporel).
Target = profil fitness (6 classes) → recommandation de programme sportif.
"""

import numpy as np
import pandas as pd
from pathlib import Path

RNG = np.random.default_rng(42)
N = 2000

OUTPUT_DIR = Path(__file__).parent / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)



def generate_base(n: int) -> pd.DataFrame:
    gender = RNG.choice([0, 1], size=n, p=[0.48, 0.52])
    age    = RNG.integers(18, 66, size=n)
    exp    = RNG.choice([1, 2, 3], size=n, p=[0.50, 0.35, 0.15])

    height = np.where(
        gender == 1,
        RNG.normal(176, 7, n),
        RNG.normal(163, 6, n),
    ).clip(150, 210)

    bmi_mean = np.where(
        exp == 1, RNG.normal(27.5, 4.5, n),
        np.where(exp == 2, RNG.normal(25.0, 3.5, n),
                           RNG.normal(23.0, 2.8, n))
    )
    bmi = bmi_mean.clip(16, 45)
    weight = bmi * (height / 100) ** 2

    fat_base = np.where(gender == 1,
        bmi * 1.05 - 10.0 + RNG.normal(0, 3, n),
        bmi * 1.10 - 5.0  + RNG.normal(0, 3, n),
    )
    fat_pct = fat_base.clip(5, 50)

    resting_bpm_mean = np.where(exp == 1, 76, np.where(exp == 2, 70, 62))
    resting_bpm = (resting_bpm_mean + RNG.normal(0, 6, n)).clip(45, 100).astype(int)

    df = pd.DataFrame({
        "age":           age,
        "gender":        gender,
        "weight_kg":     weight.round(1),
        "height_cm":     height.round(1),
        "bmi":           bmi.round(2),
        "body_fat_pct":  fat_pct.round(1),
        "resting_bpm":   resting_bpm,
        "experience_level": exp,
    })
    return df



def _fat_is_high(row: pd.Series) -> bool:
    if row["gender"] == 1:
        return row["body_fat_pct"] > 23
    return row["body_fat_pct"] > 32

def _fat_is_low(row: pd.Series) -> bool:
    if row["gender"] == 1:
        return row["body_fat_pct"] < 16
    return row["body_fat_pct"] < 23


def assign_label(df: pd.DataFrame) -> pd.Series:
    labels = []
    for _, row in df.iterrows():
        bmi   = row["bmi"]
        exp   = row["experience_level"]
        hr    = row["resting_bpm"]
        age   = row["age"]

        if bmi >= 27.5 or _fat_is_high(row):
            label = "perte_poids_debutant" if exp == 1 else "perte_poids_confirme"

        elif bmi < 22.5 or _fat_is_low(row):
            label = "prise_masse_debutant" if exp == 1 else "prise_masse_confirme"

        elif hr > 72 and 22 <= bmi <= 28:
            label = "amelioration_cardio"

        else:
            label = "maintien_bien_etre"

        labels.append(label)

    labels = np.array(labels)

    noise_idx = RNG.choice(len(labels), size=int(0.12 * len(labels)), replace=False)
    adjacents = {
        "perte_poids_debutant":  "amelioration_cardio",
        "perte_poids_confirme":  "maintien_bien_etre",
        "prise_masse_debutant":  "maintien_bien_etre",
        "prise_masse_confirme":  "amelioration_cardio",
        "amelioration_cardio":   "maintien_bien_etre",
        "maintien_bien_etre":    "amelioration_cardio",
    }
    for i in noise_idx:
        labels[i] = adjacents[labels[i]]

    return pd.Series(labels, name="fitness_profile")



def main():
    print("Génération du dataset HealthAI Coach...")
    df = generate_base(N)
    df["fitness_profile"] = assign_label(df)

    out = OUTPUT_DIR / "healthai_dataset.csv"
    df.to_csv(out, index=False)
    print(f"\nDataset sauvegardé : {out}")
    print(f"Taille : {len(df)} lignes × {len(df.columns)} colonnes")
    print(f"\nDistribution des classes :")
    dist = df["fitness_profile"].value_counts()
    for cls, cnt in dist.items():
        pct = cnt / len(df) * 100
        print(f"  {cls:<30} {cnt:>5} ({pct:.1f}%)")

    print(f"\nStats descriptives :")
    print(df.describe().round(2).to_string())


if __name__ == "__main__":
    main()
