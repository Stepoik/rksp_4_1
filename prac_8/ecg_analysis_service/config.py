import os
import time
from typing import Dict, Any

import requests

# --- Настройки по умолчанию для GitHub ---
# Эти значения должны быть заданы в переменных окружения Kubernetes/Docker или .env
# GITHUB_PAT - Personal Access Token для приватных репозиториев
DEFAULT_REPO_OWNER = "your-github-user"  # Владелец репозитория (например, company-name)
DEFAULT_REPO_NAME = "my-config-repo"  # Имя репозитория
DEFAULT_BRANCH = "main"  # Ветка, из которой брать конфигурацию
DEFAULT_APP_NAME = "python-service"  # Имя приложения (например, chat-service)
DEFAULT_PROFILE = "dev"  # Профиль (например, dev, prod)

MAX_RETRIES = 5
RETRY_DELAY_SECONDS = 5


class ConfigClient:
    """
    Класс для загрузки конфигурации напрямую из GitHub.
    Ожидает конфигурационный файл в формате:
    https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{app_name}-{profile}.yml
    """

    def __init__(self):
        # Настройки GitHub
        self.repo_owner = os.getenv("GITHUB_REPO_OWNER", DEFAULT_REPO_OWNER)
        self.repo_name = os.getenv("GITHUB_REPO_NAME", DEFAULT_REPO_NAME)
        self.branch = os.getenv("GITHUB_BRANCH", DEFAULT_BRANCH)
        self.github_token = os.getenv("GITHUB_PAT")  # Personal Access Token для аутентификации

        # Настройки приложения
        self.app_name = os.getenv("APPLICATION_NAME", DEFAULT_APP_NAME)
        self.profile = os.getenv("PROFILE_NAME", DEFAULT_PROFILE)
        self.config: Dict[str, Any] = {}

        # Первоначальная загрузка
        self.load_config()

    def _simple_yaml_parser(self, yaml_content: str) -> Dict[str, Any]:
        """
        Минимальный парсер, поддерживающий только плоские пары ключ:значение (key: value).
        В продакшене используйте PyYAML.
        """
        config = {}
        for line in yaml_content.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip().strip("'\"")  # Удаляем кавычки, если есть

                # Попытка преобразовать типы (числа, булевы)
                if value.lower() in ('true', 'false'):
                    value = value.lower() == 'true'
                elif value.isdigit():
                    value = int(value)
                elif value.replace('.', '', 1).isdigit():
                    value = float(value)

                config[key] = value
        return config

    def _fetch_config(self) -> str:
        """
        Отправляет HTTP-запрос к GitHub Raw API и возвращает сырой текст YAML.
        """
        filename = f"{self.app_name}-{self.profile}.yml"

        # URL для получения сырого файла с GitHub
        config_url = (
            f"https://raw.githubusercontent.com/"
            f"{self.repo_owner}/{self.repo_name}/{self.branch}/{filename}"
        )

        headers = {}
        if self.github_token:
            # Аутентификация с помощью Personal Access Token (PAT)
            headers['Authorization'] = f'token {self.github_token}'

        for attempt in range(MAX_RETRIES):
            try:
                print(f"Попытка {attempt + 1}: Загрузка конфигурации из {config_url}")
                response = requests.get(config_url, headers=headers, timeout=10)
                response.raise_for_status()  # Вызывает исключение для 4xx/5xx

                return response.text  # Возвращаем сырой текст YAML

            except requests.exceptions.HTTPError as e:
                # 404 Not Found - это нормально, если конфигурации для профиля нет
                if response.status_code == 404:
                    print(f"Предупреждение: Конфигурационный файл {filename} не найден (404).")
                    return ""
                raise
            except requests.exceptions.RequestException as e:
                print(f"Ошибка подключения к GitHub/загрузки: {e}")
                if attempt < MAX_RETRIES - 1:
                    print(f"Повторная попытка через {RETRY_DELAY_SECONDS} сек...")
                    time.sleep(RETRY_DELAY_SECONDS)
                else:
                    print("Не удалось загрузить конфигурацию после всех попыток.")
                    raise ConnectionError("Не удалось получить конфигурацию из GitHub.") from e

        return ""

    def load_config(self):
        """
        Загружает, парсит и сохраняет конфигурацию.
        """
        yaml_content = self._fetch_config()

        if not yaml_content:
            print("Предупреждение: Использование пустой конфигурации.")
            self.config = {}
            return

        # Используем наш простой парсер
        self.config = self._simple_yaml_parser(yaml_content)
        print("Конфигурация успешно загружена и доступна.")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Получает значение по ключу, работает как стандартный словарь.
        """
        return self.config.get(key, default)

    def refresh(self):
        """
        Метод, который можно вызвать через Actuator Webhook для перезагрузки конфигурации.
        """
        print("--- Выполняется обновление конфигурации ---")
        self.load_config()
        # В реальном приложении здесь должна быть реализована логика обновления
        # внутренних компонентов (например, пересоздание пула соединений с БД).