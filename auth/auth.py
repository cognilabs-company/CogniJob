from typing import List
import aiofiles
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from passlib.context import CryptContext
from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from sqlalchemy.exc import NoResultFound
from .schemes import UserRegister, UserInDB, UserLogin, UserResponse
from .utils import generate_token, verify_token
from database import get_async_session
from models.models import user , seller

auth_router = APIRouter()
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


@auth_router.post('/register')
async def register(
        user1: UserRegister,
        session: AsyncSession = Depends(get_async_session)
):
        if user1.password1 != user1.password2:
            raise HTTPException(status_code=400, detail='Passwords are not the same!')

        username_query = select(user).where(user.c.username == user1.username)
        email_query = select(user).where(user.c.email == user1.email)

        username_result = await session.execute(username_query)
        email_result = await session.execute(email_query)

        if username_result.first():
            raise HTTPException(status_code=400, detail="Username already in use")
        if email_result.first():
            raise HTTPException(status_code=400, detail="Email already in use")
        password=pwd_context.hash(user1.password1)
        user_count=await  session.execute(select(user))
        user_count = len(user_count.fetchall())

        is_superuser=user_count==0

        user_in_db=UserInDB(**dict(user1),password=password,registered_date=datetime.utcnow(),is_superuser=is_superuser)
        query=insert(user).values(**dict(user_in_db))
        await session.execute(query)
        await session.commit()
        return {'success': True, 'message': 'Account created successfully'}

# @auth_router.post('/login')
# async def login(user_date: UserLogin, session: AsyncSession = Depends(get_async_session)):
#     query = select(user).where(user.c.username == user_date.username)
#     userdata = await session.execute(query)
#     user_result = userdata.one_or_none()
#     if user_result is None:
#         return {'success': False, 'message': 'Email or password is not correct!'}
#     else:
#         if pwd_context.verify(user_date.password, user_result.password):
#             token = generate_token(user_result.id)
#             return token
#         else:
#             return {'success': False, 'message': 'Email or password is not correct!'}



@auth_router.post('/login')
async def login(user_date: UserLogin, session: AsyncSession = Depends(get_async_session)):
    query = select(user).where(user.c.username == user_date.username)
    userdata = await session.execute(query)

    try:
        userdata = userdata.one()
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Username or password is incorrect")
    if pwd_context.verify(user_date.password, userdata.password):
        token = generate_token(userdata.id)
        return token
    else:
        raise HTTPException(status_code=404, detail='Username or password is incorrect')
    
    


@auth_router.get('/get_current_user')
async def get_current_user(
    token: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        return HTTPException(status_code=403, detail='Forbidden')

    user_id = token.get('user_id')
    user_info = select(user).where(user.c.id == user_id)
    user_result = await session.execute(user_info)
    user_data = user_result.fetchone()
    print(user_data)
    if user_data is None:
        raise HTTPException(status_code=404, detail='User not found')

    user_dict = {
        "id": user_data[0],
        "first_name": user_data[1],
        "last_name": user_data[2],
        "email": user_data[3],
        "username": user_data[4],
        "registered_date": user_data[6],
        "is_seller": user_data[7],
        "is_client": user_data[8]
    }
    return user_dict


@auth_router.post('/add_seller')
async def get_users(
    image: UploadFile = None,
    cv: UploadFile = None,
    description: str = None,
    birth_date: datetime = None,
    active_gigs: int = None,
    session: AsyncSession = Depends(get_async_session),
    token: dict = Depends(verify_token)
):
    if token is None:
        return HTTPException(status_code=403, detail='Forbidden')
    user_id = token.get('user_id')

    user_query = select(user).filter(user.c.id == user_id, user.c.is_seller == True)
    user_result = await session.execute(user_query)
    user_record = user_result.scalars().first()

    if not user_record:
        raise HTTPException(status_code=400, detail='User is not a seller or does not exist')
    query = select(seller).where(seller.c.user_id == user_id)
    result = await session.execute(query)
    existing_seller = result.scalars().first()

    if existing_seller:
        raise HTTPException(status_code=400, detail='Seller already exists')

    image_path = None
    if image:
        image_path = f'seller_photos/{user_id}_{image.filename}'
        async with aiofiles.open(image_path, 'wb') as f:
            content = await image.read()
            await f.write(content)

    cv_path = None
    if cv:
        cv_path = f'seller_cvs/{user_id}_{cv.filename}'
        async with aiofiles.open(cv_path, 'wb') as f:
            content = await cv.read()
            await f.write(content)

    query_insert = insert(seller).values(
        user_id=user_id,
        description=description,
        birth_date=birth_date,
        active_gigs=active_gigs,
        image_url=image_path,
        cv_url=cv_path
    )
    await session.execute(query_insert)
    await session.commit()

    return {"message": "Seller added successfully"}