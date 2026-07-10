from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


from database.db import engine, ensure_user_profile_picture_column, ensure_history_columns
from models.user import User
from models.document import Document
from api.settings_api import router as settings_router
from api.chat_api import router as chat_router
from api.upload_api import router as upload_router
from api.user_api import router as user_router
from api.search_api import router as search_router
from api.stats_api import router as stats_router
from models.history import History
from api.history_api import router as history_router
from models.password_otp import PasswordResetOTP
from api.password_api import router as password_router
from models.chat import Chat, ChatMessage
from api.chat_api import router as chat_router
from api.admin_api import router as admin_router

app = FastAPI(
    title="Enterprise AI Knowledge System"
)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

User.metadata.create_all(bind=engine)
Document.metadata.create_all(bind=engine)
History.metadata.create_all(bind=engine)
ensure_user_profile_picture_column()
ensure_history_columns()
PasswordResetOTP.metadata.create_all(bind=engine)
Chat.metadata.create_all(bind=engine)
ChatMessage.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {
        "message": "Enterprise AI Knowledge System Running"
    }


app.include_router(user_router, tags=["Auth"])
app.include_router(search_router, tags=["Search"])
app.include_router(upload_router, tags=["Documents"])
app.include_router(settings_router)
app.include_router(stats_router)
app.include_router(history_router)
app.include_router(password_router)
app.include_router(chat_router, tags=["Chat"])
app.include_router(admin_router)
app.include_router(chat_router)