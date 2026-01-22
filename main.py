import unittest
import requests
import json
import time
import hashlib

class TestBBSEndpoints(unittest.TestCase):
    
    def init_test(self):
        self.base_url = "http://localhost:8000"
        self.username = f"testuser_{int(time.time())}"
        self.email = f"test_{int(time.time())}@test.com"
        self.password = "Test123!@#"
        self.token = None
    
    def login_user(self):
        response = requests.post(f"{self.base_url}/users/authenticate", 
        json={"login": self.username, "password": self.password})
        if response.status_code == 200:
            self.token = response.json().get("session_token")
        return response
    
    def create_signature(self, body=None):
        if not self.token: 
            return None
        current_time = str(int(time.time()))
        body_str = json.dumps(body) if body else "{}"
        return hashlib.sha256(f"{self.token}{body_str}{current_time}".encode()).hexdigest()
    
    def test_01_registration(self):
        response = requests.post(f"{self.base_url}/users/register", 
        json={"login": self.username, "email": self.email, "password": self.password})
        
        print(f"\nРегистрация пользователя:")
        print(f"Ожидаемый код: 200")
        print(f"Итог: {response.status_code}")
        self.assertEqual(response.status_code, 200)
    
    def test_02_registration_duplicate(self):
        requests.post(f"{self.base_url}/users/register", 
        json={"login": self.username, "email": self.email, "password": self.password})
        
        response = requests.post(f"{self.base_url}/users/register", 
        json={"login": self.username, "email": "different@test.com", "password": self.password})
        
        print(f"\nРегистрация уже зарегистрированного пользователя:")
        print(f"Ожидаемый код: 400")
        print(f"Итог: {response.status_code}")
        self.assertEqual(response.status_code, 400)
    
    def test_03_auth(self):
        requests.post(f"{self.base_url}/users/register", 
        json={"login": self.username, "email": self.email, "password": self.password})
        
        response = self._auth_user()
        print(f"\nАвторизация пользователя:")
        print(f"Ожидаемый код: 200")
        print(f"Итог: {response.status_code}")
        self.assertEqual(response.status_code, 200)
    
    def test_04_auth_wrong(self):
        response = requests.post(f"{self.base_url}/users/authenticate", 
        json={"login": "wronguser", "password": "wrongpassword"})
        
        print(f"\nАвторизация с неверными данными:")
        print(f"Ожидаемый код: 401")
        print(f"Итог: {response.status_code}")
        self.assertEqual(response.status_code, 401)

    def test_05_generate_one(self):
        requests.post(f"{self.base_url}/users/register", 
        json={"login": self.username, "email": self.email, "password": self.password})
        self._auth_user()
        
        data = {"p": 23, "q": 31, "seed": 17, "iterations": 5}
        signature = self._get_signature(data)
        headers = {"Authorization": signature}
        response = requests.post(f"{self.base_url}/bbs/generate_one", json=data, headers=headers)
        
        print(f"\nГенерация одного числа:")
        print(f"Ожидаемый код: 200")
        print(f"Итог: {response.status_code}")
        self.assertEqual(response.status_code, 200)
    
    def test_06_generate_sequence(self):
        requests.post(f"{self.base_url}/users/register", 
        json={"login": self.username, "email": self.email, "password": self.password})
        self._auth_user()
        
        data = {"p": 23, "q": 31, "seed": 17, "count": 10}
        signature = self._get_signature(data)
        headers = {"Authorization": signature}
        response = requests.post(f"{self.base_url}/bbs/generate", json=data, headers=headers)
        
        print(f"\nГенерация последовательности:")
        print(f"Ожидаемый код: 200")
        print(f"Итог: {response.status_code}")
        self.assertEqual(response.status_code, 200)
    
    def test_07_get_current_sequence(self):
        requests.post(f"{self.base_url}/users/register", 
        json={"login": self.username, "email": self.email, "password": self.password})
        self._auth_user()
        
        data = {"p": 23, "q": 31, "seed": 17, "count": 5}
        signature = self._get_signature(data)
        headers = {"Authorization": signature}
        requests.post(f"{self.base_url}/bbs/generate", json=data, headers=headers)
        
        signature = self._get_signature()
        headers = {"Authorization": signature}
        response = requests.get(f"{self.base_url}/bbs/current", headers=headers)
        
        print(f"\nПолучение текущей последовательности:")
        print(f"Ожидаемый код: 200")
        print(f"Итог: {response.status_code}")
        self.assertEqual(response.status_code, 200)
    
    def test_08_delete_sequence(self):
        requests.post(f"{self.base_url}/users/register", 
        json={"login": self.username, "email": self.email, "password": self.password})
        self._auth_user()
        
        data = {"p": 23, "q": 31, "seed": 17, "count": 3}
        signature = self._get_signature(data)
        headers = {"Authorization": signature}
        requests.post(f"{self.base_url}/bbs/generate", json=data, headers=headers)
        
        signature = self._get_signature()
        headers = {"Authorization": signature}
        response = requests.delete(f"{self.base_url}/bbs/current", headers=headers)
        
        print(f"\nУдаление текущей последовательности:")
        print(f"Ожидаемый код: 200")
        print(f"Итог: {response.status_code}")
        self.assertEqual(response.status_code, 200)

    def test_09_get_history(self):
        requests.post(f"{self.base_url}/users/register", 
        json={"login": self.username, "email": self.email, "password": self.password})
        self._auth_user()
        
        signature = self._get_signature()
        headers = {"Authorization": signature}
        response = requests.get(f"{self.base_url}/users/history", headers=headers)
        
        print(f"\nПолучение истории:")
        print(f"Ожидаемый код: 200")
        print(f"Итог: {response.status_code}")
        self.assertEqual(response.status_code, 200)
    
    def test_10_delete_history(self):
        requests.post(f"{self.base_url}/users/register", 
        json={"login": self.username, "email": self.email, "password": self.password})
        self._auth_user()
        
        signature = self._get_signature()
        headers = {"Authorization": signature}
        response = requests.delete(f"{self.base_url}/users/history", headers=headers)
        
        print(f"\nУдаление истории запросов:")
        print(f"Ожидаемый код: 200")
        print(f"Итог: {response.status_code}")
        self.assertEqual(response.status_code, 200)
    
    def test_11_generate_invalid_params(self):
        requests.post(f"{self.base_url}/users/register", 
        json={"login": self.username, "email": self.email, "password": self.password})
        self._auth_user()
        
        data = {"p": 2, "q": 31, "seed": 17, "iterations": 5}
        signature = self._get_signature(data)
        headers = {"Authorization": signature}
        response = requests.post(f"{self.base_url}/bbs/generate_one", json=data, headers=headers)
        
        print(f"\nГенерация с p <= 3:")
        print(f"Ожидаемый код: 400")
        print(f"Итог: {response.status_code}")
        self.assertEqual(response.status_code, 400)
    
    def test_12_generate_invalid_count(self):
        requests.post(f"{self.base_url}/users/register", 
        json={"login": self.username, "email": self.email, "password": self.password})
        self._auth_user()
        
        data = {"p": 23, "q": 31, "seed": 17, "count": 150}
        signature = self._get_signature(data)
        headers = {"Authorization": signature}
        response = requests.post(f"{self.base_url}/bbs/generate", json=data, headers=headers)
        
        print(f"\nГенерация с count > 100:")
        print(f"Ожидаемый код: 400")
        print(f"Итог: {response.status_code}")
        self.assertEqual(response.status_code, 400)
    
    def test_13_save_parameters(self):
        requests.post(f"{self.base_url}/users/register", 
        json={"login": self.username, "email": self.email, "password": self.password})
        self._auth_user()
        
        data = {"name": "TestParams", "p": 23, "q": 31, "seed": 17}
        signature = self._get_signature(data)
        headers = {"Authorization": signature}
        response = requests.post(f"{self.base_url}/bbs/save_params", json=data, headers=headers)
        
        print(f"\nСохранение параметров генерации:")
        print(f"Ожидаемый код: 200")
        print(f"Итог: {response.status_code}")
        self.assertEqual(response.status_code, 200)
    
    def test_14_get_saved_parameters(self):
        requests.post(f"{self.base_url}/users/register", 
        json={"login": self.username, "email": self.email, "password": self.password})
        self._auth_user()
        
        signature = self._get_signature()
        headers = {"Authorization": signature}
        response = requests.get(f"{self.base_url}/bbs/saved_params", headers=headers)
        
        print(f"\nПолучение сохраненных параметров:")
        print(f"Ожидаемый код: 200")
        print(f"Итог: {response.status_code}")
        self.assertEqual(response.status_code, 200)
    
    def test_15_change_password(self):
        requests.post(f"{self.base_url}/users/register", 
        json={"login": self.username, "email": self.email, "password": self.password})
        self._auth_user()

        new_password = "NewTest123!@#"
        change_data = {
            "old_password": self.password,
            "new_password": new_password
        }
        signature = self._get_signature(change_data)
        headers = {"Authorization": signature}
        response = requests.patch(f"{self.base_url}/users/password", json=change_data, headers=headers)
        
        print(f"\nИзменение пароля:")
        print(f"Ожидаемый код: 200")
        print(f"Итог: {response.status_code}")
        self.assertEqual(response.status_code, 200)
            
if __name__ == "__main__":
    unittest.main()