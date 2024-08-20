from models.models import user
from fastapi import HTTPException,status
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends
from auth.utils import verify_token
from database import get_async_session


async def superuser_check(
    token: dict = Depends(verify_token), 
    session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not registered")
    
    user_id = token.get('user_id')
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    result = await session.execute(select(user).where(user.c.id == user_id))
    user_data = result.fetchone()

    if not user_data or not user_data.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    return user_data
