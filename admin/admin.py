from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import insert, delete
from database import get_async_session
from auth.utils import verify_token
from models.models import user, saved_client, saved_seller, gigs_category, gigs_tags
from admin.utils import superuser_check
from admin.schemes import UserResponse, ClientCreate, TagCreate
from typing import List
from admin.schemes import GigCategoryPost
from fastapi.responses import JSONResponse

router_superuser = APIRouter(tags=["Superuser API"])

@router_superuser.get('/clients', response_model=List[UserResponse], summary="Get all Clients")
async def get_clients(
    user_data: dict = Depends(superuser_check),
    session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(select(user).where(user.c.is_client == True))
    clients = result.fetchall()
    if not clients:
        raise HTTPException(status_code=404, detail="No clients found")
    return clients

@router_superuser.post('/clients', summary="Add a Client")
async def add_client(
    client_data: ClientCreate,
    user_data: dict = Depends(superuser_check),
    session: AsyncSession = Depends(get_async_session)
):
    new_client = client_data.dict()
    new_client['is_client'] = True

    result = await session.execute(select(user).where(
        (user.c.username == new_client['username']) | 
        (user.c.email == new_client['email'])
    ))
    existing_user = result.fetchone()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this username or email already exists."
        )

    query = insert(user).values(**new_client)
    await session.execute(query)
    await session.commit()

    return {"detail": "Client added successfully"}

@router_superuser.post('/gigs_category', summary="Create a Gig Category")
async def create_gig_category(
    new_category: GigCategoryPost,
    user_data: dict = Depends(superuser_check),
    session: AsyncSession = Depends(get_async_session)
):
    new_category_data = new_category.dict()
    query = insert(gigs_category).values(**new_category_data).returning(gigs_category)
    result = await session.execute(query)
    created_category = result.fetchone()
    await session.commit()

    if created_category:
        return JSONResponse(
            status_code=201,
            content={
                "message": "Category successfully created"
            }
        )
    else:
        raise HTTPException(status_code=500, detail="Failed to create category")

@router_superuser.delete('/categories/{category_id}', summary="Delete a Category")
async def delete_gig_category(
    category_id: int,
    user_data: dict = Depends(superuser_check),
    session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(select(gigs_category).where(gigs_category.c.id == category_id))
    category_data = result.fetchone()
    if not category_data:
        raise HTTPException(status_code=404, detail="Category not found")

    await session.execute(delete(gigs_category).where(gigs_category.c.id == category_id))
    await session.commit()

    return {"detail": "Category deleted successfully"}

@router_superuser.post('/tags', summary="Create a new tag")
async def create_tag(
    new_tag: TagCreate,
    user_data: dict = Depends(superuser_check),
    session: AsyncSession = Depends(get_async_session)
):
    tag_data = new_tag.dict()
    query = insert(gigs_tags).values(**tag_data)
    await session.execute(query)
    await session.commit()

    return JSONResponse(
        status_code=201,
        content={
            "message": "Tag successfully created"
        }
    )

@router_superuser.delete('/tags/{tag_id}', summary="Delete a tag")
async def delete_tag(
    tag_id: int,
    user_data: dict = Depends(superuser_check),
    session: AsyncSession = Depends(get_async_session)
):
    query = select(gigs_tags.c.id).where(gigs_tags.c.id == tag_id)
    result = await session.execute(query)
    tag_data = result.fetchone()

    if not tag_data:
        raise HTTPException(status_code=404, detail="Tag not found")

    delete_query = delete(gigs_tags).where(gigs_tags.c.id == tag_id)
    await session.execute(delete_query)
    await session.commit()

    return JSONResponse(
        status_code=200,
        content={"message": "Tag successfully deleted"}
    )
