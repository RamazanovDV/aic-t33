import uuid
import yaml
from datetime import datetime
from pathlib import Path
from app.models import Ticket, Message, TicketPriority, MessageAuthor, User
from app.services.llm import LLMClient


SCENARIOS_FILE = Path(__file__).parent.parent.parent / "data" / "scenarios" / "scenarios.yaml"
USER_PROFILES_FILE = Path(__file__).parent.parent.parent / "data" / "scenarios" / "user_profiles.yaml"


def load_scenarios() -> list[dict]:
    if not SCENARIOS_FILE.exists():
        return []
    with open(SCENARIOS_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        return data.get("scenarios", [])


def load_user_profiles() -> list[dict]:
    if not USER_PROFILES_FILE.exists():
        return []
    with open(USER_PROFILES_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        return data.get("user_profiles", [])


async def generate_ticket(user: User, llm: LLMClient) -> Ticket:
    scenarios = load_scenarios()
    if not scenarios:
        raise ValueError("No scenarios defined")

    scenario = scenarios[datetime.now().microsecond % len(scenarios)]
    template = scenario["templates"][datetime.now().microsecond % len(scenario["templates"])]

    prompt = f"""Сгенерируй запрос в техподдержку на основе шаблона.
Шаблон: {template}
Пользователь: {user.name}, {user.position}

Сформатируй ответ как JSON с полями:
- title: краткое название проблемы (1-2 слова)
- description: развернутое описание проблемы (2-3 предложения)

Ответь ТОЛЬКО JSON, без пояснений."""

    result = await llm.generate(prompt, system="Ты — генератор тикетов техподдержки. Отвечай строго в JSON формате.")

    import json
    for line in result.split("\n"):
        try:
            ticket_data = json.loads(line.strip())
            break
        except:
            continue
    else:
        ticket_data = {"title": "Technical issue", "description": template}

    now = datetime.now()
    ticket_id = str(uuid.uuid4())[:8]

    return Ticket(
        id=ticket_id,
        user_id=user.id,
        title=ticket_data.get("title", template),
        description=ticket_data.get("description", template),
        priority=TicketPriority(scenario.get("priority", "medium")),
        category=scenario.get("category", "general"),
        messages=[
            Message(
                id=str(uuid.uuid4())[:8],
                author=MessageAuthor.USER,
                text=ticket_data.get("description", template),
                created_at=now,
            )
        ],
        created_at=now,
        updated_at=now,
    )


async def generate_user_response(ticket: Ticket, llm: LLMClient) -> str:
    messages_history = "\n".join(
        [f"{m.author}: {m.text}" for m in ticket.messages]
    )

    prompt = f"""Тикет пользователя:
{messages_history}

Сгенерируй следующее сообщение пользователя в переписке с техподдержкой.
Учитывай контекст переписки. Пользователь может:
- Уточнять информацию
- Выражать недовольство
- Задавать вопросы
- Предоставлять дополнительные детали

Ответ должен быть коротким (1-2 предложения) и естественным.

Ответь ТОЛЬКО текстом сообщения, без кавычек и пояснений."""

    return await llm.generate(prompt, system="Ты — недовольный пользователь сервиса. Отвечай коротко и эмоционально.")
