
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


from database.db import engine, ensure_user_profile_picture_column
from models.user import User
from models.document import Document
from api.settings_api import router as settings_router
from api.upload_api import router as upload_router
from api.user_api import router as user_router
from api.search_api import router as search_router
from api.stats_api import router as stats_router
from models.history import History
from api.history_api import router as history_router
from models.password_otp import PasswordResetOTP
from api.password_api import router as password_router

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
PasswordResetOTP.metadata.create_all(bind=engine)

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