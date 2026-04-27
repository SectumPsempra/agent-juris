from fastapi import APIRouter, Depends

from src.api.dependencies import get_current_user
from src.schemas.api_schemas import CurrentUser

router = APIRouter()


@router.get("")
async def get_me(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    return current_user
