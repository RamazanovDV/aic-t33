import yaml
import uuid
from datetime import datetime
from pathlib import Path
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette import status

from app.models import Ticket, TicketStatus, User, EmulatorConfig
from app import database
from app.routes import tickets, users, control
from app.services.emulator import Emulator


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = database.load_config()

    users_data = database.load_users()
    if not users_data:
        user_profiles_file = Path(__file__).parent.parent / "data" / "scenarios" / "user_profiles.yaml"
        if user_profiles_file.exists():
            with open(user_profiles_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                for profile in data.get("user_profiles", []):
                    user = User(
                        id=profile["id"],
                        name=profile["name"],
                        position=profile["position"],
                        avatar=profile.get("avatar", ""),
                        created_at=datetime.now(),
                    )
                    users_data.append(user)
                database.save_users(users_data)

    emulator = Emulator(config)
    app.state.emulator = emulator
    yield
    await emulator.stop()


app = FastAPI(
    title="CRM Emulator",
    description="Emulator for testing support agents/bots",
    version="0.1.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")), name="static")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

app.include_router(control.router)
app.include_router(tickets.router)
app.include_router(users.router)


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    emulator = request.app.state.emulator
    tickets_data = database.load_tickets()
    users_data = database.load_users()
    open_count = len([t for t in tickets_data if t.status == TicketStatus.OPEN])
    closed_count = len([t for t in tickets_data if t.status == TicketStatus.CLOSED])

    return templates.TemplateResponse(
        "tickets.html",
        {
            "request": request,
            "tickets": tickets_data,
            "users": users_data,
            "open_count": open_count,
            "closed_count": closed_count,
            "running": emulator.running if emulator else False,
        },
    )


@app.get("/tickets", response_class=HTMLResponse)
async def list_tickets_page(request: Request):
    emulator = request.app.state.emulator
    tickets_data = database.load_tickets()
    return templates.TemplateResponse(
        "tickets.html",
        {
            "request": request,
            "tickets": tickets_data,
            "users": database.load_users(),
            "open_count": len([t for t in tickets_data if t.status == TicketStatus.OPEN]),
            "closed_count": len([t for t in tickets_data if t.status == TicketStatus.CLOSED]),
            "running": emulator.running if emulator else False,
        },
    )


@app.get("/tickets/{ticket_id}", response_class=HTMLResponse)
async def ticket_detail_page(request: Request, ticket_id: str):
    emulator = request.app.state.emulator
    tickets_data = database.load_tickets()
    for ticket in tickets_data:
        if ticket.id == ticket_id:
            return templates.TemplateResponse(
                "ticket_detail.html",
                {
                    "request": request,
                    "ticket": ticket,
                    "running": emulator.running if emulator else False,
                },
            )
    raise HTTPException(status_code=404, detail="Ticket not found")


@app.get("/users", response_class=HTMLResponse)
async def list_users_page(request: Request):
    emulator = request.app.state.emulator
    return templates.TemplateResponse(
        "users.html",
        {
            "request": request,
            "users": database.load_users(),
            "running": emulator.running if emulator else False,
        },
    )


@app.post("/tickets/{ticket_id}/close")
async def close_ticket_action(ticket_id: str, rating: int):
    tickets_data = database.load_tickets()
    for ticket in tickets_data:
        if ticket.id == ticket_id:
            ticket.status = TicketStatus.CLOSED
            ticket.closed_at = datetime.now()
            ticket.rating = rating
            ticket.updated_at = datetime.now()
            database.save_tickets(tickets_data)

            users_data = database.load_users()
            for user in users_data:
                if user.id == ticket.user_id:
                    user.open_tickets = [tid for tid in user.open_tickets if tid != ticket_id]
                    ratings = [
                        t.rating for t in tickets_data if t.user_id == user.id and t.rating is not None
                    ]
                    if ratings:
                        user.rating = sum(ratings) / len(ratings)
                    database.save_users(users_data)
                    break
            return RedirectResponse(url=f"/tickets/{ticket_id}", status_code=status.HTTP_303_SEE_OTHER)
    raise HTTPException(status_code=404, detail="Ticket not found")


@app.post("/tickets/{ticket_id}/reopen")
async def reopen_ticket_action(ticket_id: str):
    tickets_data = database.load_tickets()
    for ticket in tickets_data:
        if ticket.id == ticket_id:
            ticket.status = TicketStatus.OPEN
            ticket.closed_at = None
            ticket.updated_at = datetime.now()
            database.save_tickets(tickets_data)

            users_data = database.load_users()
            for user in users_data:
                if user.id == ticket.user_id:
                    if ticket_id not in user.open_tickets:
                        user.open_tickets.append(ticket_id)
                    database.save_users(users_data)
                    break
            return RedirectResponse(url=f"/tickets/{ticket_id}", status_code=status.HTTP_303_SEE_OTHER)
    raise HTTPException(status_code=404, detail="Ticket not found")


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
