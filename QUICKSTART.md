# Quickstart — Auralis Epidemic Labs

Levanta el proyecto completo (backend + frontend) en local. Sigue los bloques en
orden. La primera vez ejecuta la sección **Instalación**; en arranques
posteriores basta con **Arranque diario**.

## Requisitos

| Herramienta | Versión usada / mínima        |
| ----------- | ----------------------------- |
| Python      | 3.14 (probado) · 3.11+ debería funcionar |
| Node.js     | 24 (probado) · 20.19+ o 22.12+ (Vite 8) |
| npm         | 11.x (probado)                |

> PostgreSQL **no** es necesario. El `docker-compose.yml` solo trae un Postgres
> opcional bajo el perfil `future-db` para una fase de persistencia futura; el
> backend actual corre íntegramente en memoria.

---

## Instalación (solo la primera vez)

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
```

---

## Arranque diario (dos terminales)

### Terminal 1 — Backend (API en :8000)

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

Disponible en http://127.0.0.1:8000 · documentación interactiva en
http://127.0.0.1:8000/docs

### Terminal 2 — Frontend (UI en :5173)

```bash
cd frontend
npm run dev
```

Abre http://localhost:5173

> El frontend habla con el backend mediante el **proxy de Vite** definido en
> `frontend/vite.config.ts` (`/health`, `/configs`, `/simulations`,
> `/experiments`, `/runs` → `127.0.0.1:8000`). No necesitas configurar URLs.
> Si Vite reporta `Port 5173 is in use`, toma otro puerto automáticamente (5174,
> …); el proxy sigue funcionando igual.

Cuando la cabecera muestre **Connected**, todo está enlazado.

---

## Verificación rápida (opcional pero recomendado)

```bash
# Backend — suite de tests
cd backend && source .venv/bin/activate && pytest

# Frontend — tipos, build y auditoría
cd frontend
npm run typecheck
npm run build
npm audit
```

Estado esperado: backend **26 passed**; frontend sin errores de tipos, build OK,
**0 vulnerabilities**.

---

## Prueba de humo en el navegador

Con ambos servidores arriba, en http://localhost:5173:

1. **Create simulation** — los botones Step / Run / Reset / Export se habilitan.
2. **Run 24 ticks** (o **Step**) — avanzan los ticks y se pueblan las métricas.
3. Panel **Live snapshot** → *Active policies* lista las políticas activas.
4. **Export current run** — escribe archivos en `outputs/runs/<run_id>/`.
5. **Run batch experiment** — corre las variantes y rellena *Scenario comparison*.
6. Consola del navegador sin errores (los `GET /health net::ERR_ABORTED` son
   artefactos benignos del doble render de React StrictMode en dev).

---

## Salidas generadas

| Acción           | Carpeta                       |
| ---------------- | ----------------------------- |
| Export de un run | `outputs/runs/<run_id>/`      |
| Batch experiment | `outputs/reports/<experiment_id>/` |

Las simulaciones viven en memoria del proceso y se pierden al detener el backend;
los exports en disco persisten.

---

## Parar todo

`Ctrl-C` en cada terminal. Si quedó algún proceso suelto ocupando un puerto:

```bash
lsof -nP -iTCP:8000 -sTCP:LISTEN -t | xargs kill   # backend
lsof -nP -iTCP:5173 -sTCP:LISTEN -t | xargs kill   # frontend
```
