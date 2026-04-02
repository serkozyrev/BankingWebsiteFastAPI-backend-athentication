from typing import List

from fastapi import APIRouter, HTTPException, status, File, UploadFile
from fastapi.params import Depends
from sqlalchemy.orm import Session

from auth.oAuth2 import get_current_user
from db import db_revenue, db_expense, db_aiagent
from db.database import get_db
from helpers import information
from routers.schemas import AgentDisplay, AgentRequestBase

router = APIRouter(
    prefix="/ai",
    tags=["ai_agent"],
)

@router.post('/parse-entry', response_model=AgentDisplay)
async def parse_entry(request: AgentRequestBase, db: Session = Depends(get_db), current_user:UserAuth=Depends(get_current_user)):
    result= await db_aiagent.parse_entry_with_ai(request, db, current_user)
    return result