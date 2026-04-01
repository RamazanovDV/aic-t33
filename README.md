# CRM Emulator

Эмулятор CRM системы для тестирования агентов техподдержки / ботов.

## Возможности

- Генерация тикетов через LLM (Ollama, OpenAI, Anthropic)
- Эмуляция ответов пользователей по таймеру
- Web-интерфейс для просмотра истории
- REST API для интеграции с ботами
- Переоткрытие тикетов при низкой оценке

## Установка

```bash
pip install -r requirements.txt
```

## Конфигурация

Отредактируй `data/config.json`:

```json
{
    "llm_base_url": "http://localhost:11434/v1",
    "llm_model": "llama3",
    "generate_interval": 30,
    "max_open_tickets": 10
}
```

Добавь пользователей в `data/scenarios/user_profiles.yaml`.

## Запуск

```bash
python -m app.main
```

или

```bash
uvicorn app.main:app --reload
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/tickets` | Список тикетов |
| GET | `/tickets/{id}` | Детали тикета |
| POST | `/tickets/{id}/messages` | Добавить сообщение |
| POST | `/tickets/{id}/close?rating=5` | Закрыть тикет |
| POST | `/tickets/{id}/reopen` | Переоткрыть тикет |
| GET | `/users` | Список пользователей |
| POST | `/emulator/start` | Запустить эмуляцию |
| POST | `/emulator/stop` | Остановить эмуляцию |
| PUT | `/emulator/config` | Изменить настройки |

Документация API: `http://localhost:8000/docs`

## Web UI

- Dashboard: `http://localhost:8000`
- Тикеты: `http://localhost:8000/tickets`
- Пользователи: `http://localhost:8000/users`

## Структура данных

**Ticket**
- `id`, `user_id`, `title`, `description`
- `status`: open/closed
- `priority`: low/medium/high
- `category`, `messages`, `rating`

**User**
- `id`, `name`, `position`, `rating`
- `open_tickets` - список открытых тикетов
