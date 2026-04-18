from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import os
from passlib.context import CryptContext

# ---------- PASSWORD HASHING ----------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ---------- APP ----------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- DB CONNECTION FUNCTION ----------
def get_db():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )

# =========================
# 🔐 AUTH ROUTES
# =========================

@app.post("/signup")
def signup(user: dict):
    try:
        conn = get_db()
        cursor = conn.cursor()

        username = user["username"].strip()
        password = user["password"]

        hashed_password = pwd_context.hash(password)

        cursor.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s) RETURNING id",
            (username, hashed_password)
        )

        user_id = cursor.fetchone()[0]
        conn.commit()

        cursor.close()
        conn.close()

        return {"user_id": user_id}

    except Exception as e:
        print("🔥 ERROR:", e)
        return {"error": "Signup failed"}


@app.post("/login")
def login(user: dict):
    conn = get_db()
    cursor = conn.cursor()

    username = user["username"].strip()
    password = user["password"]

    cursor.execute(
        "SELECT id, password FROM users WHERE username=%s",
        (username,)
    )

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    if result and pwd_context.verify(password, result[1]):
        return {"user_id": result[0]}

    return {"error": "Invalid credentials"}


# =========================
# 📝 NOTES ROUTES
# =========================

@app.get("/notes/{user_id}")
def get_notes(user_id: int):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM notes WHERE user_id=%s ORDER BY id DESC",
        (user_id,)
    )

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return [
        {
            "id": r[0],
            "title": r[1],
            "text": r[2],
            "createdAt": str(r[3])
        }
        for r in rows
    ]


@app.post("/notes")
def add_note(note: dict):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO notes (title, text, created_at, user_id) VALUES (%s, %s, NOW(), %s) RETURNING id, created_at",
        (note["title"], note["text"], note["user_id"])
    )

    new_note = cursor.fetchone()
    conn.commit()

    cursor.close()
    conn.close()

    return {
        "id": new_note[0],
        "title": note["title"],
        "text": note["text"],
        "createdAt": str(new_note[1])
    }


@app.put("/notes/{note_id}")
def update_note(note_id: int, updated_note: dict):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE notes SET title=%s, text=%s WHERE id=%s",
        (updated_note["title"], updated_note["text"], note_id)
    )

    conn.commit()

    cursor.close()
    conn.close()

    return {"message": "Updated"}


@app.delete("/notes/{note_id}")
def delete_note(note_id: int):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM notes WHERE id=%s",
        (note_id,)
    )

    conn.commit()

    cursor.close()
    conn.close()

    return {"message": "Deleted"}