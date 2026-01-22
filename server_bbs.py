from typing import Union, List
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import json
import time
import os
import random
import hashlib

app = FastAPI(title="BBS Generator API", description="Генератор псевдослучайных чисел Блюм Блюм Шуб")

# === МОДЕЛИ ДАННЫХ ===
class User(BaseModel):
    login: str
    email: str
    password: str
    technical_token: Union[str, None] = None
    session_token: Union[str, None] = None
    id: Union[int, None] = -1
    current_sequence: List[int] = []
    bbs_params: dict = {}
    saved_params: List[dict] = []

class AuthUser(BaseModel):
    login: str
    password: str

class BBSGenerateRequest(BaseModel):
    p: int
    q: int
    seed: int
    count: int

class BBSGenerateOneRequest(BaseModel):
    p: int
    q: int
    seed: int
    iterations: int

class SaveParamsRequest(BaseModel):
    name: str
    p: int
    q: int
    seed: int

class PasswordChange(BaseModel):
    old_password: str
    new_password: str

# === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===
def get_user_by_token(request: Request, body: dict = None) -> User:
    client_signature = request.headers.get('Authorization')
    if not client_signature:
        raise HTTPException(status_code=401, detail="Отсутствует подпись")
    
    current_time = int(time.time())
    body_str = json.dumps(body) if body is not None else "{}"
    
    for time_add in [-3, -2, -1, 0]:
        check_time = str(current_time + time_add)
        
        for file in os.listdir("users"):
            with open(f"users/{file}", 'r') as f:
                user_data = json.load(f)
                user_token = user_data.get('session_token')
                server_signature = hashlib.sha256(f"{user_token}{body_str}{check_time}".encode()).hexdigest()
                if server_signature == client_signature:
                    return User(**user_data)
    raise HTTPException(status_code=401, detail="Неверная подпись")

def save_user(user: User):
    with open(f"users/user_{user.id}.json", 'w') as f:
        json.dump(user.model_dump(), f)

def save_history(user_id: int, operation_type: str, details: str):
    history_file = f"history/history_{user_id}.json"
    if not os.path.exists(history_file):
        return
    
    with open(history_file, 'r') as f:
        history = json.load(f)
    
    current_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    history_add = {
        "user": user_id,
        "time": current_time,
        "operation": operation_type,
        "details": details
    }
    history.append(history_add)
    
    with open(history_file, 'w') as f:
        json.dump(history, f, indent=2)

def blum_blum_shub(p: int, q: int, seed: int, count: int) -> List[int]:
    n = p * q
    x = seed % n
    result = []
    
    for _ in range(count):
        byte_value = 0
        
        for _ in range(8):
            x = (x * x) % n
            bit = x & 1
            byte_value = (byte_value << 1) | bit
        
        result.append(byte_value % 100)
    
    return result

def generate_one_number(p: int, q: int, seed: int, iterations: int) -> int:
    n = p * q
    x = seed % n
    
    for _ in range(iterations):
        x = (x * x) % n
    
    byte_value = 0
    for _ in range(8):
        x = (x * x) % n
        bit = x & 1
        byte_value = (byte_value << 1) | bit
    
    return byte_value % 100  

# === ЭНДПОИНТЫ API ===

@app.post("/users/register")
def create_user(user: User):
    if not os.path.exists("users"):
        os.makedirs("users")
    
    for file in os.listdir("users"):
        with open(f"users/{file}", 'r') as f:
            data = json.load(f)
            if data['login'] == user.login:
                raise HTTPException(status_code=400, detail="Логин уже занят")
            if data['email'] == user.email:
                raise HTTPException(status_code=400, detail="Email уже занят")
    
    user.id = int(time.time())
    user.technical_token = str(random.getrandbits(128))
    user.session_token = hashlib.sha256(f"{user.technical_token}{time.time()}".encode()).hexdigest()
    
    save_user(user)
    
    if not os.path.exists("history"):
        os.makedirs("history")
    
    with open(f"history/history_{user.id}.json", 'w') as f:
        json.dump([], f)
    
    save_history(user.id, "register", "Пользователь зарегистрирован")
    return {
        "message": "Успешная регистрация",
        "login": user.login,
        "session_token": user.session_token
    }

@app.post("/users/authenticate")
def auth_user(params: AuthUser):
    json_files_names = [file for file in os.listdir('users/') if file.endswith('.json')]
    for json_file_name in json_files_names:
        file_path = os.path.join('users/', json_file_name)
        with open(file_path, 'r') as f:
            json_item = json.load(f)
            user = User(**json_item)
            if user.login == params.login and user.password == params.password:
                user.session_token = hashlib.sha256(f"{user.technical_token}{time.time()}".encode()).hexdigest()
                save_user(user)
                save_history(user.id, "auth", "Успешная авторизация")
                return {
                    "message": "Успешная авторизация",
                    "login": user.login,
                    "session_token": user.session_token
                }
    
    raise HTTPException(status_code=401, detail="Неверный логин или пароль")

@app.post("/bbs/generate_one")
def generate_one_bbs_number(request: BBSGenerateOneRequest, request_obj: Request):
    user = get_user_by_token(request_obj, request.model_dump())
    
    if request.p <= 3 or request.q <= 3:
        raise HTTPException(status_code=400, detail="Числа p и q должны быть больше 3")
    if request.iterations <= 0:
        raise HTTPException(status_code=400, detail="Количество итераций должно быть положительным")
    
    result_number = generate_one_number(request.p, request.q, request.seed, request.iterations)
    
    save_history(user.id, "bbs_generate_one", 
                 f"Сгенерировано одно число: {result_number} (p={request.p}, q={request.q}, seed={request.seed}, iter={request.iterations})")
    
    return {
        "message": "Число сгенерировано",
        "number": result_number,
        "parameters": request.model_dump()
    }

@app.post("/bbs/generate")
def generate_bbs_sequence(request: BBSGenerateRequest, request_obj: Request):
    user = get_user_by_token(request_obj, request.model_dump())
    
    if request.p <= 3 or request.q <= 3:
        raise HTTPException(status_code=400, detail="Числа p и q должны быть больше 3")
    if request.count <= 0 or request.count > 100:
        raise HTTPException(status_code=400, detail="Количество чисел должно быть от 1 до 100")
    
    sequence = blum_blum_shub(request.p, request.q, request.seed, request.count)
    
    user.current_sequence = sequence
    user.bbs_params = request.model_dump()
    save_user(user)

    save_history(user.id, "bbs_generate", f"Сгенерировано {request.count} чисел BBS")
    return {
        "message": "Последовательность сгенерирована",
        "sequence": sequence,
        "params": user.bbs_params
    }

@app.get("/bbs/current")
def get_current_sequence(request_obj: Request):
    user = get_user_by_token(request_obj)
    
    if not user.current_sequence:
        raise HTTPException(status_code=404, detail="Последовательность не найдена")
    
    save_history(user.id, "bbs_get", f"Получена последовательность")
    return {
        "message": "Текущая последовательность",
        "sequence": user.current_sequence,
        "params": user.bbs_params
    }

@app.delete("/bbs/current")
def delete_sequence(request_obj: Request):
    user = get_user_by_token(request_obj)
    
    user.current_sequence = []
    user.bbs_params = {}
    save_user(user)
    
    save_history(user.id, "bbs_delete", "Последовательность удалена")
    return {"message": "Последовательность удалена", "sequence": []}

@app.post("/bbs/save_params")
def save_parameters(request: SaveParamsRequest, request_obj: Request):
    user = get_user_by_token(request_obj, request.model_dump())
    
    if not hasattr(user, 'saved_params'):
        user.saved_params = []
    
    for param in user.saved_params:
        if param.get('name') == request.name:
            raise HTTPException(status_code=400, detail="Параметры с таким именем уже существуют")
    
    user.saved_params.append({
        "name": request.name,
        "p": request.p,
        "q": request.q,
        "seed": request.seed,
        "created_at": time.strftime('%Y-%m-%d %H:%M:%S')
    })
    
    save_user(user)
    save_history(user.id, "save_params", f"Сохранены параметры '{request.name}'")
    
    return {
        "message": "Параметры сохранены",
        "name": request.name,
        "total_saved": len(user.saved_params)
    }

@app.get("/bbs/saved_params")
def get_saved_parameters(request_obj: Request):
    user = get_user_by_token(request_obj)
    
    if not hasattr(user, 'saved_params') or not user.saved_params:
        return {"message": "Нет сохраненных параметров", "params": []}
    
    return {
        "message": f"Сохраненные параметры ({len(user.saved_params)})",
        "params": user.saved_params
    }

@app.delete("/bbs/saved_params/{param_name}")
def delete_saved_parameters(param_name: str, request_obj: Request):
    user = get_user_by_token(request_obj)
    
    if not hasattr(user, 'saved_params'):
        raise HTTPException(status_code=404, detail="Нет сохраненных параметров")
    
    original_count = len(user.saved_params)
    user.saved_params = [p for p in user.saved_params if p.get('name') != param_name]
    
    if len(user.saved_params) == original_count:
        raise HTTPException(status_code=404, detail="Параметры с таким именем не найдены")
    
    save_user(user)
    save_history(user.id, "delete_params", f"Удалены параметры '{param_name}'")
    
    return {
        "message": "Параметры удалены",
        "deleted_name": param_name,
        "remaining": len(user.saved_params)
    }

@app.get("/users/history")
def get_user_history(request_obj: Request):
    user = get_user_by_token(request_obj)
    
    history_file = f"history/history_{user.id}.json"
    
    with open(history_file, 'r') as f:
        history = json.load(f)
        
    if history == []:
        return {"message": "История пуста", "history": history}
    
    return {
        "message": "История запросов",
        "history": history
    }

@app.delete("/users/history")
def delete_user_history(request_obj: Request):
    user = get_user_by_token(request_obj)
    
    history_file = f"history/history_{user.id}.json"
    if os.path.exists(history_file):
        with open(history_file, 'w') as f:
            json.dump([], f)
            
    return {"message": "История удалена"}

@app.patch("/users/password")
def change_password(request: PasswordChange, request_obj: Request):
    user = get_user_by_token(request_obj, request.model_dump())
    
    user_file = f"users/user_{user.id}.json"
    if not os.path.exists(user_file):
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    with open(user_file, 'r') as f:
        user_data = json.load(f)
    if user_data['password'] != request.old_password:
        raise HTTPException(status_code=400, detail="Неверный старый пароль")
    
    user_data['password'] = request.new_password
    user_data['technical_token'] = hashlib.sha256(f"{time.time()}{random.getrandbits(256)}".encode()).hexdigest()
    user_data['session_token'] = hashlib.sha256(f"{user_data['technical_token']}{time.time()}".encode()).hexdigest()
    
    with open(user_file, 'w') as f:
        json.dump(user_data, f)
    save_history(user.id, "change_password", "Пароль изменен")
    
    return {
        "message": "Пароль изменен",
        "new_session_token": user_data['session_token']
    }

if __name__ == "__main__":
    import uvicorn
    print("Сервер BBS Generator запущен на http://localhost:8000")
    print("Документация API: http://localhost:8000/docs")
    uvicorn.run(app, host="127.0.0.1", port=8000)