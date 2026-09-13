# 👥 TeamFinder Bot — Telegram-бот для поиска людей в команду и проектов

Полностью готовый к продакшену асинхронный Telegram-бот на **Python 3.10+**, **aiogram 3.x** и **SQLAlchemy 2.0 (async)** с поддержкой **SQLite** и **PostgreSQL**, системой модерации заявок, защищенным двухсторонним чатом между администратором и кандидатом, управлением анкетами и опциональной интеграцией **Google Gemini AI**.

---

## 📌 Содержание
1. [Архитектура и возможности](#-архитектура-и-возможности)
2. [Структура проекта](#-структура-проекта)
3. [Установка Python](#1-установка-python)
4. [Создание Telegram-бота через @BotFather и получение BOT_TOKEN](#2-создание-telegram-бота-через-botfather)
5. [Как узнать свой Telegram User ID](#3-как-узнать-свой-telegram-user-id)
6. [Настройка окружения и файла .env](#4-настройка-окружения-и-файла-env)
7. [Установка зависимостей](#5-установка-зависимостей)
8. [Запуск бота локально](#6-запуск-бота-локально)
9. [Развертывание на VPS (systemd)](#7-развертывание-на-vps-systemd)
10. [Обновление бота](#8-обновление-бота)
11. [Тестирование (pytest)](#9-тестирование)

---

## 🧠 Архитектура и возможности

- **Два режима анкет:**
  - `🔎 Найти команду`: анкета специалиста (роль, ключевой стек, опыт, цели, готовность по времени, портфолио/о себе).
  - `👥 Найти участника`: заявка проекта (описание продукта/стартапа, требуемая роль, стек, опыт, занятость, условия).
- **Пошаговый UX (FSM):**
  - Кнопки `⬅️ Назад` и `❌ Отмена` на каждом шаге.
  - Валидация длины текста и форматов контактов.
  - Экран предпросмотра с кнопками `✅ Отправить`, `✏️ Изменить`, `❌ Отмена`.
- **Админ-панель:**
  - Доступ строго по числовому `user_id` из конфигурации `ADMIN_IDS` (никаких уязвимых проверок по username!).
  - Интерактивные inline-кнопки под заявкой:
    - `✅ Принять` — перевод в статус `accepted`, автоматическое поздравление кандидату, замена кнопки на `🟢 ПРИНЯТО` с защитой от повторного клика.
    - `❌ Отклонить` — перевод в статус `rejected`, корректное уведомление кандидату без раскрытия внутренних причин, фиксация статуса `🔴 ОТКЛОНЕНО`.
    - `💬 Связаться` — безопасный двухсторонний чат через бота: админ отправляет сообщение через бота, кандидат получает его с кнопкой «Ответить» и пишет ответ, который передается админу!
    - `🚫 Заблокировать` — мгновенная блокировка пользователя и отклонение спам-заявок.
- **Раздел «📋 Моя анкета»:**
  - Просмотр актуальной анкеты и её текущего статуса модерации.
  - Удаление/отзыв анкеты и возможность создать новую.
  - Защита от создания дубликатов и спама.
- **База данных:**
  - Асинхронный SQLAlchemy 2.0 (по умолчанию SQLite через `aiosqlite`, переключение на PostgreSQL заменой одной строчки в `.env`).
  - Таблицы: `users`, `applications`, `admin_messages`, `audit_logs`.
- **Логирование:**
  - Структурированное логирование всех событий, ошибок и времени выполнения без утечки токенов.

---

## 📁 Структура проекта

```text
teamfinder/
├── bot/
│   ├── handlers/            # Обработчики команд, сообщений и callback-кнопок
│   │   ├── common.py        # /start, /help, отмена
│   │   ├── questionnaire.py # Пошаговые анкеты "Найти команду" и "Найти участника"
│   │   ├── my_profile.py    # Раздел "Моя анкета" (просмотр, удаление, редактирование)
│   │   ├── admin.py         # /admin, статистика, списки заявок, поиск
│   │   ├── admin_actions.py # Логика кнопок: Принять, Отклонить, Блокировать
│   │   └── chat_relay.py    # Двухсторонний безопасный чат админ <-> пользователь
│   ├── keyboards/           # Клавиатуры бота
│   │   ├── reply.py         # Главное меню, Назад, Отмена
│   │   └── inline.py        # Карточки заявок, подтверждение, админ-панель
│   ├── services/            # Бизнес-логика
│   │   ├── user.py          # Пользователи, блокировки, статистика
│   │   ├── application.py   # CRUD и статусы анкет, поиск, фильтры
│   │   ├── chat.py          # Сохранение и получение истории сообщений
│   │   └── ai_helper.py     # Интеграция Gemini (опционально)
│   ├── database/            # Работа с БД (SQLAlchemy 2.0 async)
│   │   ├── base.py          # DeclarativeBase
│   │   ├── models.py        # Модели User, Application, AdminMessage, AuditLog
│   │   └── session.py       # Async engine и sessionmaker
│   ├── states/              # FSM состояния (aiogram.fsm)
│   │   ├── questionnaire.py # Состояния шагов анкеты
│   │   └── admin.py         # Состояния ввода сообщения и поиска
│   ├── middlewares/         # Промежуточные слои
│   │   ├── auth.py          # Проверка блокировки и прав администратора
│   │   └── logging.py       # Структурированное логирование событий
│   └── utils/
│       ├── formatters.py    # HTML-форматирование карточек и текста
│       └── validators.py    # Валидация входных данных
├── config/
│   └── settings.py          # Конфигурация Pydantic Settings
├── tests/                   # Набор тестов (pytest)
├── .env.example             # Пример переменных окружения
├── requirements.txt         # Зависимости проекта
├── README.md                # Документация
└── main.py                  # Главная точка входа
```

---

## 1. Установка Python

Для работы бота требуется **Python 3.10 или новее**.

### Ubuntu / Debian Linux:
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git
python3 --version
```

### macOS:
```bash
brew install python
python3 --version
```

### Windows:
1. Скачайте установщик с официального сайта [python.org](https://www.python.org/downloads/).
2. **Обязательно** установите галочку: **«Add python.exe to PATH»**.
3. Проверьте в терминале PowerShell: `python --version`.

---

## 2. Создание Telegram-бота через @BotFather

1. Откройте Telegram и найдите официального бота **[@BotFather](https://t.me/BotFather)** (с синей галочкой).
2. Нажмите `Start` или отправьте команду:
   ```text
   /newbot
   ```
3. Введите отображаемое имя вашего бота (например: `TeamFinder Community`).
4. Введите юзернейм бота, заканчивающийся на `bot` (например: `my_teamfinder_test_bot`).
5. BotFather выдаст сообщение с вашим **HTTP API токеном**:
   ```text
   Use this token to access the HTTP API:
   7123456789:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```
6. Скопируйте и сохраните этот токен — это значение переменной `BOT_TOKEN`.

---

## 3. Как узнать свой Telegram User ID

Доступ к админ-панели и управлению заявками защищен по числовому **Telegram User ID**:

1. Откройте в Telegram любого бота для определения ID, например **[@userinfobot](https://t.me/userinfobot)** или **[@getmyid_bot](https://t.me/getmyid_bot)**.
2. Отправьте боту любое сообщение или нажмите `/start`.
3. Бот ответит информацией с вашим числовым `Id`:
   ```text
   Id: 123456789
   First name: Alex
   Username: @alex
   ```
4. Число `123456789` — это ваш `ADMIN_IDS`. Если администраторов несколько, укажите их через запятую: `123456789,987654321`.

---

## 4. Настройка окружения и файла .env

1. Перейдите в каталог с проектом:
   ```bash
   cd teamfinder
   ```
2. Создайте файл `.env` из примера `.env.example`:
   ```bash
   cp .env.example .env
   ```
3. Откройте `.env` в текстовом редакторе (`nano .env`):
   ```env
   # Токен от @BotFather
   BOT_TOKEN=7123456789:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxx

   # Telegram ID администраторов через запятую
   ADMIN_IDS=123456789

   # База данных (для локальной работы оставляем SQLite)
   DATABASE_URL=sqlite+aiosqlite:///teamfinder.db

   # Уровень логирования
   LOG_LEVEL=INFO
   ```

---

## 5. Установка зависимостей

Рекомендуется использовать изолированное виртуальное окружение (`venv`):

```bash
# 1. Создание виртуального окружения
python3 -m venv venv

# 2. Активация виртуального окружения:
# На Linux / macOS:
source venv/bin/activate
# На Windows PowerShell:
# .\venv\Scripts\Activate.ps1

# 3. Обновление pip и установка зависимостей:
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 6. Запуск бота локально

```bash
python main.py
```

После запуска в консоли появится лог:
```text
2026-09-13 14:00:00 [INFO] teamfinder.main: Starting TeamFinder Bot...
2026-09-13 14:00:00 [INFO] bot.database.session: Database tables initialized successfully.
2026-09-13 14:00:00 [INFO] teamfinder.main: TeamFinder Bot initialized successfully. Configured admins: [123456789]
2026-09-13 14:00:01 [INFO] teamfinder.main: Bot is now polling for Telegram updates...
```

Теперь откройте бота в Telegram и отправьте команду `/start`!

---

## 7. Развертывание на VPS (systemd)

Для бесперебойной круглосуточной работы бота на сервере (Ubuntu/Debian) настройте службу **systemd**:

1. Подключитесь к VPS по SSH:
   ```bash
   ssh root@YOUR_SERVER_IP
   ```
2. Склонируйте проект в каталог `/opt/teamfinder`:
   ```bash
   git clone <URL_ВАШЕГО_РЕПОЗИТОРИЯ> /opt/teamfinder
   cd /opt/teamfinder
   ```
3. Создайте виртуальное окружение и установите пакеты:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   nano .env  # Вставьте ваш реальный BOT_TOKEN и ADMIN_IDS
   ```
4. Создайте systemd-сервис:
   ```bash
   sudo nano /etc/systemd/system/teamfinder.service
   ```
   Вставьте следующее содержимое:
   ```ini
   [Unit]
   Description=TeamFinder Telegram Bot Service
   After=network.target

   [Service]
   Type=simple
   User=root
   WorkingDirectory=/opt/teamfinder
   ExecStart=/opt/teamfinder/venv/bin/python /opt/teamfinder/main.py
   Restart=always
   RestartSec=5
   EnvironmentFile=/opt/teamfinder/.env

   [Install]
   WantedBy=multi-user.target
   ```
5. Активируйте и запустите службу:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable teamfinder.service
   sudo systemctl start teamfinder.service
   ```
6. Проверка статуса и логов:
   ```bash
   # Проверить статус
   sudo systemctl status teamfinder.service

   # Смотреть живые логи
   sudo journalctl -u teamfinder.service -f
   ```

---

## 8. Обновление бота

Чтобы обновить бота на сервере:
```bash
cd /opt/teamfinder
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart teamfinder.service
```

---

## 9. Тестирование

Проект содержит полный автоматизированный тестовый набор на **pytest**, покрывающий все 18 сценариев из технического задания:

```bash
pytest tests/ -v
```
