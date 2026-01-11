from fastapi import FastAPI
from app.db.session import Base, engine
from app.routes import auth,verbs

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Auth Service")

app.include_router(auth.router)
app.include_router(verbs.router)
