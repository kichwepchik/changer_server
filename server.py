from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3

app = FastAPI()

# Подключаемся к базе данных SQLite
conn = sqlite3.connect("keys.db", check_same_thread=False)
cursor = conn.cursor()

# Создаем таблицу, если её нет
cursor.execute("""
CREATE TABLE IF NOT EXISTS keys (
    key TEXT PRIMARY KEY,
    hwid TEXT DEFAULT NULL
)
""")
conn.commit()

# Модели данных
class KeyModel(BaseModel):
    key: str

class ActivationModel(BaseModel):
    key: str
    hwid: str

class HWIDModel(BaseModel):
    hwid: str

# Добавление ключа
@app.post("/add_key")
def add_key(data: KeyModel):
    try:
        cursor.execute("INSERT INTO keys (key) VALUES (?)", (data.key,))
        conn.commit()
        return {"status": "added"}
    except:
        raise HTTPException(status_code=400, detail="Ключ уже существует!")

# Активация ключа
@app.post("/activate")
def activate_key(data: ActivationModel):
    cursor.execute("SELECT hwid FROM keys WHERE key=?", (data.key,))
    result = cursor.fetchone()

    if not result:
        raise HTTPException(status_code=400, detail="Неверный ключ!")

    stored_hwid = result[0]

    if stored_hwid and stored_hwid != data.hwid:
        raise HTTPException(status_code=400, detail="Ключ уже активирован на другом устройстве!")

    cursor.execute("UPDATE keys SET hwid=? WHERE key=?", (data.hwid, data.key))
    conn.commit()
    
    return {"status": "activated"}

# Проверка HWID
@app.post("/check_hwid")
def check_hwid(data: HWIDModel):
    cursor.execute("SELECT key FROM keys WHERE hwid=?", (data.hwid,))
    result = cursor.fetchone()

    if result:
        return {"status": "verified"}
    else:
        raise HTTPException(status_code=400, detail="Устройство не активировано!")

# Получение всех ключей и привязанных HWID
@app.get("/keys")
def get_keys():
    cursor.execute("SELECT * FROM keys")
    keys = cursor.fetchall()
    return [{"key": row[0], "hwid": row[1]} for row in keys]

# Удаление ключа
@app.post("/delete_key")
def delete_key(data: KeyModel):
    cursor.execute("DELETE FROM keys WHERE key=?", (data.key,))
    conn.commit()
    return {"status": "deleted"}

# Отвязка HWID от ключа
@app.post("/remove_hwid")
def remove_hwid(data: ActivationModel):
    cursor.execute("UPDATE keys SET hwid=NULL WHERE key=?", (data.key,))
    conn.commit()
    return {"status": "hwid_removed"}
