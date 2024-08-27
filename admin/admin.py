from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import insert, delete
from database import get_async_session
from auth.utils import verify_token
from models.models import user, saved_client, saved_seller, gigs_category, gigs_tags,skills,seller,seller_occupation
from admin.utils import superuser_check
from admin.schemes import UserResponse, ClientCreate, TagCreate,SkillCreate1,SellerResponse,UserWithSellerResponse
from typing import List
from admin.schemes import GigCategoryPost
from fastapi.responses import JSONResponse
from sqlalchemy import join
from auth.auth import pwd_context
from client.schemes import GigCategoryResponse,GigTag

from models.models import occupation,seller_occupation
from admin.schemes import OccupCreate1,SellerOccupation

router_superuser = APIRouter(tags=["Superuser API"])


@router_superuser.post('/user', summary="Add a Client")
async def add_client(
    client_data: ClientCreate,
    user_data: dict = Depends(superuser_check),
    session: AsyncSession = Depends(get_async_session)
):
    new_client = client_data.dict()



    result = await session.execute(select(user).where(
        (user.c.username == new_client['username']) | 
        (user.c.email == new_client['email']) |
         (user.c.phone_number == new_client['phone_number']) |
          (user.c.telegram_username == new_client['telegram_username'])
    ))
    existing_user = result.fetchone()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this username or email or phone or username already exists."
        )

   
    hashed_password = pwd_context.hash(client_data.password)

  
    query = insert(user).values(
        first_name=new_client['first_name'],
        last_name=new_client['last_name'],
        email=new_client['email'],
        username=new_client['username'],
        password=hashed_password,
        is_seller=new_client['is_seller'],
        is_client=new_client['is_client'],
        is_superuser=new_client['is_superuser'],
        telegram_username=new_client['telegram_username'],
        phone_number=new_client['phone_number']
    )

  
    await session.execute(query)
    await session.commit()


    return JSONResponse(
        status_code=201,
        content={"message": "User added successfully"}
    )


@router_superuser.get('/users', response_model=List[UserWithSellerResponse], summary="Get all Users with Seller Info")
async def get_all_users_with_seller(
    user_data: dict = Depends(superuser_check),
    session: AsyncSession = Depends(get_async_session)
):

    query = (
        select(user, seller)
        .select_from(join(user, seller, user.c.id == seller.c.user_id, isouter=True))
    )
    
    result = await session.execute(query)
    all_users_with_seller = result.fetchall()
    
    if not all_users_with_seller:
        raise HTTPException(status_code=404, detail="No users found")

    response_data = []

    for user_row in all_users_with_seller:
  
        user_data = {column.name: user_row[i] for i, column in enumerate(user.columns)}
        seller_data = {column.name: user_row[i + len(user.columns)] for i, column in enumerate(seller.columns)}


        if seller_data.get('birth_date'):
            seller_data['birth_date'] = seller_data['birth_date'].isoformat()

  
        seller_data_dict = SellerResponse(**seller_data) if any(seller_data.values()) else None

        response_data.append(UserWithSellerResponse(
            id=user_data['id'],
            first_name=user_data['first_name'],
            last_name=user_data['last_name'],
            email=user_data['email'],
            username=user_data['username'],
            password=user_data['password'],
            registered_date=user_data['registered_date'].isoformat(),
            is_seller=user_data['is_seller'],
            is_client=user_data['is_client'],
            is_superuser=user_data['is_superuser'],
            telegram_username=user_data['telegram_username'],
            phone_number=user_data['phone_number'],
            seller=seller_data_dict
        ))

    return response_data





@router_superuser.get('/user/{user_id}', response_model=UserWithSellerResponse, summary="Get User with Seller Info")
async def get_user_with_seller(
    user_id: int,
    user_data: dict = Depends(superuser_check),
    session: AsyncSession = Depends(get_async_session)
):

    query = (
        select(user, seller)
        .select_from(join(user, seller, user.c.id == seller.c.user_id, isouter=True))
        .where(user.c.id == user_id)
    )
    
    result = await session.execute(query)
    user_with_seller = result.fetchone()
    
    if not user_with_seller:
        raise HTTPException(status_code=404, detail="User not found")

    user_data = {column.name: user_with_seller[i] for i, column in enumerate(user.columns)}
    seller_data = {column.name: user_with_seller[i + len(user.columns)] for i, column in enumerate(seller.columns)}


    if seller_data.get('birth_date'):
        seller_data['birth_date'] = seller_data['birth_date'].isoformat()

 
    seller_data_dict = SellerResponse(**seller_data) if any(seller_data.values()) else None

    response_data = UserWithSellerResponse(
        id=user_data['id'],
        first_name=user_data['first_name'],
        last_name=user_data['last_name'],
        email=user_data['email'],
        username=user_data['username'],
        password=user_data['password'],
        registered_date=user_data['registered_date'].isoformat(),
        is_seller=user_data['is_seller'],
        is_client=user_data['is_client'],
        is_superuser=user_data['is_superuser'],
        telegram_username=user_data['telegram_username'],
        phone_number=user_data['phone_number'],
        seller=seller_data_dict
    )

    return response_data



@router_superuser.delete('/user/{user_id}', summary="Delete a User")
async def delete_user(
    user_id: int,
    user_data: dict = Depends(superuser_check),
    session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(select(user).where(user.c.id == user_id))
    existing_user = result.fetchone()

    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")

 
    query = delete(user).where(user.c.id == user_id)
    await session.execute(query)
    await session.commit()

    return JSONResponse(
        status_code=200,
        content={"message": "User deleted successfully"}
    )

    

@router_superuser.post('/gigs_category', summary="Create a Gigg Category")
async def create_gig_category(
    new_category: GigCategoryPost,
    user_data: dict = Depends(superuser_check),
    session: AsyncSession = Depends(get_async_session)
):
 
    existing_category_query = select(gigs_category.c.id).where(gigs_category.c.category_name == new_category.category_name)
    existing_category_result = await session.execute(existing_category_query)
    existing_category = existing_category_result.scalar()

    if existing_category:
        raise HTTPException(status_code=400, detail="This category already exists")

 
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




@router_superuser.get('/categories', response_model=List[GigCategoryResponse], summary="Get all Gig Categories")
async def get_all_gig_categories(
    session: AsyncSession = Depends(get_async_session)
):
 
    result = await session.execute(select(gigs_category))
    categories_data = result.fetchall()
    
 
    categories = [
        GigCategoryResponse(
            id=category.id,
            category_name=category.category_name
        )
        for category in categories_data
    ]

    return categories





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

    return JSONResponse(
        status_code=200,
        content={"message": "Category deleted successfull"}
    )

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




@router_superuser.get('/tag', response_model=List[GigTag], summary="Get all tags")
async def get_tags(session: AsyncSession = Depends(get_async_session)):
    query = select(gigs_tags)
    result = await session.execute(query)
    tags_data = result.fetchall()
    

    tags_list = [GigTag(id=row.id, tag_name=row.tag_name) for row in tags_data]

    if not tags_list:
        raise HTTPException(status_code=404, detail="No tags found")

    return tags_list



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


@router_superuser.post('/skill_toseller', summary="Create a new skill")
async def create_skill(
    new_skill: SkillCreate1,
    user_data: dict = Depends(superuser_check),
    session: AsyncSession = Depends(get_async_session)
):
    skill_data = new_skill.dict()
    query = insert(skills).values(**skill_data)
    await session.execute(query)
    await session.commit()

    return JSONResponse(
        status_code=201,
        content={
            "message": "Skill successfully created"
        }
    )


from admin.schemes import SellerSkill

@router_superuser.get('/skills', response_model=List[SellerSkill], summary="Get all tags")
async def get_tags(session: AsyncSession = Depends(get_async_session)):
    query = select(skills)
    result = await session.execute(query)
    skills_data = result.fetchall()
    

    skill_list = [SellerSkill(id=row.id, skill_name=row.skill_name) for row in skills_data]

    if not skill_list:
        raise HTTPException(status_code=404, detail="No skill found")

    return skill_list


@router_superuser.delete('/skill/{skill_id}', summary="Delete a skill by ID")
async def delete_skill(
    skill_id: int,
    user_data: dict = Depends(superuser_check),
    session: AsyncSession = Depends(get_async_session)
):

    query = select(skills).where(skills.c.id == skill_id)
    result = await session.execute(query)
    skill_data = result.scalar()
    
    if not skill_data:
        raise HTTPException(status_code=404, detail="Skill not found")

    delete_query = delete(skills).where(skills.c.id == skill_id)
    await session.execute(delete_query)
    await session.commit()

    return JSONResponse(
        status_code=200,
        content={"message": "Skill successfully deleted"}
    )


@router_superuser.post('/occup_toseller', summary="Create a new occup")
async def create_skill(
    new_occup: OccupCreate1,
    user_data: dict = Depends(superuser_check),
    session: AsyncSession = Depends(get_async_session)
):
    occup_data = new_occup.dict()
    query = insert(occupation).values(**occup_data)
    await session.execute(query)
    await session.commit()

    return JSONResponse(
        status_code=201,
        content={
            "message": "occupation successfully created"
        }
    )



@router_superuser.get('/occupations', response_model=List[SellerOccupation], summary="Get all tags")
async def get_occup(session: AsyncSession = Depends(get_async_session)):
    query = select(occupation)
    result = await session.execute(query)
    occup_data = result.fetchall()
    

    occup_list = [SellerOccupation(id=row.id, occup_name=row.occup_name) for row in occup_data]

    if not occup_list:
        raise HTTPException(status_code=404, detail="No occupation found")

    return occup_list



@router_superuser.delete('/occupation/{occupation_id}', summary="Delete an occupation by ID")
async def delete_occupation(
    occupation_id: int,
    user_data: dict = Depends(superuser_check),
    session: AsyncSession = Depends(get_async_session)
):

    query = select(occupation).where(occupation.c.id == occupation_id)
    result = await session.execute(query)
    occup_data = result.scalar()
    
    if not occup_data:
        raise HTTPException(status_code=404, detail="Occupation not found")


    delete_query = delete(occupation).where(occupation.c.id == occupation_id)
    await session.execute(delete_query)
    await session.commit()

    return JSONResponse(
        status_code=200,
        content={"message": "Occupation successfully deleted"}
    )