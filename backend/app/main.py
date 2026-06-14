"""FastAPI application composition root."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import configs, experiments, health, simulations
from app.core.errors import AuralisError, ConfigNotFoundError, SimulationNotFoundError
from app.core.logging import configure_logging
from app.core.settings import get_settings

settings = get_settings()
configure_logging(settings.log_level)

app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    description="API for socio-cognitive epidemic simulation workflows.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(configs.router)
app.include_router(simulations.router)
app.include_router(experiments.router)


@app.exception_handler(AuralisError)
async def handle_auralis_error(request: Request, error: AuralisError) -> JSONResponse:
    """Translate expected application errors at the HTTP boundary."""

    del request
    status_code = 404 if isinstance(error, (ConfigNotFoundError, SimulationNotFoundError)) else 400
    return JSONResponse(status_code=status_code, content={"detail": str(error)})
