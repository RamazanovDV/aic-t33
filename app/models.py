from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from typing import Optional


class TicketStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"


class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class MessageAuthor(str, Enum):
    USER = "user"
    BOT = "bot"


class Message(BaseModel):
    id: str
    author: MessageAuthor
    text: str
    created_at: datetime


class Ticket(BaseModel):
    id: str
    user_id: str
    title: str
    description: str
    status: TicketStatus = TicketStatus.OPEN
    priority: TicketPriority
    category: str
    messages: list[Message] = Field(default_factory=list)
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None


class User(BaseModel):
    id: str
    name: str
    position: str
    avatar: str = ""
    rating: float = 0.0
    open_tickets: list[str] = Field(default_factory=list)
    created_at: datetime


class EmulatorConfig(BaseModel):
    generate_interval: int = 30
    response_interval: int = 45
    max_open_tickets: int = 10
    reopen_threshold: int = 3
    llm_model: str = "gpt-4"
    llm_base_url: str = "http://localhost:11434/v1"
    llm_api_key: str = "ollama"
