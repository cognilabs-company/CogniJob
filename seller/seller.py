from fastapi import UploadFile,Body
import aiofiles
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, delete,func,update
from sqlalchemy.future import select
from auth.utils import verify_token
from client.client import router_public
from database import get_async_session
from models.models import seller_projects, certificate, experience, occupation, \
    project_files, seller, user
from .schemas import SellerProjectCreate, SellerProject, Certificate, \
    ExperienceCreate, Experience, \
    ProjectFile,SellerUpdateSchema,Profil
from models.models import skills, seller_skills,seller_occupation,occupation,saved_seller
from sqlalchemy import select
from fastapi import APIRouter, Depends, HTTPException
from typing import List ,Dict
from fastapi.responses import JSONResponse
from models.models import gigs
from fastapi import Form
from typing import Optional
from datetime import date

seller_router = APIRouter(tags=['Seller API'])

@seller_router.put("/update/profil", response_model=dict, summary="Update seller profile")
async def update_seller_profile(
    description: Optional[str] = Form(None),
    birth_date: Optional[date] = Form(None),
    image_url: UploadFile = None,
    cv_url: UploadFile = None,
    token: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")

    user_id = token.get('user_id')
    
    seller_query = select(seller.c.id).where(seller.c.user_id == user_id)
    result = await session.execute(seller_query)
    seller_id = result.scalar()

    if seller_id is None:
        raise HTTPException(status_code=404, detail=f"Seller not found for user_id {user_id}")

    out_file1 = None
    out_file2 = None

    if image_url is not None:
        out_file1 = f'/{image_url.filename}'
        async with aiofiles.open(f'image_file/{out_file1}', 'wb') as f:
            content = await image_url.read()
            await f.write(content)

    if cv_url is not None:
        out_file2 = f'/{cv_url.filename}'
        async with aiofiles.open(f'cv_file/{out_file2}', 'wb') as f:
            content = await cv_url.read()
            await f.write(content)

    query = update(seller).where(seller.c.id == seller_id)
    if out_file1 is not None:
        query = query.values(image_url=out_file1)
    if description is not None:
        query = query.values(description=description)
    if out_file2 is not None:
        query = query.values(cv_url=out_file2)
    if birth_date is not None:
        query = query.values(birth_date=birth_date)

    await session.execute(query)
    await session.commit()

    return {"message": "Seller profile updated successfully"}

@seller_router.post("/project/", summary="Create a new project")
async def create_seller_project(
        project: SellerProjectCreate,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")

    user_id = token.get('user_id')


    seller_query = select(seller.c.id).where(seller.c.user_id == user_id)
    result = await session.execute(seller_query)
    seller_id = result.scalar()

    if seller_id is None:
     raise HTTPException(status_code=404, detail=f"Seller not found for user_id {user_id}")

    existing_project_result=await session.execute(
        select(seller_projects).where(
            seller_projects.c.title==project.title,
            seller_projects.c.price ==project.price,
            seller_projects.c.delivery_days==project.delivery_days,
            seller_projects.c.seller_id==seller_id,
            seller_projects.c.description==project.description,
            seller_projects.c.status==True

        )
    )


    existing_project=existing_project_result.fetchone()
    if existing_project:
        raise HTTPException(status_code=400, detail="You have already created a project")



    project_data = project.dict()
    project_data['seller_id'] = seller_id


    query = insert(seller_projects).values(**project_data)
    result = await session.execute(query)
    await session.commit()

    return JSONResponse(
        status_code=201,
        content={"message": "Project successfully added"}
    )



@seller_router.get("/projects/", response_model=List[SellerProject], summary="Get all projects by user")
async def read_seller_projects(
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")

    user_id = token.get('user_id')

    seller_query = select(seller.c.id).where(seller.c.user_id == user_id)
    result = await session.execute(seller_query)
    seller_id = result.scalar()
    
    if seller_id is None:
        raise HTTPException(status_code=404, detail=f"Seller not found for user_id {user_id}")


    result = await session.execute(
        select(seller_projects).where(seller_projects.c.seller_id == seller_id)
    )
    projects = result.fetchall()

    if not projects:
        raise HTTPException(status_code=404, detail="No projects found for this user")

    project_list = []
    for project in projects:
  
        print(project)
        project_id = project[0]  

  
        project_files_result = await session.execute(
            select(project_files).where(project_files.c.seller_project_id == project_id)
        )
        project_files_data = project_files_result.fetchall()

    
       
       

        project_dict = {
            "id": project[0],
            "title": project[1],
         
            "price": project[2],
            "delivery_days": project[3],
            "seller_id": project[4],
            "description": project[5],
            "status": project[6],
            "files": [ProjectFile(id=file.id, file_url=file.file_url, seller_project_id=file.seller_project_id) for file
                      in project_files_data],
           
        }

        project_list.append(SellerProject(**project_dict))

    return project_list



@seller_router.delete("/projects/{project_id}/", summary="Delete a project by ID")
async def delete_seller_project(
        project_id: int,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")

    user_id = token.get('user_id')


    seller_query = select(seller.c.id).where(seller.c.user_id == user_id)
    result = await session.execute(seller_query)
    seller_id = result.scalar()
    
    if seller_id is None:
        raise HTTPException(status_code=404, detail=f"Seller not found for user_id {user_id}")

  
    result = await session.execute(
        select(seller_projects).where(
            seller_projects.c.id == project_id,
            seller_projects.c.seller_id == seller_id
        )
    )
    project = result.scalars().first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found or not owned by the user")

  
    await session.execute(
        delete(project_files).where(project_files.c.seller_project_id == project_id)
    )



    await session.execute(
        delete(seller_projects).where(seller_projects.c.id == project_id)
    )

    await session.commit()


    return JSONResponse(
        status_code=200,
        content={"message": "Project deleted successfully"}
    )



@seller_router.post("/certificate/", summary="Add a new certificate")
async def add_certificate(
        file: UploadFile,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")

    user_id = token.get('user_id')

    seller_query = select(seller.c.id).where(seller.c.user_id == user_id)
    result = await session.execute(seller_query)
    seller_id = result.scalar()

    if seller_id is None:
     raise HTTPException(status_code=404, detail=f"Seller not found for user_id {user_id}")
    
    
    cert_count_query = select(func.count(certificate.c.id)).where(certificate.c.seller_id == seller_id)
    result = await session.execute(cert_count_query)
    cert_count = result.scalar()

    if cert_count >= 3:
        raise HTTPException(status_code=403, detail="Cannot add more than 5 certificates")



    
    if file is not None:
        out_file = f'/{file.filename}'
        async with aiofiles.open(f'certificate_file/{out_file}', 'wb') as f:
            content = await file.read()
            await f.write(content)

    new_cert = certificate.insert().values(
        pdf_url=out_file,
        seller_id=seller_id
    )
    result = await session.execute(new_cert)
    await session.commit()

    return JSONResponse(
        status_code=201,
        content={"message":" Certificate successfully added to the seller"}
    )




@seller_router.get("/certificates/", response_model=List[Certificate], summary="Get all certificates by user")
async def get_certificates(
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")

    user_id = token.get('user_id')

    seller_query = select(seller.c.id).where(seller.c.user_id == user_id)
    result = await session.execute(seller_query)
    seller_id = result.scalar()

    if seller_id is None:
     raise HTTPException(status_code=404, detail=f"Seller not found for user_id {user_id}")
    
    result = await session.execute(
        select(certificate).where(certificate.c.seller_id == seller_id)
    )
    certificates = result.fetchall()



    return certificates



@seller_router.delete("/certificates/{cert_id}/", summary="Delete a certificate by ID")
async def delete_certificate(
        cert_id: int,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")

    user_id = token.get('user_id')

    seller_query = select(seller.c.id).where(seller.c.user_id == user_id)
    result = await session.execute(seller_query)
    seller_id = result.scalar()

    if seller_id is None:
     raise HTTPException(status_code=404, detail=f"Seller not found for user_id {user_id}")
  
    result = await session.execute(select(certificate).where(
        (certificate.c.id == cert_id) & (certificate.c.seller_id == seller_id)
    ))

    cert = result.scalar_one_or_none()

    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")


    await session.execute(certificate.delete().where(certificate.c.id == cert_id))
    await session.commit()

    return JSONResponse(
        status_code=200,
        content={"message": "Certificate deleted successfully"}
    )



@seller_router.post("/experience/",  summary="Add a new experience")
async def add_experience(
        exp: ExperienceCreate,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")

    user_id = token.get('user_id')
  

    seller_query = select(seller.c.id).where(seller.c.user_id == user_id)
    result = await session.execute(seller_query)
    seller_id = result.scalar()
    if seller_id is None:
     raise HTTPException(status_code=404, detail=f"Seller not found for user_id {user_id}")

     
    exp_count_query = select(func.count()).where(experience.c.seller_id == seller_id)
    result = await session.execute(exp_count_query)
    exp_count = result.scalar()

    
    if exp_count >=5:
        raise HTTPException(status_code=403, detail="Cannot add more than 5 experiences")

    existing_exp_result=await session.execute(
        select(experience).where(
            experience.c.company_name == exp.company_name,
            experience.c.start_date == exp.start_date,
            experience.c.end_date == exp.end_date,
            experience.c.seller_id == seller_id,
            experience.c.city == exp.city,
            experience.c.country == exp.country,
            experience.c.job_title == exp.job_title,
            experience.c.description == exp.description

        )
    )


    existing_exp=existing_exp_result.fetchone()
    if existing_exp:
        raise HTTPException(status_code=400, detail="You have already created a experience")

    new_exp = experience.insert().values(
        company_name=exp.company_name,
        start_date=exp.start_date,
        end_date=exp.end_date,
        seller_id=seller_id,
        city=exp.city,
        country=exp.country,
        job_title=exp.job_title,
        description=exp.description
    )
    result = await session.execute(new_exp)
    await session.commit()


    return JSONResponse(
        status_code=201,
        content={"message": "Experience successfully added to the seller"}
    )



@seller_router.get("/experiences/", response_model=List[Experience], summary="Get all experiences by user")
async def get_experiences(
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")

    user_id = token.get('user_id')
  

    seller_query = select(seller.c.id).where(seller.c.user_id == user_id)
    result = await session.execute(seller_query)
    seller_id = result.scalar()
    if seller_id is None:
     raise HTTPException(status_code=404, detail=f"Seller not found for user_id {user_id}")


    result = await session.execute(
        select(experience).where(experience.c.seller_id == seller_id)
    )
    experiences = result.fetchall()

    if not experiences:
        raise HTTPException(status_code=404, detail="No experiences found for this user")

    experience_list = []
    for exp in experiences:
        exp_dict = {
            "id": exp[0],
            "company_name": exp[1],
            "start_date": exp[2],
            "end_date": exp[3],
            "seller_id": exp[4],
            "city": exp[5],
            "country": exp[6],
            "job_title": exp[7],
            "description": exp[8]
        }
        experience_list.append(Experience(**exp_dict))

    return experience_list



@seller_router.delete("/experiences/{exp_id}/", summary="Delete an experience by ID")
async def delete_experience(
        exp_id: int,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")

    user_id = token.get('user_id')

    result = await session.execute(select(experience).where(
        (experience.c.id == exp_id) & (experience.c.seller_id == user_id)
    ))
    exp = result.scalar_one_or_none()

    if not exp:
        raise HTTPException(status_code=404, detail="Experience not found")


    await session.execute(experience.delete().where(experience.c.id == exp_id))
    await session.commit()


    return JSONResponse(
        status_code=200,
        content={"message": "Experience deleted successfully"}
    )



@seller_router.get("/experiences/{exp_id}/", response_model=List[Experience], summary="Get an experience by ID")
async def get_experience(
        exp_id: int,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")

    user_id = token.get('user_id')

    seller_query = select(seller.c.id).where(seller.c.user_id == user_id)
    result = await session.execute(seller_query)
    seller_id = result.scalar()
    
    if seller_id is None:
        raise HTTPException(status_code=404, detail=f"Seller not found for user_id {user_id}")

 
    result = await session.execute(select(experience).where(
        (experience.c.id == exp_id) & (experience.c.seller_id == seller_id)
    ))
    exp = result.fetchall()  

    if not exp:
        raise HTTPException(status_code=404, detail="Experience not found")

 
    return exp



@seller_router.post("/project-file/", summary="Add a new project file")
async def add_project_files(
        file: UploadFile,
        seller_project_id: int,

        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")

    user_id = token.get('user_id')

   
    seller_query = select(seller.c.id).where(seller.c.user_id == user_id)
    result = await session.execute(seller_query)
    seller_id = result.scalar()
    
    if seller_id is None:
        raise HTTPException(status_code=404, detail=f"Seller not found for user_id {user_id}")

   
    project_query = select(seller_projects.c.id).where(
        (seller_projects.c.id == seller_project_id) &
        (seller_projects.c.seller_id == seller_id)
    )
    project_result = await session.execute(project_query)
    project = project_result.scalar()

    if project is None:
        raise HTTPException(status_code=403, detail="You are not allowed to add files to this project")
    

    if file is not None:
        out_file = f'/{file.filename}'
        async with aiofiles.open(f'project_file/{out_file}', 'wb') as f:
            content = await file.read()
            await f.write(content)
  
    new_proj_file = project_files.insert().values(
        file_url=out_file,
        seller_project_id=seller_project_id
    )
    await session.execute(new_proj_file)
    await session.commit()

    return JSONResponse(
        status_code=201,
        content={"message": "File successfully added to the project"}
    )



@seller_router.get("/project-files/", summary="Get all project files for a seller")
async def get_project_files(
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")

    user_id = token.get('user_id')

    # Seller ID ni olish
    seller_query = select(seller.c.id).where(seller.c.user_id == user_id)
    result = await session.execute(seller_query)
    seller_id = result.scalar()

    if seller_id is None:
        raise HTTPException(status_code=404, detail="Seller not found")


    files_query = select(project_files).select_from(
        project_files.join(seller_projects, project_files.c.seller_project_id == seller_projects.c.id)
    ).where(
        seller_projects.c.seller_id == seller_id
    )

    result = await session.execute(files_query)
    files = result.fetchall()

    if not files:
        raise HTTPException(status_code=404, detail="No project files found")

    project_files_list = []
    for file in files:
        project_files_list.append({
            "id": file.id,
            "file_url": file.file_url,
            "seller_project_id": file.seller_project_id
        })

    return project_files_list



@seller_router.delete("/project-files/{proj_file_id}/", summary="Delete a project file by ID")
async def delete_project_file(
        proj_file_id: int,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")

    user_id = token.get('user_id')


    result = await session.execute(select(project_files).where(
        (project_files.c.id == proj_file_id)
    ))
    proj_file = result.scalar_one_or_none()

    if not proj_file:
        raise HTTPException(status_code=404, detail="Project file not found")

   
    await session.execute(project_files.delete().where(project_files.c.id == proj_file_id))
    await session.commit()

    return JSONResponse(
        status_code=200,
        content={"message": "Project file deleted successfully"}
    )



@seller_router.post("/seller/skill/", summary="Add multiple skills to seller profile")
async def add_skills_to_seller(
    skills_ids: List[int],  
    token: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")
    user_id = token.get('user_id')

    seller_result = await session.execute(select(seller.c.id).where(seller.c.user_id == user_id))
    seller_id = seller_result.scalar()
    if not seller_id:
        raise HTTPException(status_code=404, detail=f"Seller not found for user_id {user_id}")

    
    skill_result = await session.execute(select(skills.c.id).where(skills.c.id.in_(skills_ids)))
    valid_skill_ids = set(skill_result.scalars().all())
    invalid_skill_ids = set(skills_ids) - valid_skill_ids
    if invalid_skill_ids:
        raise HTTPException(status_code=404, detail=f"Skills with IDs {list(invalid_skill_ids)} not found")

    existing_skills_result = await session.execute(select(seller_skills.c.skill_id).where(seller_skills.c.seller_id == seller_id))
    existing_skill_ids = set(existing_skills_result.scalars().all())

    new_skill_ids = valid_skill_ids - existing_skill_ids
    max_skills_limit = 3  
    if len(existing_skill_ids) + len(new_skill_ids) > max_skills_limit:
        raise HTTPException(status_code=400, detail=f"Cannot add more than {max_skills_limit} skills")


    if new_skill_ids:
        values_to_insert = [{"seller_id": seller_id, "skill_id": skill_id} for skill_id in new_skill_ids]
        insert_query = insert(seller_skills).values(values_to_insert)
        await session.execute(insert_query)
        await session.commit()


    return JSONResponse(
        status_code=201,
        content={"message": "Skills added to seller profile successfully"}
    )



@seller_router.get("/seller/skills/", summary="Occupations")
async def get_seller_profile(
    token: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_async_session)
) -> Dict:
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")
    user_id = token.get('user_id')

    seller_result = await session.execute(select(seller.c.id).where(seller.c.user_id == user_id))
    seller_id = seller_result.scalar()
    if not seller_id:
        raise HTTPException(status_code=404, detail=f"Seller not found for user_id {user_id}")
  
    seller_query = select(seller).where(seller.c.id == seller_id)
    seller_result = await session.execute(seller_query)
    seller_data = seller_result.fetchone()

    if not seller_data:
        raise HTTPException(status_code=404, detail=f"Seller not found with id {seller_id}")

    skills_query = select(skills).join(seller_skills).where(seller_skills.c.seller_id == seller_id)
    skills_result = await session.execute(skills_query)
    skills_list = [{"id": skill.id, "skill_name": skill.skill_name} for skill in skills_result.fetchall()]

    return {
        "skills":skills_list
    }



@seller_router.delete("/seller/skill/{skill_id}", summary="Remove a skill from seller profile")
async def delete_skill_from_seller(
    skill_id: int,
    token: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")
    user_id = token.get('user_id')

  
    seller_result = await session.execute(select(seller.c.id).where(seller.c.user_id == user_id))
    seller_id = seller_result.scalar()
    if not seller_id:
        raise HTTPException(status_code=404, detail=f"Seller not found for user_id {user_id}")

    skill_result = await session.execute(select(skills.c.id).where(skills.c.id == skill_id))
    if skill_result.scalar() is None:
        raise HTTPException(status_code=404, detail=f"Skill with ID {skill_id} not found")

    existing_skill_result = await session.execute(select(seller_skills.c.skill_id).where(
        seller_skills.c.seller_id == seller_id,
        seller_skills.c.skill_id == skill_id
    ))
    if existing_skill_result.scalar() is None:
        raise HTTPException(status_code=404, detail="Skill not found in seller profile")


    delete_query = delete(seller_skills).where(
        seller_skills.c.seller_id == seller_id,
        seller_skills.c.skill_id == skill_id
    )
    await session.execute(delete_query)
    await session.commit()


    return JSONResponse(
        status_code=200,
        content={"message": "Skill removed from seller profile successfully"}
    )



@seller_router.post("/seller/occupation/", summary="Add multiple occupations to seller profile")
async def add_occupations_to_seller(
    occupation_ids: List[int],  
    token: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")
    user_id = token.get('user_id')

    seller_result = await session.execute(select(seller.c.id).where(seller.c.user_id == user_id))
    seller_id = seller_result.scalar()
    if not seller_id:
        raise HTTPException(status_code=404, detail=f"Seller not found for user_id {user_id}")


    occupation_result = await session.execute(select(occupation.c.id).where(occupation.c.id.in_(occupation_ids)))
    valid_occupation_ids = set(occupation_result.scalars().all())
    invalid_occupation_ids = set(occupation_ids) - valid_occupation_ids
    if invalid_occupation_ids:
        raise HTTPException(status_code=404, detail=f"Occupations with IDs {list(invalid_occupation_ids)} not found")


    existing_occupations_result = await session.execute(select(seller_occupation.c.occupation_id).where(seller_occupation.c.seller_id == seller_id))
    existing_occupation_ids = set(existing_occupations_result.scalars().all())

    new_occupation_ids = valid_occupation_ids - existing_occupation_ids
    max_occupations_limit = 5  
    if len(existing_occupation_ids) + len(new_occupation_ids) > max_occupations_limit:
        raise HTTPException(status_code=400, detail=f"Cannot add more than {max_occupations_limit} occupations")

   
    if new_occupation_ids:
        values_to_insert = [{"seller_id": seller_id, "occupation_id": occ_id} for occ_id in new_occupation_ids]
        insert_query = insert(seller_occupation).values(values_to_insert)
        await session.execute(insert_query)
        await session.commit()

    return JSONResponse(
        status_code=201,
        content={"message": "Occupations added to seller profile successfully"}
    )



@seller_router.get("/seller/occupations/", summary="Occupations")
async def get_seller_profile(
    token: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_async_session)
) -> Dict:
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")
    user_id = token.get('user_id')

    seller_result = await session.execute(select(seller.c.id).where(seller.c.user_id == user_id))
    seller_id = seller_result.scalar()
    if not seller_id:
        raise HTTPException(status_code=404, detail=f"Seller not found for user_id {user_id}")
  
    seller_query = select(seller).where(seller.c.id == seller_id)
    seller_result = await session.execute(seller_query)
    seller_data = seller_result.fetchone()

    if not seller_data:
        raise HTTPException(status_code=404, detail=f"Seller not found with id {seller_id}")

    occupations_query = select(occupation).join(seller_occupation).where(seller_occupation.c.seller_id == seller_id)
    occupations_result = await session.execute(occupations_query)
    occupations_list = [{"id": occ.id, "occup_name": occ.occup_name} for occ in occupations_result.fetchall()]

    return {
        "occupaitions":occupations_list
    }



@seller_router.delete("/seller/occupation/{occupation_id}", summary="Remove an occupation from seller profile")
async def delete_occupation_from_seller(
    occupation_id: int,
    token: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")
    user_id = token.get('user_id')


    seller_result = await session.execute(select(seller.c.id).where(seller.c.user_id == user_id))
    seller_id = seller_result.scalar()
    if not seller_id:
        raise HTTPException(status_code=404, detail=f"Seller not found for user_id {user_id}")

  
    occupation_result = await session.execute(select(occupation.c.id).where(occupation.c.id == occupation_id))
    if occupation_result.scalar() is None:
        raise HTTPException(status_code=404, detail=f"Occupation with ID {occupation_id} not found")


    existing_occupation_result = await session.execute(select(seller_occupation.c.occupation_id).where(
        seller_occupation.c.seller_id == seller_id,
        seller_occupation.c.occupation_id == occupation_id
    ))
    if existing_occupation_result.scalar() is None:
        raise HTTPException(status_code=404, detail="Occupation not found in seller profile")


    delete_query = delete(seller_occupation).where(
        seller_occupation.c.seller_id == seller_id,
        seller_occupation.c.occupation_id == occupation_id
    )
    await session.execute(delete_query)
    await session.commit()


    return JSONResponse(
        status_code=200,
        content={"message": "Occupation removed from seller profile successfully"}
    )



@seller_router.get("/seller/profile/", summary="Get seller's profile including skills, certificates, experience, and seller details")
async def get_seller_profile(
    token: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_async_session)
) -> Dict:
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")
    user_id = token.get('user_id')

    seller_result = await session.execute(select(seller.c.id).where(seller.c.user_id == user_id))
    seller_id = seller_result.scalar()
    if not seller_id:
        raise HTTPException(status_code=404, detail=f"Seller not found for user_id {user_id}")
  
    seller_query = select(seller).where(seller.c.id == seller_id)
    seller_result = await session.execute(seller_query)
    seller_data = seller_result.fetchone()

    if not seller_data:
        raise HTTPException(status_code=404, detail=f"Seller not found with id {seller_id}")

    seller_info = {
        "id": seller_data.id,
        "user_id": seller_data.user_id,
        "image_url": seller_data.image_url,
        "description": seller_data.description,
        "cv_url": seller_data.cv_url,
        "birth_date": seller_data.birth_date
    }


    skills_query = select(skills).join(seller_skills).where(seller_skills.c.seller_id == seller_id)
    skills_result = await session.execute(skills_query)
    skills_list = [{"id": skill.id, "skill_name": skill.skill_name} for skill in skills_result.fetchall()]


    experience_query = select(experience).where(experience.c.seller_id == seller_id)
    experience_result = await session.execute(experience_query)
    experience_list = [{
        "id": exp.id,
        "company_name": exp.company_name,
        "start_date": exp.start_date,
        "end_date": exp.end_date,
        "city": exp.city,
        "country": exp.country,
        "job_title": exp.job_title,
        "description": exp.description
    } for exp in experience_result.fetchall()]


    certificates_query = select(certificate).where(certificate.c.seller_id == seller_id)
    certificates_result = await session.execute(certificates_query)
    certificates_list = [{"id": cert.id, "pdf_url": cert.pdf_url} for cert in certificates_result.fetchall()]

    occupations_query = select(occupation).join(seller_occupation).where(seller_occupation.c.seller_id == seller_id)
    occupations_result = await session.execute(occupations_query)
    occupations_list = [{"id": occ.id, "occup_name": occ.occup_name} for occ in occupations_result.fetchall()]


    return {
        "seller": seller_info,
        "skills": skills_list,
        "experience": experience_list,
        "certificates": certificates_list,
        "occupations":occupations_list
    }




@seller_router.post('/saved_clients', summary="Save a Client")
async def save_client(
    client_id: int, 
    token: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")
    
    user_id = token.get('user_id')

    seller_result = await session.execute(select(seller.c.id).where(seller.c.user_id == user_id))
    seller_id = seller_result.scalar()
    if not seller_id:
        raise HTTPException(status_code=404, detail=f"Seller not found for user_id {user_id}")
    
    result = await session.execute(select(user).where(user.c.id == user_id))
    user_data = result.fetchone()
    
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user_data.is_seller:
        raise HTTPException(status_code=403, detail="Only sellers can save clients")

    result = await session.execute(select(user).where(user.c.id == client_id))
    client_data = result.fetchone()

    if not client_data or not client_data.is_client:
        raise HTTPException(status_code=404, detail="Client not found or not a client")

    query = insert(saved_seller).values(user_id=client_id, seller_id=seller_id)
    await session.execute(query)
    await session.commit()

    return JSONResponse(
        status_code=201,
        content={"message": "Client saved successfully"}
    )



@seller_router.get('/saved_clients', summary="Get Saved Clients")
async def get_saved_clients(
    token: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")
    
    user_id = token.get('user_id')

    seller_result = await session.execute(select(seller.c.id).where(seller.c.user_id == user_id))
    seller_id = seller_result.scalar()
    if not seller_id:
        raise HTTPException(status_code=404, detail=f"Seller not found for user_id {user_id}")
    result = await session.execute(select(saved_seller).where(saved_seller.c.seller_id == seller_id))
    saved_clients = result.fetchall()

    if not saved_clients:
        raise HTTPException(status_code=404, detail="No saved clients found")

    clients = []
    for sc in saved_clients:
        clients.append({
            "id": sc.id,
            "seller_id": sc.seller_id,
            "save_client_id": sc.user_id,
        })

    return clients



@seller_router.delete('/saved_clients/{saved_client_id}', summary="Delete Saved Client")
async def delete_saved_client(
    saved_client_id: int,
    token: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")
    
    user_id = token.get('user_id')


    seller_result = await session.execute(select(seller.c.id).where(seller.c.user_id == user_id))
    seller_id = seller_result.scalar()
    if not seller_id:
        raise HTTPException(status_code=404, detail=f"Seller not found for user_id {user_id}")
    result = await session.execute(select(saved_seller).where(saved_seller.c.seller_id == seller_id, saved_seller.c.user_id == saved_client_id))
    saved_client_data = result.fetchone()

    if not saved_client_data:
        raise HTTPException(status_code=404, detail="Saved client not found")

    await session.execute(delete(saved_seller).where(saved_seller.c.user_id == saved_client_id))
    await session.commit()


    return JSONResponse(
        status_code=200,
        content={"message": "Saved client deleted successfully"}
    )





@seller_router.get("/gigs/{gig_id}/apply", response_model=Dict[str, str])
async def apply_for_gig(
    gig_id: int,
    token: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")
    
    user_id = token.get('user_id')

 
    seller_result = await session.execute(select(seller.c.id).where(seller.c.user_id == user_id))
    seller_id = seller_result.scalar_one_or_none()
    if not seller_id:
        raise HTTPException(status_code=404, detail=f"Seller not found for user_id {user_id}")


    result = await session.execute(select(gigs).where(gigs.c.id == gig_id))
    gig = result.fetchone()
    if not gig:
        raise HTTPException(status_code=404, detail="Gig not found")


    client_result = await session.execute(select(user).where(user.c.id == gig.user_id))
    client = client_result.fetchone() 
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    return {
        "telegram_username": client.telegram_username,
        "phone_number": client.phone_number
    }




@router_public.get("/sellers/{occupation_name}/", summary="Get sellers by occupation name")
async def get_sellers_by_occupation_name(
    occupation_name: str,
    session: AsyncSession = Depends(get_async_session)
) -> Dict:
 
    occupation_query = select(occupation.c.id).where(occupation.c.occup_name.ilike(f"%{occupation_name}%"))
    occupation_result = await session.execute(occupation_query)
    occupation_ids = set(occupation_result.scalars().all())
    
    if not occupation_ids:
        raise HTTPException(status_code=404, detail="No occupations found with the given name")


    seller_query = select(seller.c.id, seller.c.user_id, seller.c.image_url, seller.c.description, seller.c.cv_url, seller.c.birth_date).join(
        seller_occupation,
        seller.c.id == seller_occupation.c.seller_id
    ).where(seller_occupation.c.occupation_id.in_(occupation_ids))
    
    seller_result = await session.execute(seller_query)
    sellers = [{
        "id": s.id,
        "user_id": s.user_id,
        "image_url": s.image_url,
        "description": s.description,
        "cv_url": s.cv_url,
        "birth_date": s.birth_date
    } for s in seller_result.fetchall()]

    return {"sellers": sellers}



@router_public.get('/sellers_by_skill/{skil_name}', summary="Get Sellers by Skill")
async def get_sellers_by_skill(
    skill_name: str,
    session: AsyncSession = Depends(get_async_session)
):

    result = await session.execute(
        select(skills.c.id).where(skills.c.skill_name == skill_name)
    )
    skill_data = result.fetchone()

    if not skill_data:
        raise HTTPException(status_code=404, detail="Skill not found")

    skill_id = skill_data.id

   
    result = await session.execute(
        select(seller).join(seller_skills).where(seller_skills.c.skill_id == skill_id)
    )
    sellers = result.fetchall()

    if not sellers:
        raise HTTPException(status_code=404, detail="No sellers found with the given skill")

    seller_profiles = []
    for s in sellers:
        seller_profiles.append({
            "id": s.id,
            "user_id": s.user_id,
            "image_url": s.image_url,
            "description": s.description,
            "cv_url": s.cv_url,
            "birth_date": s.birth_date
        })

    return seller_profiles



@router_public.get("/seller/profile/{seller_id}", summary="Get seller's profile including skills, certificates, experience, and seller details")
async def get_seller_profile(
    seller_id:int,
    session: AsyncSession = Depends(get_async_session)
) -> Dict:
    seller_query = select(seller).where(seller.c.id == seller_id)
    seller_result = await session.execute(seller_query)
    seller_data = seller_result.fetchone()

    if not seller_data:
        raise HTTPException(status_code=404, detail=f"Seller not found with id {seller_id}")

    seller_info = {
        "id": seller_data.id,
        "user_id": seller_data.user_id,
        "image_url": seller_data.image_url,
        "description": seller_data.description,
        "cv_url": seller_data.cv_url,
        "birth_date": seller_data.birth_date
    }


    skills_query = select(skills).join(seller_skills).where(seller_skills.c.seller_id == seller_id)
    skills_result = await session.execute(skills_query)
    skills_list = [{"id": skill.id, "skill_name": skill.skill_name} for skill in skills_result.fetchall()]

    experience_query = select(experience).where(experience.c.seller_id == seller_id)
    experience_result = await session.execute(experience_query)
    experience_list = [{
        "id": exp.id,
        "company_name": exp.company_name,
        "start_date": exp.start_date,
        "end_date": exp.end_date,
        "city": exp.city,
        "country": exp.country,
        "job_title": exp.job_title,
        "description": exp.description
    } for exp in experience_result.fetchall()]

    certificates_query = select(certificate).where(certificate.c.seller_id == seller_id)
    certificates_result = await session.execute(certificates_query)
    certificates_list = [{"id": cert.id, "pdf_url": cert.pdf_url} for cert in certificates_result.fetchall()]

    occupations_query = select(occupation).join(seller_occupation).where(seller_occupation.c.seller_id == seller_id)
    occupations_result = await session.execute(occupations_query)
    occupations_list = [{"id": occ.id, "occup_name": occ.occup_name} for occ in occupations_result.fetchall()]


    return {
        "seller": seller_info,
        "skills": skills_list,
        "experience": experience_list,
        "certificates": certificates_list,
        "occupations":occupations_list
    }


