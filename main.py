import time
from fastapi import Request

from fastapi import FastAPI
from fastapi.params import Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from helpers import information
from auth import authentication

from auth.oAuth2 import get_current_user
from db.database import engine, get_db
from db import models
from routers import expense, analytics, user, aiAgent, categories, account
from routers.schemas import RecordBase, SearchRecord

app = FastAPI()

@app.get("/kaithhealthcheck")
async def leapcell_health_check():
    """ Leapcell-specific health check endpoint.
    Leapcell platform checks this endpoint to verify
    that your service is ready.
    """
    return {"status": "ok"}

@app.get("/kaithheathcheck")
async def leapcell_health_check():
    """ Leapcell-specific health check endpoint.
    Leapcell platform checks this endpoint to verify
    that your service is ready.
    """
    return {"status": "ok"}

@app.middleware("http")
async def add_middleware(request: Request, call_next):
    start_time=time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    response.headers["duration"] = str(duration)
    return response

@app.post("/getbyid")
def get_by_id(request:RecordBase,db:Session=Depends(get_db), current_user:UserAuth=Depends(get_current_user)):
    return information.get_by_id_info(request, db, current_user.user_id)

@app.post("/search")
def search(request:SearchRecord,db:Session=Depends(get_db), current_user:UserAuth=Depends(get_current_user)):
    return information.search(request, db, current_user.user_id)
app.include_router(user.router)
app.include_router(account.router)
app.include_router(authentication.router)
app.include_router(aiAgent.router)
app.include_router(categories.router)
app.include_router(expense.router)
app.include_router(analytics.router)

models.Base.metadata.create_all(engine)

origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "https://singular-meerkat-fdc7a5.netlify.app"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
