from fastapi import FastAPI
from app.db.session import Base, engine
from app.routes import auth,verbs,grammar,quiz,paytm,games
from fastapi.middleware.cors import CORSMiddleware

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Auth Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js
    allow_credentials=True,
    allow_methods=["*"],  # IMPORTANT
    allow_headers=["*"],  # IMPORTANT
)

app.include_router(auth.router)
app.include_router(verbs.router)
app.include_router(quiz.router)
app.include_router(grammar.router)
app.include_router(paytm.router)
app.include_router(games.router)
# app.include_router(chat.router)
