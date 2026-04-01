from typing import List

from fastapi import APIRouter
from fastapi.params import Depends
from sqlalchemy.orm import Session
from auth.oAuth2 import get_current_user

from db import db_analytics
from db.database import get_db
from routers.schemas import Analytics, UserAuth

router = APIRouter(
    prefix="/analytics",
    tags=["analytics"],
)

# image_url_types =['absolute', 'relative']

@router.get('')
def analytics_info(db: Session = Depends(get_db), current_user:UserAuth=Depends(get_current_user)):

    info_chequing_line_of_credit=db_analytics.analytics(db, current_user.user_id, ['Chequing', 'LineOfCredit'])
    info_visa=db_analytics.analytics(db, current_user.user_id, ['Visa'])
    return{'infoChequingLineOfCredit': info_chequing_line_of_credit, 'infoVisa': info_visa}
