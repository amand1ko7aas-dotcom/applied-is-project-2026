from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database.db import init_db
from app.routers.documents import router as hatshy_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="АРМ Хатшы — Кафедра құжат айналымы ИС",
    description="Кафедра хатшысының автоматтандырылған жұмыс орны (REST API: Құжаттар, Тапсырмалар, Қызметкерлер)",
    version="2.0.0",
    lifespan=lifespan,
)

app.include_router(hatshy_router)


@app.get("/")
def health_check():
    return {"status": "ok", "system": "АРМ Хатшы — Кафедра құжат айналымы"}
