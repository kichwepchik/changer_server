from fastapi import FastAPI, HTTPException
import sqlite3

app = FastAPI()

# Подключаемся к базе данных SQLite
conn = sqlite3.connect("keys.db", check_same_thread=False)
cursor = conn.cursor()

# Создаем таблицу для хранения ключей (если её нет)
cursor.execute("""
CREATE TABLE IF NOT EXISTS keys (
    key TEXT PRIMARY KEY,
    hwid TEXT DEFAULT NULL
)
""")
conn.commit()

@app.post("/activate")
def activate_key(key: str, hwid: str):
    """ Проверка активации ключа и привязка к HWID """
    cursor.execute("SELECT hwid FROM keys WHERE key=?", (key,))
    result = cursor.fetchone()

    if not result:
        raise HTTPException(status_code=400, detail="Неверный ключ!")

    stored_hwid = result[0]

    if stored_hwid and stored_hwid != hwid:
        raise HTTPException(status_code=400, detail="Ключ уже активирован на другом устройстве!")

    # Если ключ ещё не был привязан к HWID, привязываем
    cursor.execute("UPDATE keys SET hwid=? WHERE key=?", (hwid, key))
    conn.commit()
    
    return {"status": "activated"}

@app.post("/add_key")
def add_key(key: str):
    """ Добавление нового ключа в базу """
    try:
        cursor.execute("INSERT INTO keys (key) VALUES (?)", (key,))
        conn.commit()
        return {"status": "added"}
    except:
        raise HTTPException(status_code=400, detail="Ключ уже существует!")

