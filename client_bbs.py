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
    if len(login) < 5:
        print("Ошибка! Логин должен содержать не менее 5 символов")
        return False
    return True

def validate_email(email):
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        print("Ошибка: Формат email не соответствует норме. Пример для ознакомления: alena@gmail.com")
        return False
    return True

def validate_password(password):
    password_pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*[!@#$%^&*(),.?":{}|<>]).{5,}$'
    if not re.match(password_pattern, password):
        print("Ошибка! Минимальное количество символов для пароля = 5, заглавные или строчные буквы, спецсимволы")
        return False
    return True

def print_error(response):
    try:
        error_data = json.loads(response)
        error = error_data.get("detail", "Ошибка")
        print(f"Ошибка: {error}")
    except:
        print(f"Ошибка: {response}")

def is_prime(n):
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    for i in range(3, int(n**0.5) + 1, 2):
        if n % i == 0:
            return False
    return True

def is_blum_prime(n):
    return is_prime(n) and (n % 4 == 3)

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
    
    def print_bbs_info(self):
        print("\n" + "="*60)
        print("ИНФОРМАЦИЯ О ПАРАМЕТРАХ BBS:")
        print("="*60)
        print("Для корректной работы генератора BBS рекомендуется:")
        print("- p и q должны быть простыми числами")
        print("- p и q должны быть сравнимы с 3 по модулю 4 (p % 4 == 3, q % 4 == 3)")
        print("- p и q не должны быть равны")
        print("- seed не должно быть кратно p*q")
        print("\nПримеры подходящих параметров:")
        print("- p=11, q=19, seed=13")
        print("- p=23, q=31, seed=17")
        print("="*60 + "\n")
    
    def check_basic_params(self, p, q, seed):
        errors = []
        if p <= 3 or q <= 3:
            errors.append("p и q должны быть больше 3")
        if p == q:
            errors.append("p и q не должны быть равны")
        if seed <= 0:
            errors.append("seed должно быть положительным числом")
        
        if errors:
            print("\nПредупреждение:")
            for error in errors:
                print(f"- {error}")
            print("Генерация может работать некорректно.")
            return False
        return True
    
    def register(self):
        print("\nРЕГИСТРАЦИЯ В СИСТЕМЕ BBS")
        
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
        
        print("Пароли совпадают")
        user_data = User(login=login, email=email, password=password)
        
        response = requests.post("http://localhost:8000/users/register", json=user_data.model_dump())
        
        if response.status_code == 200:
            user = response.json()
            self.session_token = user['session_token']
            print(f"\nПользователь {user['login']} успешно зарегистрирован!")
            return True
        else:
            error = response.json().get('detail', 'Ошибка')
            print(f"Произошла ошибка: {error}")
            return False
    
    def authenticate(self):
        print("\nАВТОРИЗАЦИЯ В СИСТЕМЕ BBS")
        
        login = input("Логин: ")
        password = input("Пароль: ")
        
        user_data = AuthUser(login=login, password=password)
        
        response = requests.post("http://localhost:8000/users/authenticate", json=user_data.model_dump())
        
        if response.status_code == 200:
            user = response.json()
            self.session_token = user['session_token']
            print(f"\nАвторизация {user['login']} прошла успешно!")
            return True
        else:
            error = response.json().get('detail', 'Ошибка')
            print(f"Произошла ошибка: {error}")
            return False
    
    def generate_one_number(self):
        print("\nГЕНЕРАЦИЯ ОДНОГО ЧИСЛА BBS")
        self.print_bbs_info()
        
        try:
            p = int(input("Число p: "))
            q = int(input("Число q: "))
            seed = int(input("Начальное значение (seed): "))
            iterations = int(input("Количество итераций: "))
            
            self.check_basic_params(p, q, seed)
            
            if iterations <= 0:
                print("Ошибка: количество итераций должно быть положительным")
                return
            
            data = {"p": p, "q": q, "seed": seed, "iterations": iterations}
            result, code = self.send_request('POST', "http://localhost:8000/bbs/generate_one", data)
            
            if code == 200:
                response_data = json.loads(result)
                print(f"\n{response_data['message']}")
                print(f"Число: {response_data['number']}")
            else:
                print_error(result)
        except ValueError:
            print("Ошибка: введите целые числа")
        except Exception as e:
            print(f"Произошла ошибка: {e}")
    
    def generate_sequence(self):
        print("\nГЕНЕРАЦИЯ ПОСЛЕДОВАТЕЛЬНОСТИ BBS")
        self.print_bbs_info()
        
        try:
            p = int(input("Число p: "))
            q = int(input("Число q: "))
            seed = int(input("Начальное значение (seed): "))
            count = int(input("Количество чисел (1-100): "))
            
            self.check_basic_params(p, q, seed)
            
            if count < 1 or count > 100:
                print("Ошибка: количество должно быть от 1 до 100")
                return
            
            data = {"p": p, "q": q, "seed": seed, "count": count}
            result, code = self.send_request('POST', "http://localhost:8000/bbs/generate", data)
            
            if code == 200:
                response_data = json.loads(result)
                print(f"\n{response_data['message']}")
                sequence = response_data['sequence']
                print(f"Последовательность ({len(sequence)} чисел):")
                
                for i in range(0, len(sequence), 10):
                    print(" ".join(str(x) for x in sequence[i:i+10]))
            else:
                print_error(result)
        except ValueError:
            print("Ошибка: введите целые числа")
        except Exception as e:
            print(f"Произошла ошибка: {e}")
    
    def get_current_sequence(self):
        result, code = self.send_request('GET', "http://localhost:8000/bbs/current")
        
        if code == 200:
            response_data = json.loads(result)
            print(f"\n{response_data['message']}")
            
            if 'params' in response_data:
                params = response_data['params']
                print(f"Параметры: p={params.get('p')}, q={params.get('q')}, seed={params.get('seed')}")
            
            sequence = response_data['sequence']
            print(f"Текущая последовательность ({len(sequence)} чисел):")
            print(f"{sequence}")
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
            print(f"{response_data['message']}")
        else:
            print_error(result)
    
    def save_parameters(self):
        print("\nСОХРАНЕНИЕ ПАРАМЕТРОВ ГЕНЕРАЦИИ")
        self.print_bbs_info()
        
        try:
            name = input("Название для сохранения параметров: ")
            if not name:
                print("Ошибка: название не может быть пустым")
                return
            
            p = int(input("Число p: "))
            q = int(input("Число q: "))
            seed = int(input("Начальное значение (seed): "))
            
            self.check_basic_params(p, q, seed)
            
            data = {"name": name, "p": p, "q": q, "seed": seed}
            result, code = self.send_request('POST', "http://localhost:8000/bbs/save_params", data)
            
            if code == 200:
                response_data = json.loads(result)
                print(f"\n{response_data['message']}")
                print(f"Имя: {response_data['name']}")
                print(f"Всего сохранено параметров: {response_data['total_saved']}")
            else:
                print_error(result)
        except ValueError:
            print("Ошибка: введите целые числа")
        except Exception as e:
            print(f"Произошла ошибка: {e}")
    
    def show_saved_parameters(self):
        result, code = self.send_request('GET', "http://localhost:8000/bbs/saved_params")
        
        if code == 200:
            response_data = json.loads(result)
            print(f"\n{response_data['message']}")
            
            params = response_data['params']
            if not params:
                print("Нет сохраненных параметров")
            else:
                for i, param in enumerate(params, 1):
                    print(f"{i}. {param.get('name')}: p={param.get('p')}, q={param.get('q')}, seed={param.get('seed')} ({param.get('created_at')})")
        else:
            print_error(result)
    
    def delete_saved_parameters(self):
        self.show_saved_parameters()
        
        param_name = input("\nВведите название параметров для удаления: ")
        if not param_name:
            print("Отмена операции")
            return
        
        confirm = input(f"Вы точно хотите удалить параметры '{param_name}'? (да/нет): ")
        if confirm.lower() != 'да':
            print("Отмена операции")
            return
        
        result, code = self.send_request('DELETE', f"http://localhost:8000/bbs/saved_params/{param_name}")
        
        if code == 200:
            response_data = json.loads(result)
            print(f"{response_data['message']}")
            print(f"Удалено: {response_data['deleted_name']}")
            print(f"Осталось параметров: {response_data['remaining']}")
        else:
            print_error(result)
    
    def view_history(self):
        result, code = self.send_request('GET', "http://localhost:8000/users/history")
        
        if code == 200:
            response_data = json.loads(result)
            print(f"\n{response_data['message']}")
            
            history = response_data['history']
            if not history:
                print("История пуста")
            else:
                for i, inf in enumerate(history, 1):
                    print(f"{i}. {inf.get('time')}: {inf.get('operation')} ({inf.get('details')})")
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
            print(f"{response_data['message']}")
        else:
            print_error(result)
    
    def change_password(self):
        print("\nСМЕНА ПАРОЛЯ")
        
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
            print("Ошибка: Пароли не совпадают")
            return
        
        data = {"old_password": old_password, "new_password": new_password}
        result, code = self.send_request('PATCH', "http://localhost:8000/users/password", data)
        
        if code == 200:
            response_data = json.loads(result)
            self.session_token = response_data['new_session_token']
            print(f"{response_data['message']}")
        else:
            print_error(result)
    
    def bbs_main(self):
        while True:
            print("\nГЕНЕРАЦИЯ ПСЕВДОСЛУЧАЙНЫХ ЧИСЕЛ BBS")
            print("1. Сгенерировать одно число")
            print("2. Сгенерировать последовательность")
            print("3. Показать текущую последовательность")
            print("4. Сохранить параметры генерации")
            print("5. Показать сохраненные параметры")
            print("6. Удалить сохраненные параметры")
            print("7. Удалить текущую последовательность")
            print("8. Назад в главное меню")
            
            try:
                choice = input("Выберите действие (1-8): ").strip()
                
                if choice == "1":
                    self.generate_one_number()
                elif choice == "2":
                    self.generate_sequence()
                elif choice == "3":
                    self.get_current_sequence()
                elif choice == "4":
                    self.save_parameters()
                elif choice == "5":
                    self.show_saved_parameters()
                elif choice == "6":
                    self.delete_saved_parameters()
                elif choice == "7":
                    self.delete_sequence()
                elif choice == "8":
                    print("Возврат в главное меню...")
                    return
                else:
                    print("Неверный выбор. Введите число от 1 до 8")
            except Exception as e:
                print(f"Произошла ошибка: {e}")
    
    def account_management(self):
        while True:
            print("\nУПРАВЛЕНИЕ УЧЕТНОЙ ЗАПИСЬЮ")
            print("1. Просмотр истории запросов")
            print("2. Удаление истории запросов")
            print("3. Смена пароля")
            print("4. Назад в главное меню")
            
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
                    print("Неверный выбор. Введите число от 1 до 4")
            except Exception as e:
                print(f"Произошла ошибка: {e}")
    
    def main_menu(self):
        while True:
            print("\nГЛАВНОЕ МЕНЮ - BBS ГЕНЕРАТОР")
            print("1. Работа с генератором BBS")
            print("2. Управление учетной записью")
            print("3. Выход из профиля")
            
            try:
                choice = input("Выберите действие (1-3): ").strip()
                
                if choice == "1":
                    self.bbs_main()
                elif choice == "2":
                    self.account_management()
                elif choice == "3":
                    print("Выход из профиля выполнен")
                    self.session_token = None
                    break
                else:
                    print("Неверный выбор. Введите число от 1 до 3")
            except Exception as e:
                print(f"Произошла ошибка: {e}")

def main():
    client = Client()
    
    print("\nГЕНЕРАТОР БЛЮМ БЛЮМ ШУБ (BBS)")
    
    while True:
        print("\nВыберите действие:")
        print("1. Регистрация нового пользователя")
        print("2. Авторизация")
        print("3. Выйти из программы")
        
        try:
            choice = input("Ваш выбор (1-3): ").strip()
            
            if choice == "1":
                if client.register():
                    client.main_menu()
            elif choice == "2":
                if client.authenticate():
                    client.main_menu()
            elif choice == "3":
                print("\nПрограмма завершена.")
                break
            else:
                print("Неверный выбор. Введите число от 1 до 3")
        except ValueError:
            print("Некорректный ввод! Введите число.")
        except Exception as e:
            print(f"Произошла ошибка: {e}")

if __name__ == "__main__":
    main()