from fastapi import FastAPI
from app.db.session import Base, engine
from app.routes import auth

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Auth Service")

app.include_router(auth.router)
