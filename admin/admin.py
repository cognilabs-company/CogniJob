from fastapi import Depends, HTTPException, APIRouter, status

from .scheme import UserResponse
from auth.utils import verify_token
from typing import List
from database import get_async_session
from sqlalchemy import insert, update, delete
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.models import user, client, gigs_category

admin_router = APIRouter(tags=["Admin APIS"])


@admin_router.get('/get_all_users', response_model=List[UserResponse])
async def get_all_users(
        session: AsyncSession = Depends(get_async_session),
        token: dict = Depends(verify_token)
):
    if token is None:
        raise HTTPException(status_code=403, detail='Forbidden')

    user_id = token.get('user_id')
    admin = await session.execute(
        select(user).where(
            (user.c.id == user_id) &
            (user.c.is_admin == True)
        )
    )
    if not admin.scalar():
        raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED)

    query = select(user)
    users = await session.execute(query)
    result = users.fetchall()
    return result


@admin_router.delete('/delete_user')
async def delete_user(
        user_id: int,
        session: AsyncSession = Depends(get_async_session),
        token: dict = Depends(verify_token)
):
    if token is None:
        raise HTTPException(status_code=403, detail='Forbidden')

    admin = await session.execute(
        select(user).where(
            (user.c.id == token.get('user_id')) &
            (user.c.is_admin == True)
        )
    )
    if not admin.scalar():
        raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED)

    check_user = select(user).where(user.c.id == user_id)
    data = await session.execute(check_user)
    if not data.fetchone():
        raise HTTPException(status_code=404, detail='User not found')
    query = delete(client).where(client.c.user_id == user_id)
    query1 = delete(user).where(user.c.id == user_id)
    await session.execute(query)
    await session.execute(query1)
    await session.commit()
    return {"success": True}


@admin_router.post('/create_category')
async def create_category(
        category_name: str,
        session: AsyncSession = Depends(get_async_session),
        token: dict = Depends(verify_token)
):
    if token is None:
        raise HTTPException(status_code=403, detail='Forbidden')

    admin = await session.execute(
        select(user).where(
            (user.c.id == token.get('user_id')) &
            (user.c.is_admin == True)
        )
    )
    if not admin.scalar():
        raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED)

    existing_category = await session.execute(
        select(gigs_category).where(gigs_category.c.category_name == category_name)
    )
    if existing_category.scalar():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category already exists")

    query = insert(gigs_category).values(category_name=category_name)
    await session.execute(query)
    await session.commit()
    return {"success": True}


@admin_router.delete('/delete_category/{category_id}')
async def delete_category(
        category_id: int,
        session: AsyncSession = Depends(get_async_session),
        token: dict = Depends(verify_token)
):
    if token is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Forbidden')

    admin = await session.execute(
        select(user).where(
            (user.c.id == token.get('user_id')) &
            (user.c.is_admin == True)
        )
    )
    if not admin.scalar():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    category_to_delete = await session.execute(
        select(gigs_category).where(gigs_category.c.id == category_id)
    )
    category_record = category_to_delete.scalar()

    if not category_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    query = delete(gigs_category).where(gigs_category.c.id == category_id)
    await session.execute(query)
    await session.commit()
    return {"success": True}
