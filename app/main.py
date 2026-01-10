from fastapi import FastAPI
from db.session import Base, engine
from routes import auth

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Auth Service")

app.include_router(auth.router)
