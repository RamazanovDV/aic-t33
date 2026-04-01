import asyncio
from datetime import datetime
from app.models import EmulatorConfig, Ticket, User, TicketStatus, Message, MessageAuthor
from app.services.llm import LLMClient
from app.services.generator import generate_ticket, generate_user_response
from app import database


class Emulator:
    def __init__(self, config: EmulatorConfig):
        self.config = config
        self.running = False
        self.tasks: list[asyncio.Task] = []
        self.llm = LLMClient(config)

    async def start(self):
        if self.running:
            return
        self.running = True
        self.tasks = [
            asyncio.create_task(self._generate_loop()),
            asyncio.create_task(self._response_loop()),
        ]

    async def stop(self):
        self.running = False
        for task in self.tasks:
            task.cancel()
        self.tasks = []

    async def _generate_loop(self):
        while self.running:
            try:
                await asyncio.sleep(self.config.generate_interval)
                if not self.running:
                    break

                tickets = database.load_tickets()
                open_tickets = [t for t in tickets if t.status == TicketStatus.OPEN]

                if len(open_tickets) >= self.config.max_open_tickets:
                    continue

                users = database.load_users()
                if not users:
                    continue

                user = users[datetime.now().microsecond % len(users)]
                ticket = await generate_ticket(user, self.llm)

                tickets.append(ticket)
                database.save_tickets(tickets)

                user.open_tickets.append(ticket.id)
                database.save_users(users)

            except Exception as e:
                print(f"Generate loop error: {e}")

    async def _response_loop(self):
        while self.running:
            try:
                await asyncio.sleep(self.config.response_interval)
                if not self.running:
                    break

                tickets = database.load_tickets()
                open_tickets = [t for t in tickets if t.status == TicketStatus.OPEN]

                if not open_tickets:
                    continue

                for ticket in open_tickets[:3]:
                    try:
                        response = await generate_user_response(ticket, self.llm)
                        message = Message(
                            id=str(datetime.now().timestamp())[:8],
                            author=MessageAuthor.USER,
                            text=response,
                            created_at=datetime.now(),
                        )
                        ticket.messages.append(message)
                        ticket.updated_at = datetime.now()
                        database.save_tickets(tickets)
                    except Exception as e:
                        print(f"Response generation error for ticket {ticket.id}: {e}")

            except Exception as e:
                print(f"Response loop error: {e}")

    def update_config(self, config: EmulatorConfig):
        self.config = config
        self.llm = LLMClient(config)
