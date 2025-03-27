from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3

app = FastAPI()

# Подключаемся к базе данных SQLite
conn = sqlite3.connect("keys.db", check_same_thread=False)
cursor = conn.cursor()

# Создаем таблицу для хранения ключей
cursor.execute("""
CREATE TABLE IF NOT EXISTS keys (
    key TEXT PRIMARY KEY,
    hwid TEXT DEFAULT NULL
)
""")
conn.commit()

# Модели данных для POST-запросов
class KeyModel(BaseModel):
    key: str

class ActivationModel(BaseModel):
    key: str
    hwid: str

@app.post("/add_key")
def add_key(data: KeyModel):
    """ Добавление нового ключа в базу """
    try:
        cursor.execute("INSERT INTO keys (key) VALUES (?)", (data.key,))
        conn.commit()
        return {"status": "added"}
    except:
        raise HTTPException(status_code=400, detail="Ключ уже существует!")

@app.post("/activate")
def activate_key(data: ActivationModel):
    """ Проверка активации ключа и привязка к HWID """
    cursor.execute("SELECT hwid FROM keys WHERE key=?", (data.key,))
    result = cursor.fetchone()

    if not result:
        raise HTTPException(status_code=400, detail="Неверный ключ!")

    stored_hwid = result[0]

    if stored_hwid and stored_hwid != data.hwid:
        raise HTTPException(status_code=400, detail="Ключ уже активирован на другом устройстве!")

    # Если ключ ещё не был привязан к HWID, привязываем
    cursor.execute("UPDATE keys SET hwid=? WHERE key=?", (data.hwid, data.key))
    conn.commit()
    
    return {"status": "activated"}
