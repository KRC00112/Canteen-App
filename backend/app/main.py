from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.router import router as auth_router
from app.cart.router import router as cart_router
from app.database.database import init_db
from app.inventory.router import router as inventory_router
from app.menu.router import router as menu_router
from app.orders.router import router as orders_router
from app.staff.router import router as staff_router
from app.users.router import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Canteen Pre-Order System API",
    description="SOA backend for the Canteen Pre-Order System (CS612 Group 4).",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(menu_router)
app.include_router(inventory_router)
app.include_router(cart_router)
app.include_router(orders_router)
app.include_router(staff_router)


@app.get("/", tags=["Health"])
def health():
    return {"service": "canteen-backend", "status": "ok"}
