"""
Migration : ancienne DB (mainline) → nouvelle DB (thomas).
Copie la table exercises (ETL) + re-seed meals + re-seed sessions.
"""
import os
import subprocess
import sys

OLD_URL = "postgresql://postgres:postgres@mainline.proxy.rlwy.net:51566/healthai"
NEW_URL = "postgresql://postgres:postgres@thomas.proxy.rlwy.net:14269/healthai"

import psycopg2
import psycopg2.extras


def migrate_exercises():
    """Copie la table exercises de l'ancienne BDD vers la nouvelle."""
    print("→ Connexion ancienne BDD...")
    old = psycopg2.connect(OLD_URL, cursor_factory=psycopg2.extras.RealDictCursor)
    new = psycopg2.connect(NEW_URL, cursor_factory=psycopg2.extras.RealDictCursor)

    old_cur = old.cursor()
    new_cur = new.cursor()

    # Récupérer la structure et les données
    old_cur.execute("SELECT * FROM exercises LIMIT 1")
    cols = [d[0] for d in old_cur.description]
    print(f"  Colonnes trouvées : {cols}")

    old_cur.execute("SELECT COUNT(*) as n FROM exercises")
    total = old_cur.fetchone()["n"]
    print(f"  {total} exercices à migrer...")

    # Créer la table dans la nouvelle BDD (même structure)
    old_cur.execute("""
        SELECT column_name, data_type, character_maximum_length
        FROM information_schema.columns
        WHERE table_name = 'exercises'
        ORDER BY ordinal_position
    """)
    schema = old_cur.fetchall()

    seen = set()
    col_defs = []
    for c in schema:
        col_name = c["column_name"]
        if col_name in seen:
            continue
        seen.add(col_name)
        dtype = c["data_type"]
        if col_name == "id":
            col_defs.append("id SERIAL PRIMARY KEY")
        elif dtype == "integer":
            col_defs.append(f"{col_name} INTEGER")
        elif dtype in ("character varying", "varchar"):
            length = c["character_maximum_length"] or 255
            col_defs.append(f"{col_name} VARCHAR({length})")
        elif dtype == "text":
            col_defs.append(f"{col_name} TEXT")
        elif dtype == "double precision":
            col_defs.append(f"{col_name} FLOAT")
        elif dtype == "boolean":
            col_defs.append(f"{col_name} BOOLEAN")
        elif dtype == "timestamp without time zone":
            col_defs.append(f"{col_name} TIMESTAMP")
        else:
            col_defs.append(f"{col_name} TEXT")

    new_cur.execute(f"DROP TABLE IF EXISTS exercises CASCADE")
    new_cur.execute(f"CREATE TABLE exercises ({', '.join(col_defs)})")

    # Copier par batch
    BATCH = 500
    offset = 0
    copied = 0
    while True:
        old_cur.execute(f"SELECT * FROM exercises ORDER BY id LIMIT {BATCH} OFFSET {offset}")
        rows = old_cur.fetchall()
        if not rows:
            break

        for row in rows:
            values = [row[c] for c in cols]
            placeholders = ",".join(["%s"] * len(cols))
            new_cur.execute(
                f"INSERT INTO exercises ({','.join(cols)}) VALUES ({placeholders})",
                values
            )
        copied += len(rows)
        offset += BATCH
        print(f"  {copied}/{total} copiés...")

    new.commit()
    old.close()
    new.close()
    print(f"✓ {copied} exercices migrés vers la nouvelle BDD")


if __name__ == "__main__":
    migrate_exercises()

    # Re-seed meals et sessions sur la nouvelle BDD
    env = os.environ.copy()
    env["DATABASE_URL"] = NEW_URL

    print("\n→ Seed meals sur nouvelle BDD...")
    result = subprocess.run(
        [sys.executable, "ml/data/seed_meals.py"],
        env=env, capture_output=True, text=True
    )
    print(result.stdout or result.stderr)

    print("→ Seed sessions sur nouvelle BDD...")
    result = subprocess.run(
        [sys.executable, "ml/data/seed_sessions.py"],
        env=env, capture_output=True, text=True
    )
    print(result.stdout or result.stderr)

    print("\n✓ Migration complète.")
    print(f"  Mets à jour DATABASE_URL dans ton .env :")
    print(f"  DATABASE_URL={NEW_URL}")
