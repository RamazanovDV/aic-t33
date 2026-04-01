import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from app.models import Ticket, TicketStatus, Message, MessageAuthor
from app import database

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.get("", response_model=list[Ticket])
def list_tickets(
    status: Optional[TicketStatus] = None,
    user_id: Optional[str] = None,
):
    tickets = database.load_tickets()
    if status:
        tickets = [t for t in tickets if t.status == status]
    if user_id:
        tickets = [t for t in tickets if t.user_id == user_id]
    return tickets


@router.get("/{ticket_id}", response_model=Ticket)
def get_ticket(ticket_id: str):
    tickets = database.load_tickets()
    for ticket in tickets:
        if ticket.id == ticket_id:
            return ticket
    raise HTTPException(status_code=404, detail="Ticket not found")


@router.post("/{ticket_id}/messages")
def add_message(
    ticket_id: str,
    text: str,
    author: MessageAuthor = MessageAuthor.BOT,
):
    tickets = database.load_tickets()
    for ticket in tickets:
        if ticket.id == ticket_id:
            message = Message(
                id=str(uuid.uuid4())[:8],
                author=author,
                text=text,
                created_at=datetime.now(),
            )
            ticket.messages.append(message)
            ticket.updated_at = datetime.now()
            database.save_tickets(tickets)
            return {"message": "Message added", "data": message}
    raise HTTPException(status_code=404, detail="Ticket not found")


@router.post("/{ticket_id}/close")
def close_ticket(ticket_id: str, rating: int = Query(ge=1, le=5)):
    tickets = database.load_tickets()
    for ticket in tickets:
        if ticket.id == ticket_id:
            ticket.status = TicketStatus.CLOSED
            ticket.closed_at = datetime.now()
            ticket.rating = rating
            ticket.updated_at = datetime.now()
            database.save_tickets(tickets)

            users = database.load_users()
            for user in users:
                if user.id == ticket.user_id:
                    user.open_tickets = [tid for tid in user.open_tickets if tid != ticket_id]
                    ratings = [
                        t.rating
                        for t in tickets
                        if t.user_id == user.id and t.rating is not None
                    ]
                    if ratings:
                        user.rating = sum(ratings) / len(ratings)
                    database.save_users(users)
                    break
            return {"message": "Ticket closed", "rating": rating}
    raise HTTPException(status_code=404, detail="Ticket not found")


@router.post("/{ticket_id}/reopen")
def reopen_ticket(ticket_id: str):
    tickets = database.load_tickets()
    for ticket in tickets:
        if ticket.id == ticket_id:
            ticket.status = TicketStatus.OPEN
            ticket.closed_at = None
            ticket.updated_at = datetime.now()
            database.save_tickets(tickets)

            users = database.load_users()
            for user in users:
                if user.id == ticket.user_id:
                    if ticket_id not in user.open_tickets:
                        user.open_tickets.append(ticket_id)
                    database.save_users(users)
                    break
            return {"message": "Ticket reopened"}
    raise HTTPException(status_code=404, detail="Ticket not found")
