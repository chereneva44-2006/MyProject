import requests
import json
from pydantic import BaseModel
import re
import time
import hashlib

class User(BaseModel):
    login: str
    email: str
    password: str

class AuthUser(BaseModel):
    login: str
    password: str

def validate_login(login):
    if len(login) < 8:
        print("Ошибка: Логин должен содержать не менее 8 символов")
        return False
    return True

def validate_email(email):
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        print("Ошибка: Неверный формат email. Пример: user@gmail.com")
        return False
    return True

def validate_password(password):
    password_pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*[!@#$%^&*(),.?":{}|<>]).{10,}$'
    if not re.match(password_pattern, password):
        print("Ошибка: Пароль должен содержать мин. 10 символов, заглавные/строчные буквы, спецсимволы")
        return False
    return True

def print_error(response):
    error_data = json.loads(response)
    error = error_data.get("detail", "Ошибка")
    print(f"Ошибка: {error}")

class Client:
    def __init__(self):
        self.session_token = None
    
    def create_signature(self, data):
        current_time = str(int(time.time()))
        body_str = json.dumps(data) if data is not None else "{}"
        signature = hashlib.sha256(f"{self.session_token}{body_str}{current_time}".encode()).hexdigest()
        return signature
    
    def send_request(self, method, url, data=None):
        headers = {'Authorization': self.create_signature(data)}
        
        if method.upper() == 'GET':
            response = requests.get(url, json=data, headers=headers)
        elif method.upper() == 'POST':
            response = requests.post(url, json=data, headers=headers)
        elif method.upper() == 'PATCH':
            response = requests.patch(url, json=data, headers=headers)
        elif method.upper() == 'DELETE':
            response = requests.delete(url, json=data, headers=headers)
        
        return response.text, response.status_code
    
    def reg(self):
        print("\n" + "="*40)
        print("РЕГИСТРАЦИЯ В СИСТЕМЕ BBS")
        print("="*40)
        
        login = input("Логин: ")
        if not validate_login(login):
            return False
        
        email = input("Email: ")
        if not validate_email(email):
            return False
        
        password = input("Пароль: ")
        if not validate_password(password):
            return False
        
        confirm_password = input("Повторите пароль: ")
        if password != confirm_password:
            print("Ошибка: Пароли не совпадают")
            return False
        
        print("✓ Пароли совпадают")
        user_data = User(login=login, email=email, password=password)
        
        response = requests.post("http://localhost:8000/users/reg", json=user_data.model_dump())
        
        if response.status_code == 200:
            user = response.json()
            self.session_token = user['session_token']
            print(f"\n✅ Пользователь {user['login']} успешно зарегистрирован!")
            return True
        else:
            error = response.json().get('detail', 'Ошибка')
            print(f"❌ Произошла ошибка: {error}")
            return False
    
    def auth(self):
        print("\n" + "="*40)
        print("АВТОРИЗАЦИЯ В СИСТЕМЕ BBS")
        print("="*40)
        
        login = input("Логин: ")
        password = input("Пароль: ")
        
        user_data = AuthUser(login=login, password=password)
        
        response = requests.post("http://localhost:8000/users/auth", json=user_data.model_dump())
        
        if response.status_code == 200:
            user = response.json()
            self.session_token = user['session_token']
            print(f"\n✅ Авторизация {user['login']} прошла успешно!")
            return True
        else:
            error = response.json().get('detail', 'Ошибка')
            print(f"❌ Произошла ошибка: {error}")
            return False
    
    def generate_sequence(self):
        print("\n" + "="*40)
        print("ГЕНЕРАЦИЯ ПОСЛЕДОВАТЕЛЬНОСТИ BBS")
        print("="*40)
        print("Введите параметры для генерации:")
        print("(для примера используйте: p=11, q=23, seed=7)")
        
        try:
            p = int(input("Простое число p: "))
            q = int(input("Простое число q: "))
            seed = int(input("Начальное зерно (seed): "))
            count = int(input("Количество чисел для генерации (1-100): "))
            
            if count < 1 or count > 100:
                print("Ошибка: количество должно быть от 1 до 100")
                return
            
            data = {"p": p, "q": q, "seed": seed, "count": count}
            result, code = self.send_request('POST', "http://localhost:8000/bbs/generate", data)
            
            if code == 200:
                response_data = json.loads(result)
                print(f"\n✅ {response_data['message']}")
                print(f"📊 Параметры: p={p}, q={q}, seed={seed}")
                print(f"🔢 Сгенерированная последовательность ({count} чисел):")
                print(f"   {response_data['sequence']}")
            else:
                print_error(result)
        except ValueError:
            print("❌ Ошибка: введите целые числа")
        except Exception as e:
            print(f"❌ Произошла ошибка: {e}")
    
    def get_current_sequence(self):
        result, code = self.send_request('GET', "http://localhost:8000/bbs/current")
        
        if code == 200:
            response_data = json.loads(result)
            print(f"\n✅ {response_data['message']}")
            
            if 'params' in response_data:
                params = response_data['params']
                print(f"📊 Параметры: p={params.get('p')}, q={params.get('q')}, seed={params.get('seed')}")
            
            sequence = response_data['sequence']
            print(f"🔢 Текущая последовательность ({len(sequence)} чисел):")
            print(f"   {sequence}")
        else:
            print_error(result)
    
    def test_sequence(self):
        result, code = self.send_request('POST', "http://localhost:8000/bbs/test")
        
        if code == 200:
            response_data = json.loads(result)
            print(f"\n✅ {response_data['message']}")
            
            test_result = response_data['test_result']
            print("\n📈 РЕЗУЛЬТАТЫ ЧАСТОТНОГО ТЕСТА:")
            print(f"   Всего чисел: {test_result['total_numbers']}")
            print(f"   Четных чисел: {test_result['even_count']} ({test_result['even_percentage']}%)")
            print(f"   Нечетных чисел: {test_result['odd_count']} ({test_result['odd_percentage']}%)")
            
            if test_result.get('is_balanced', False):
                print("   ✅ Распределение сбалансировано")
            else:
                print("   ⚠️  Распределение несбалансировано")
        else:
            print_error(result)
    
    def delete_sequence(self):
        confirm = input("\nВы точно хотите удалить текущую последовательность? (да/нет): ")
        if confirm.lower() != 'да':
            print("Отмена операции")
            return
        
        result, code = self.send_request('DELETE', "http://localhost:8000/bbs/current")
        
        if code == 200:
            response_data = json.loads(result)
            print(f"✅ {response_data['message']}")
        else:
            print_error(result)
    
    def view_history(self):
        result, code = self.send_request('GET', "http://localhost:8000/users/history")
        
        if code == 200:
            response_data = json.loads(result)
            print(f"\n📜 {response_data['message']}")
            
            history = response_data['history']
            if not history:
                print("   История пуста")
            else:
                for i, inf in enumerate(history, 1):
                    print(f"   {i}. {inf.get('time')}: {inf.get('operation')} ({inf.get('details')})")
        else:
            print_error(result)
    
    def delete_history(self):
        confirm = input("\nВы точно хотите удалить всю историю запросов? (да/нет): ")
        if confirm.lower() != 'да':
            print("Отмена операции")
            return
        
        result, code = self.send_request('DELETE', "http://localhost:8000/users/history")
        
        if code == 200:
            response_data = json.loads(result)
            print(f"✅ {response_data['message']}")
        else:
            print_error(result)
    
    def change_password(self):
        print("\n" + "="*40)
        print("СМЕНА ПАРОЛЯ")
        print("="*40)
        
        confirm = input("Вы точно хотите изменить пароль? (да/нет): ")
        if confirm.lower() != 'да':
            print("Отмена операции")
            return
        
        old_password = input("Старый пароль: ")
        new_password = input("Новый пароль: ")
        
        if not validate_password(new_password):
            return
        
        confirm_password = input("Повторите новый пароль: ")
        if new_password != confirm_password:
            print("❌ Ошибка: Пароли не совпадают")
            return
        
        data = {"old_password": old_password, "new_password": new_password}
        result, code = self.send_request('PATCH', "http://localhost:8000/users/password", data)
        
        if code == 200:
            response_data = json.loads(result)
            self.session_token = response_data['new_session_token']
            print(f"✅ {response_data['message']}")
        else:
            print_error(result)
    
    def work_bbs(self):
        while True:
            print("\n" + "="*50)
            print("🏗️  ГЕНЕРАЦИЯ ПСЕВДОСЛУЧАЙНЫХ ЧИСЕЛ BBS")
            print("="*50)
            print("1. Сгенерировать новую последовательность")
            print("2. Показать текущую последовательность")
            print("3. Протестировать последовательность (частотный тест)")
            print("4. Удалить текущую последовательность")
            print("5. Назад в главное меню")
            print("="*50)
            
            try:
                choice = input("Выберите действие (1-5): ").strip()
                
                if choice == "1":
                    self.generate_sequence()
                elif choice == "2":
                    self.get_current_sequence()
                elif choice == "3":
                    self.test_sequence()
                elif choice == "4":
                    self.delete_sequence()
                elif choice == "5":
                    print("Возврат в главное меню...")
                    return
                else:
                    print("❌ Неверный выбор. Введите число от 1 до 5")
            except Exception as e:
                print(f"❌ Произошла ошибка: {e}")
    
    def account_management(self):
        while True:
            print("\n" + "="*40)
            print("👤 УПРАВЛЕНИЕ УЧЕТНОЙ ЗАПИСЬЮ")
            print("="*40)
            print("1. Просмотр истории запросов")
            print("2. Удаление истории запросов")
            print("3. Смена пароля")
            print("4. Назад в главное меню")
            print("="*40)
            
            try:
                choice = input("Выберите действие (1-4): ").strip()
                
                if choice == "1":
                    self.view_history()
                elif choice == "2":
                    self.delete_history()
                elif choice == "3":
                    self.change_password()
                elif choice == "4":
                    print("Возврат в главное меню...")
                    return
                else:
                    print("❌ Неверный выбор. Введите число от 1 до 4")
            except Exception as e:
                print(f"❌ Произошла ошибка: {e}")
    
    def main_menu(self):
        while True:
            print("\n" + "="*50)
            print("🌟 ГЛАВНОЕ МЕНЮ - BBS ГЕНЕРАТОР")
            print("="*50)
            print("1. Работа с генератором BBS")
            print("2. Управление учетной записью")
            print("3. Выход из профиля")
            print("="*50)
            
            try:
                choice = input("Выберите действие (1-3): ").strip()
                
                if choice == "1":
                    self.work_bbs()
                elif choice == "2":
                    self.account_management()
                elif choice == "3":
                    print("🔒 Выход из профиля выполнен")
                    self.session_token = None
                    break
                else:
                    print("❌ Неверный выбор. Введите число от 1 до 3")
            except Exception as e:
                print(f"❌ Произошла ошибка: {e}")

def main():
    client = Client()
    
    print("\n" + "="*60)
    print("🚀 ДОБРО ПОЖАЛОВАТЬ В ГЕНЕРАТОР БЛЮМ БЛЮМ ШУБ (BBS)!")
    print("="*60)
    print("Криптографически стойкий генератор псевдослучайных чисел")
    print("="*60)
    
    while True:
        print("\nВыберите действие:")
        print("1. 📝 Регистрация нового пользователя")
        print("2. 🔑 Авторизация")
        print("3. 🚪 Выйти из программы")
        
        try:
            choice = input("Ваш выбор (1-3): ").strip()
            
            if choice == "1":
                if client.reg():
                    client.main_menu()
            elif choice == "2":
                if client.auth():
                    client.main_menu()
            elif choice == "3":
                print("\n👋 До свидания! Программа завершена.")
                break
            else:
                print("❌ Неверный выбор. Введите число от 1 до 3")
        except ValueError:
            print("❌ Некорректный ввод! Введите число.")
        except Exception as e:
            print(f"❌ Произошла ошибка: {e}")

if __name__ == "__main__":
    main()