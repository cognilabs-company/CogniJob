from fastapi import FastAPI, Depends, HTTPException, APIRouter
from auth.utils import verify_token
from typing import List
from database import get_async_session
from sqlalchemy import insert, update, delete
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from .schemes import Gig, GigPost
from models.models import user, gigs, gigs_category, gigs_skill, gigs_file
from .schemes import GigCategoryPost, GigSkillPost, GigFilePost, GigSkill, GigFile, GigCategoryfull, GigFilefull, \
    GigSkillfull, Gigfull, GigCategory

router_client = APIRouter(tags=["Client API"])


@router_client.post('/gigs', response_model=Gig, summary="Create a Gig")
async def create_gig(new_gig: GigPost, token: dict = Depends(verify_token),
                     session: AsyncSession = Depends(get_async_session)):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")
    user_id = token.get('user_id')

    result = await session.execute(select(user).where(user.c.id == user_id))
    user_data = result.fetchone()
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    if not user_data.is_client:
        raise HTTPException(status_code=403, detail="Only clients can post gigs")

    new_gig_data = new_gig.dict()
    new_gig_data['user_id'] = user_id

    query = insert(gigs).values(**new_gig_data).returning(gigs)
    result = await session.execute(query)
    created_gig = result.fetchone()
    await session.commit()

    return created_gig


@router_client.get('/gigs', response_model=List[Gig], summary="Get all Gigs by User")
async def get_user_gigs(token: dict = Depends(verify_token), session: AsyncSession = Depends(get_async_session)):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")
    user_id = token.get('user_id')

    result = await session.execute(select(gigs).where(gigs.c.user_id == user_id))
    user_gigs = result.fetchall()

    if not user_gigs:
        raise HTTPException(status_code=404, detail="No gigs found for this user")

    return user_gigs


@router_client.delete('/gigs/{gig_id}', summary="Delete a Gig")
async def delete_gig(
        gig_id: int,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")
    user_id = token.get('user_id')

    result = await session.execute(select(user).where(user.c.id == user_id))
    user_data = result.fetchone()
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    result = await session.execute(select(gigs).where(gigs.c.id == gig_id))
    gig_data = result.fetchone()
    if not gig_data or gig_data.user_id != user_id:
        raise HTTPException(status_code=403, detail="You can only delete your own gigs")

    await session.execute(delete(gigs).where(gigs.c.id == gig_id))
    await session.commit()

    return {"detail": "Gig deleted successfully"}


@router_client.get('/gigs/{gig_id}/categories', response_model=List[GigCategory], summary="Get Categories for a Gig")
async def get_gig_categories(gig_id: int, token: dict = Depends(verify_token),
                             session: AsyncSession = Depends(get_async_session)):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")
    user_id = token.get('user_id')

    result = await session.execute(select(user).where(user.c.id == user_id))
    user_data = result.fetchone()
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    result = await session.execute(select(gigs).where(gigs.c.id == gig_id))
    gig_data = result.fetchone()
    if not gig_data:
        raise HTTPException(status_code=404, detail="Gig not found")

    result = await session.execute(select(gigs_category).where(gigs_category.c.gigs_id == gig_id))
    categories = result.fetchall()

    if not categories:
        raise HTTPException(status_code=404, detail="No categories found for this gig")

    return categories


@router_client.post('/gigs_category', summary="Create a Gig Category")
async def create_gig_category(
        new_category: GigCategoryPost,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")
    user_id = token.get('user_id')

    result = await session.execute(select(user).where(user.c.id == user_id))
    user_data = result.fetchone()
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    if not user_data.is_client:
        raise HTTPException(status_code=403, detail="Only clients can post categories")

    result = await session.execute(select(gigs).where(gigs.c.id == new_category.gigs_id))
    gig_data = result.fetchone()
    if not gig_data:
        raise HTTPException(status_code=404, detail="Gig not found")

    if gig_data.user_id != user_id:
        raise HTTPException(status_code=403, detail="You can only add categories to your own gigs")

    new_category_data = new_category.dict()
    query = insert(gigs_category).values(**new_category_data).returning(gigs_category)
    result = await session.execute(query)
    created_category = result.fetchone()
    await session.commit()

    if created_category:

        created_category_dict = {
            'id': created_category[0],
            'category_name': created_category[1],
            'gigs_id': created_category[2]

        }

        created_category_model = GigCategory(**created_category_dict)
        return created_category_model.dict()
    else:
        raise HTTPException(status_code=500, detail="Failed to create category")


@router_client.delete('/gigs/{gig_id}/categories/{category_id}', summary="Delete a Gig Category")
async def delete_gig_category(
        gig_id: int,
        category_id: int,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")

    user_id = token.get('user_id')

    result = await session.execute(select(user).where(user.c.id == user_id))
    user_data = result.fetchone()
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    result = await session.execute(select(gigs).where(gigs.c.id == gig_id))
    gig_data = result.fetchone()
    if not gig_data or gig_data.user_id != user_id:
        raise HTTPException(status_code=403, detail="You can only delete categories from your own gigs")

    result = await session.execute(
        select(gigs_category).where(gigs_category.c.id == category_id, gigs_category.c.gigs_id == gig_id))
    category_data = result.fetchone()
    if not category_data:
        raise HTTPException(status_code=404, detail="Category not found for this gig")

    await session.execute(delete(gigs_category).where(gigs_category.c.id == category_id))
    await session.commit()

    return {"detail": "Category deleted successfully"}


@router_client.get('/gigs/{gig_id}/skill', response_model=List[GigSkill], summary="Get Categories for a Gig")
async def get_gig_skill(gig_id: int, token: dict = Depends(verify_token),
                        session: AsyncSession = Depends(get_async_session)):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")
    user_id = token.get('user_id')

    result = await session.execute(select(user).where(user.c.id == user_id))
    user_data = result.fetchone()
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    result = await session.execute(select(gigs).where(gigs.c.id == gig_id))
    gig_data = result.fetchone()
    if not gig_data:
        raise HTTPException(status_code=404, detail="Gig not found")

    result = await session.execute(select(gigs_skill).where(gigs_skill.c.gigs_id == gig_id))
    skill = result.fetchall()

    if not skill:
        raise HTTPException(status_code=404, detail="No skill found for this gig")

    return skill


@router_client.post('/gigs_skill', summary="Create a Gig Skill")
async def create_gig_skill(
        new_skill: GigSkillPost,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")
    user_id = token.get('user_id')

    result = await session.execute(select(user).where(user.c.id == user_id))
    user_data = result.fetchone()
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    if not user_data.is_client:
        raise HTTPException(status_code=403, detail="Only clients can post skills")

    result = await session.execute(select(gigs).where((gigs.c.id == new_skill.gigs_id) & (gigs.c.user_id == user_id)))
    gig_data = result.fetchone()
    if not gig_data:
        raise HTTPException(status_code=403,
                            detail="Siz bu gigga skill qo'sha olmaysiz, chunki bu sizning gigingiz emas")

    new_skill_data = new_skill.dict()
    query = insert(gigs_skill).values(**new_skill_data).returning(gigs_skill)
    result = await session.execute(query)
    created_skill = result.fetchone()
    await session.commit()

    created_skill_data = {
        'id': created_skill.id,
        'skill_name': created_skill.skill_name,
        'gigs_id': created_skill.gigs_id
    }
    return GigSkill(**created_skill_data)


@router_client.delete('/gigs/{gig_id}/skills/{skill_id}', summary="Delete a Gig Skill")
async def delete_gig_skill(
        gig_id: int,
        skill_id: int,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")

    user_id = token.get('user_id')

    result = await session.execute(select(user).where(user.c.id == user_id))
    user_data = result.fetchone()
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    result = await session.execute(select(gigs).where(gigs.c.id == gig_id))
    gig_data = result.fetchone()
    if not gig_data or gig_data.user_id != user_id:
        raise HTTPException(status_code=403, detail="You can only delete skills from your own gigs")

    result = await session.execute(
        select(gigs_skill).where(gigs_skill.c.id == skill_id, gigs_skill.c.gigs_id == gig_id))
    skill_data = result.fetchone()
    if not skill_data:
        raise HTTPException(status_code=404, detail="Skill not found for this gig")

    await session.execute(delete(gigs_skill).where(gigs_skill.c.id == skill_id))
    await session.commit()

    return {"detail": "Skill deleted successfully"}


@router_client.get('/gigs/{gig_id}/files', response_model=List[GigFile], summary="Get files for a specific gig")
async def get_gig_files(gig_id: int, token: dict = Depends(verify_token),
                        session: AsyncSession = Depends(get_async_session)):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")
    user_id = token.get('user_id')

    result = await session.execute(select(user).where(user.c.id == user_id))
    user_data = result.fetchone()
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    result = await session.execute(select(gigs).where(gigs.c.id == gig_id))
    gig_data = result.fetchone()
    if not gig_data or gig_data.user_id != user_id:
        raise HTTPException(status_code=403, detail="You can only view files for your own gigs")

    result = await session.execute(select(gigs_file).where(gigs_file.c.gigs_id == gig_id))
    files = result.fetchall()

    if not files:
        raise HTTPException(status_code=404, detail="No files found for this gig")

    return files


@router_client.post('/gigs_file', summary="Create a Gig File")
async def create_gig_file(new_file: GigFilePost, token: dict = Depends(verify_token),
                          session: AsyncSession = Depends(get_async_session)):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")
    user_id = token.get('user_id')

    result = await session.execute(select(user).where(user.c.id == user_id))
    user_data = result.fetchone()
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    if not user_data.is_client:
        raise HTTPException(status_code=403, detail="Only clients can post files")

    result = await session.execute(select(gigs).where(gigs.c.id == new_file.gigs_id))
    gig_data = result.fetchone()
    if not gig_data or gig_data.user_id != user_id:
        raise HTTPException(status_code=403, detail="You can only add files to your own gigs")

    new_file_data = new_file.dict()
    query = insert(gigs_file).values(**new_file_data).returning(gigs_file)
    result = await session.execute(query)
    created_file = result.fetchone()
    await session.commit()

    created_file_data = {
        'id': created_file.id,
        'file_url': created_file.file_url,
        'gigs_id': created_file.gigs_id
    }
    return GigFile(**created_file_data)


@router_client.delete('/gigs/{gig_id}/files/{file_id}', summary="Delete a Gig File")
async def delete_gig_file(
        gig_id: int,
        file_id: int,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")

    user_id = token.get('user_id')

    result = await session.execute(select(user).where(user.c.id == user_id))
    user_data = result.fetchone()
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    result = await session.execute(select(gigs).where(gigs.c.id == gig_id))
    gig_data = result.fetchone()
    if not gig_data or gig_data.user_id != user_id:
        raise HTTPException(status_code=403, detail="You can only delete files from your own gigs")

    result = await session.execute(select(gigs_file).where(gigs_file.c.id == file_id, gigs_file.c.gigs_id == gig_id))
    file_data = result.fetchone()
    if not file_data:
        raise HTTPException(status_code=404, detail="File not found for this gig")

    await session.execute(delete(gigs_file).where(gigs_file.c.id == file_id))
    await session.commit()

    return {"detail": "File deleted successfully"}

