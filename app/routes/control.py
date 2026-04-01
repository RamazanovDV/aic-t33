from fastapi import APIRouter, Request
from app.models import EmulatorConfig
from app import database

router = APIRouter(prefix="/emulator", tags=["emulator"])


@router.get("/status")
def get_status(request: Request):
    emulator = request.app.state.emulator
    return {"running": emulator.running, "config": emulator.config}


@router.post("/start")
async def start_emulator(request: Request):
    emulator = request.app.state.emulator
    if emulator.running:
        return {"message": "Already running"}
    await emulator.start()
    return {"message": "Started", "running": True}


@router.post("/stop")
async def stop_emulator(request: Request):
    emulator = request.app.state.emulator
    if not emulator.running:
        return {"message": "Already stopped"}
    await emulator.stop()
    return {"message": "Stopped", "running": False}


@router.get("/config", response_model=EmulatorConfig)
def get_config():
    return database.load_config()


@router.put("/config")
def update_config(config: EmulatorConfig, request: Request):
    database.save_config(config)
    emulator = request.app.state.emulator
    emulator.update_config(config)
    return {"message": "Config updated", "config": config}
