# 3D Print Error Handler

Сервис для мониторинга 3D печати в реальном времени. Используя камеру, он отслеживает процесс печати и автоматически выявляет ошибки. В случае обнаружения проблемы, сервис отправляет уведомление пользователю.

## Описание

Этот проект предназначен для наблюдения за процессом 3D печати. Камера следит за ходом печати и может выявить ошибки, такие как: недоразвитие слоев, деформация объектов и другие типичные проблемы 3D печати. В случае обнаружения ошибки, пользователю отправляется уведомление.

## Установка

1. **Клонируйте репозиторий:**

   Склонируйте проект в свою рабочую папку:
   ```bash
   git clone https://github.com/Kraksi/3Dprint_camera.git
   cd <имя_папки_с_проектом>

2. **Создайте виртуальное окружение:**

   Создайте виртуальное окружение для изоляции зависимостей:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # для Linux/MacOS
   venv\Scripts\activate     # для Windows

3. **Установите зависимости:**

   Установите все необходимые библиотеки из файла requirements.txt:
   ```bash
   pip install -r requirements.txt

4. **Запустите приложение:**

   Запустите сервер с помощью Uvicorn:
   ```bash
   uvicorn main:app --reload

5. **Доступность:**

   После запуска сервер будет доступен по адресу: http://localhost:8000/

6. **Тестирование:**

   Можно запустить тестирование
   ```bash
   pytest


## Использование

1. Для работы с сервисом вам достаточно подключить веб-камеру. Если у вас подключено несколько камер, убедитесь, что выбрана нужная. По умолчание установлена камера с индексом "0". В сервисе можно подключить только одну веб-камеру
2. В базе данных уже добавлен user для теста приложения Логин: admin Password: Admin
3. После запуска сервера введите логин и пароль.
4. Процесс 3D печати будет автоматически отслеживаться.
5. Если обнаружена ошибка в печати, сервис уведомит вас.

## Зависимости

Проект использует следующие технологии и библиотеки:

1. FastAPI – для создания API.
2. Jinja – для рендеринга HTML-шаблонов.
3. SQLAlchemy – для работы с базой данных.
4. Pytest – для написания и выполнения тестов.

Применяются следующие паттерны проектирования:

1. Singleton
2. Repository
3. Observer
   
