from fastapi import FastAPI, Depends, HTTPException, APIRouter
from auth.utils import verify_token
from typing import List
from database import get_async_session
from sqlalchemy import insert, update, delete
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.models import user, gigs, gigs_category, gigs_skill, gigs_file
from schemes import GigCategoryfull, GigFilefull, GigSkillfull, Gigfull, Gig
from auth.auth import auth_router
from client.client import router_client

app = FastAPI(title='Fitnessapp', version='1.0.0')
router = APIRouter()


@router.get('/gigss', response_model=List[Gig], summary="Get all Gigs aaa User")
async def get_public_gigs(session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(gigs))
    gigs_list = result.fetchall()

    if not gigs_list:
        raise HTTPException(status_code=404, detail="No gigs found")

    return gigs_list


def convert_to_gig_model(gig_data, categories, skills, files):
    categories_list = [GigCategoryfull(id=cat.id, category_name=cat.category_name) for cat in categories]
    skills_list = [GigSkillfull(id=skill.id, skill_name=skill.skill_name) for skill in skills]
    files_list = [GigFilefull(id=file.id, file_url=file.file_url) for file in files]

    return Gigfull(
        id=gig_data.id,
        gigs_title=gig_data.gigs_title,
        duration=gig_data.duration,
        price=gig_data.price,
        description=gig_data.description,
        user_id=gig_data.user_id,
        categories=categories_list,
        skills=skills_list,
        files=files_list
    )


@router.get('/gigs/{gig_id}/full', response_model=Gigfull, summary="Get Gig with all details")
async def get_gig_with_details(gig_id: int, session: AsyncSession = Depends(get_async_session)):
    # Fetch gig data
    result = await session.execute(select(gigs).where(gigs.c.id == gig_id))
    gig_data = result.fetchone()
    if not gig_data:
        raise HTTPException(status_code=404, detail="Gig not found")

    # Fetch categories
    result = await session.execute(select(gigs_category).where(gigs_category.c.gigs_id == gig_id))
    categories = result.fetchall()

    # Fetch skills
    result = await session.execute(select(gigs_skill).where(gigs_skill.c.gigs_id == gig_id))
    skills = result.fetchall()

    # Fetch files
    result = await session.execute(select(gigs_file).where(gigs_file.c.gigs_id == gig_id))
    files = result.fetchall()

    return convert_to_gig_model(gig_data, categories, skills, files)

app.include_router(router, prefix='/main')
app.include_router(auth_router, prefix='/auth')
app.include_router(router_client, prefix='/client')
