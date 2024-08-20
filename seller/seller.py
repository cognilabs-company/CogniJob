from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from auth.utils import verify_token
from database import get_async_session
from models.models import seller_projects, certificate, language, experience, occupation, projects_skills, \
    project_files, seller, saved_client, user
from .schemas import SellerProjectCreate, SellerProject, CertificateCreate, Certificate, LanguageCreate, Language, \
    ExperienceCreate, Experience, OccupationCreate, Occupation, ProjectSkillCreate, ProjectSkill, ProjectFileCreate, \
    ProjectFile, Seller

seller_router = APIRouter(tags=['Seller API'])


@seller_router.get("/seller/", response_model=Seller, summary="Get details of the current seller")
async def get_seller(
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")

    user_id = token.get('user_id')

    # Fetch seller details
    seller_info_query = select(seller).where(seller.c.user_id == user_id)
    seller_result = await session.execute(seller_info_query)
    seller_data = seller_result.fetchone()

    if not seller_data:
        raise HTTPException(status_code=404, detail="Seller not found")

    seller_id = seller_data[0]

    # Fetch languages
    result_languages = await session.execute(
        select(language).where(language.c.seller_id == seller_id)
    )
    languages_data = result_languages.fetchall()
    languages_list = [Language(id=lan.id, lan_name=lan.lan_name) for lan in languages_data]

    # Fetch experiences
    result_experiences = await session.execute(
        select(experience).where(experience.c.seller_id == seller_id)
    )
    experiences_data = result_experiences.fetchall()
    experiences_list = [Experience(
        id=exp.id,
        company_name=exp.company_name,
        start_date=exp.start_date,
        end_date=exp.end_date,
        city=exp.city,
        country=exp.country,
        job_title=exp.job_title,
        description=exp.description
    ) for exp in experiences_data]

    # Fetch occupations
    result_occupations = await session.execute(
        select(occupation).where(occupation.c.seller_id == seller_id)
    )
    occupations_data = result_occupations.fetchall()
    occupations_list = [Occupation(id=occ.id, occup_name=occ.occup_name) for occ in occupations_data]

    # Fetch certificates
    result_certificates = await session.execute(
        select(certificate).where(certificate.c.seller_id == seller_id)
    )
    certificates_data = result_certificates.fetchall()
    certificates_list = [Certificate(id=cert.id, pdf_url=cert.pdf_url) for cert in certificates_data]

    # Assemble seller data without projects
    seller_info = Seller(
        id=seller_data.id,
        user_id=seller_data.user_id,
        image_url=seller_data.image_url,
        description=seller_data.description,
        cv_url=seller_data.cv_url,
        birth_date=seller_data.birth_date,
        active_gigs=seller_data.active_gigs,
        languages=languages_list,
        experiences=experiences_list,
        occupations=occupations_list,
        certificates=certificates_list
    )

    return seller_info


@seller_router.post("/projects/", response_model=SellerProject, summary="Create a new project")
async def create_seller_project(
        project: SellerProjectCreate,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")

    user_id = token.get('user_id')

    new_project = seller_projects.insert().values(
        title=project.title,
        category=project.category,
        price=project.price,
        delivery_days=project.delivery_days,
        seller_id=user_id,
        description=project.description,
        status=project.status
    )
    result = await session.execute(new_project)
    await session.commit()

    return {**project.dict(), "id": result.inserted_primary_key[0], "seller_id": user_id}


@seller_router.get("/projects/", response_model=List[SellerProject], summary="Get all projects by user")
async def read_seller_projects(
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")

    user_id = token.get('user_id')

    result = await session.execute(
        select(seller_projects).where(seller_projects.c.seller_id == user_id)
    )
    projects = result.fetchall()

    if not projects:
        raise HTTPException(status_code=404, detail="No projects found for this user")

    project_list = []
    for project in projects:
        project_id = project[0]  # Unpack the tuple to get the project id

        project_files_result = await session.execute(
            select(project_files).where(project_files.c.seller_project_id == project_id)
        )
        project_files_data = project_files_result.fetchall()

        project_skills_result = await session.execute(
            select(projects_skills).where(projects_skills.c.seller_project_id == project_id)
        )
        project_skills_data = project_skills_result.fetchall()

        project_dict = {
            "id": project[0],
            "title": project[1],
            "category": project[2],
            "price": project[3],
            "delivery_days": project[4],
            "seller_id": project[5],
            "description": project[6],
            "status": project[7],
            "files": [ProjectFile(id=file.id, file_url=file.file_url, seller_project_id=file.seller_project_id) for file
                      in project_files_data],
            "skills": [ProjectSkill(id=skill.id, skill_name=skill.skill_name, seller_project_id=skill.seller_project_id)
                       for skill in project_skills_data],
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

    # Check if the project exists and belongs to the user
    result = await session.execute(
        select(seller_projects).where(
            seller_projects.c.id == project_id,
            seller_projects.c.seller_id == user_id
        )
    )
    project = result.scalars().first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found or not owned by the user")

    # Delete associated project files
    await session.execute(
        delete(project_files).where(project_files.c.seller_project_id == project_id)
    )

    # Delete associated project skills
    await session.execute(
        delete(projects_skills).where(projects_skills.c.seller_project_id == project_id)
    )

    # Delete the project itself
    await session.execute(
        delete(seller_projects).where(seller_projects.c.id == project_id)
    )

    await session.commit()

    return {"detail": "Project deleted successfully"}


@seller_router.post("/certificates/", response_model=Certificate, summary="Add a new certificate")
async def add_certificate(
        cert: CertificateCreate,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")

    user_id = token.get('user_id')

    new_cert = certificate.insert().values(
        pdf_url=cert.pdf_url,
        seller_id=user_id
    )
    result = await session.execute(new_cert)
    await session.commit()

    return {**cert.dict(), "id": result.inserted_primary_key[0], "seller_id": user_id}


# DELETE Certificate by ID
@seller_router.delete("/certificates/{cert_id}/", summary="Delete a certificate by ID")
async def delete_certificate(
        cert_id: int,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")

    user_id = token.get('user_id')

    # Check if the certificate exists and belongs to the user
    result = await session.execute(select(certificate).where(
        (certificate.c.id == cert_id) & (certificate.c.seller_id == user_id)
    ))
    cert = result.scalar_one_or_none()

    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")

    # Delete the certificate
    await session.execute(certificate.delete().where(certificate.c.id == cert_id))
    await session.commit()

    return {"detail": "Certificate deleted successfully"}


# GET all certificates
@seller_router.get("/certificates/", response_model=List[Certificate], summary="Get all certificates by user")
async def get_certificates(
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")

    user_id = token.get('user_id')

    result = await session.execute(
        select(certificate).where(certificate.c.seller_id == user_id)
    )
    certificates = result.fetchall()

    if not certificates:
        raise HTTPException(status_code=404, detail="No certificates found for this user")

    certificate_list = []
    for cert in certificates:
        cert_dict = {
            "id": cert[0],
            "pdf_url": cert[1],
            "seller_id": cert[2]
        }
        certificate_list.append(Certificate(**cert_dict))

    return certificate_list


# GET Certificate by ID
# @seller_router.get("/certificates/{cert_id}/", response_model=Certificate, summary="Get a certificate by ID")
# async def get_certificate(
#         cert_id: int,
#         token: dict = Depends(verify_token),
#         session: AsyncSession = Depends(get_async_session)
# ):
#     if token is None:
#         raise HTTPException(status_code=401, detail="Not registered")
#
#     user_id = token.get('user_id')
#
#     # Retrieve the certificate by ID and user ID
#     result = await session.execute(select(certificate).where(
#         (certificate.c.id == cert_id) & (certificate.c.seller_id == user_id)
#     ))
#     cert = result.scalar_one_or_none()
#
#     if not cert:
#         raise HTTPException(status_code=404, detail="Certificate not found")
#
#     return cert


@seller_router.post("/languages/", response_model=Language, summary="Add a new language")
async def add_language(
        lang: LanguageCreate,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")

    user_id = token.get('user_id')

    new_lang = language.insert().values(
        lan_name=lang.lan_name,
        seller_id=user_id
    )
    result = await session.execute(new_lang)
    await session.commit()

    return {**lang.dict(), "id": result.inserted_primary_key[0], "seller_id": user_id}


# DELETE Language by ID
@seller_router.delete("/languages/{lang_id}/", summary="Delete a language by ID")
async def delete_language(
        lang_id: int,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")

    user_id = token.get('user_id')

    # Check if the language exists and belongs to the user
    result = await session.execute(select(language).where(
        (language.c.id == lang_id) & (language.c.seller_id == user_id)
    ))
    lang = result.scalar_one_or_none()

    if not lang:
        raise HTTPException(status_code=404, detail="Language not found")

    # Delete the language
    await session.execute(language.delete().where(language.c.id == lang_id))
    await session.commit()

    return {"detail": "Language deleted successfully"}


# GET all languages
@seller_router.get("/languages/", response_model=List[Language], summary="Get all languages by user")
async def get_languages(
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")

    user_id = token.get('user_id')

    result = await session.execute(
        select(language).where(language.c.seller_id == user_id)
    )
    languages = result.fetchall()

    if not languages:
        raise HTTPException(status_code=404, detail="No languages found for this user")

    language_list = []
    for lang in languages:
        lang_dict = {
            "id": lang[0],
            "lan_name": lang[1],
            "seller_id": lang[2]
        }
        language_list.append(Language(**lang_dict))

    return language_list


# GET Language by ID
# @seller_router.get("/languages/{lang_id}/", response_model=Language, summary="Get a language by ID")
# async def get_language(
#         lang_id: int,
#         token: dict = Depends(verify_token),
#         session: AsyncSession = Depends(get_async_session)
# ):
#     if token is None:
#         raise HTTPException(status_code=401, detail="Not registered")
#
#     user_id = token.get('user_id')
#
#     # Retrieve the language by ID and user ID
#     result = await session.execute(select(language).where(
#         (language.c.id == lang_id) & (language.c.seller_id == user_id)
#     ))
#     lang = result.scalar_one_or_none()
#
#     if not lang:
#         raise HTTPException(status_code=404, detail="Language not found")
#
#     return lang


@seller_router.post("/experiences/", response_model=Experience, summary="Add a new experience")
async def add_experience(
        exp: ExperienceCreate,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")

    user_id = token.get('user_id')

    new_exp = experience.insert().values(
        company_name=exp.company_name,
        start_date=exp.start_date,
        end_date=exp.end_date,
        seller_id=user_id,
        city=exp.city,
        country=exp.country,
        job_title=exp.job_title,
        description=exp.description
    )
    result = await session.execute(new_exp)
    await session.commit()

    return {**exp.dict(), "id": result.inserted_primary_key[0], "seller_id": user_id}


# GET all experiences
@seller_router.get("/experiences/", response_model=List[Experience], summary="Get all experiences by user")
async def get_experiences(
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")

    user_id = token.get('user_id')

    result = await session.execute(
        select(experience).where(experience.c.seller_id == user_id)
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


# DELETE Experience by ID
@seller_router.delete("/experiences/{exp_id}/", summary="Delete an experience by ID")
async def delete_experience(
        exp_id: int,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")

    user_id = token.get('user_id')

    # Check if the experience exists and belongs to the user
    result = await session.execute(select(experience).where(
        (experience.c.id == exp_id) & (experience.c.seller_id == user_id)
    ))
    exp = result.scalar_one_or_none()

    if not exp:
        raise HTTPException(status_code=404, detail="Experience not found")

    # Delete the experience
    await session.execute(experience.delete().where(experience.c.id == exp_id))
    await session.commit()

    return {"detail": "Experience deleted successfully"}


# GET Experience by ID
@seller_router.get("/experiences/{exp_id}/", response_model=Experience, summary="Get an experience by ID")
async def get_experience(
        exp_id: int,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")

    user_id = token.get('user_id')

    # Retrieve the experience by ID and user ID
    result = await session.execute(select(experience).where(
        (experience.c.id == exp_id) & (experience.c.seller_id == user_id)
    ))
    exp = result.scalar_one_or_none()

    if not exp:
        raise HTTPException(status_code=404, detail="Experience not found")

    return exp


@seller_router.post("/occupations/", response_model=Occupation, summary="Add a new occupation")
async def add_occupation(
        occ: OccupationCreate,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")

    user_id = token.get('user_id')

    new_occ = occupation.insert().values(
        occup_name=occ.occup_name,
        seller_id=user_id
    )
    result = await session.execute(new_occ)
    await session.commit()

    return {**occ.dict(), "id": result.inserted_primary_key[0], "seller_id": user_id}


# DELETE Occupation by ID
@seller_router.delete("/occupations/{occ_id}/", summary="Delete an occupation by ID")
async def delete_occupation(
        occ_id: int,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")

    user_id = token.get('user_id')

    # Check if the occupation exists and belongs to the user
    result = await session.execute(select(occupation).where(
        (occupation.c.id == occ_id) & (occupation.c.seller_id == user_id)
    ))
    occ = result.scalar_one_or_none()

    if not occ:
        raise HTTPException(status_code=404, detail="Occupation not found")

    # Delete the occupation
    await session.execute(occupation.delete().where(occupation.c.id == occ_id))
    await session.commit()

    return {"detail": "Occupation deleted successfully"}


# GET all occupations
@seller_router.get("/occupations/", response_model=List[Occupation], summary="Get all occupations by user")
async def get_occupations(
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")

    user_id = token.get('user_id')

    result = await session.execute(
        select(occupation).where(occupation.c.seller_id == user_id)
    )
    occupations = result.fetchall()

    if not occupations:
        raise HTTPException(status_code=404, detail="No occupations found for this user")

    occupation_list = []
    for occ in occupations:
        occ_dict = {
            "id": occ[0],
            "occup_name": occ[1],
            "seller_id": occ[2]
        }
        occupation_list.append(Occupation(**occ_dict))

    return occupation_list


# GET Occupation by ID
@seller_router.get("/occupations/{occ_id}/", response_model=Occupation, summary="Get an occupation by ID")
async def get_occupation(
        occ_id: int,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")

    user_id = token.get('user_id')

    # Retrieve the occupation by ID and user ID
    result = await session.execute(select(occupation).where(
        (occupation.c.id == occ_id) & (occupation.c.seller_id == user_id)
    ))
    occ = result.scalar_one_or_none()

    if not occ:
        raise HTTPException(status_code=404, detail="Occupation not found")

    return occ


@seller_router.post("/project-skills/", response_model=ProjectSkill, summary="Add a new project skill")
async def add_project_skills(
        proj_skill: ProjectSkillCreate,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")

    user_id = token.get('user_id')

    new_proj_skill = projects_skills.insert().values(
        skill_name=proj_skill.skill_name,
        seller_project_id=proj_skill.seller_project_id
    )
    result = await session.execute(new_proj_skill)
    await session.commit()

    return {**proj_skill.dict(), "id": result.inserted_primary_key[0]}


# DELETE Project Skill by ID
@seller_router.delete("/project-skills/{proj_skill_id}/", summary="Delete a project skill by ID")
async def delete_project_skill(
        proj_skill_id: int,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")

    user_id = token.get('user_id')

    # Check if the project skill exists and belongs to the user
    result = await session.execute(select(projects_skills).where(
        (projects_skills.c.id == proj_skill_id)
    ))
    proj_skill = result.scalar_one_or_none()

    if not proj_skill:
        raise HTTPException(status_code=404, detail="Project skill not found")

    # Delete the project skill
    await session.execute(projects_skills.delete().where(projects_skills.c.id == proj_skill_id))
    await session.commit()

    return {"detail": "Project skill deleted successfully"}


# GET Project Skill by ID
@seller_router.get("/project-skills/{proj_skill_id}/", response_model=ProjectSkill, summary="Get a project skill by ID")
async def get_project_skill(
        proj_skill_id: int,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")

    # Retrieve the project skill by ID
    result = await session.execute(select(projects_skills).where(
        (projects_skills.c.id == proj_skill_id)
    ))
    proj_skill = result.scalar_one_or_none()

    if not proj_skill:
        raise HTTPException(status_code=404, detail="Project skill not found")

    return proj_skill


@seller_router.post("/project-files/", response_model=ProjectFile, summary="Add a new project file")
async def add_project_files(
        proj_file: ProjectFileCreate,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")

    user_id = token.get('user_id')

    new_proj_file = project_files.insert().values(
        file_url=proj_file.file_url,
        seller_project_id=proj_file.seller_project_id
    )
    result = await session.execute(new_proj_file)
    await session.commit()

    return {**proj_file.dict(), "id": result.inserted_primary_key[0]}


# DELETE Project File by ID
@seller_router.delete("/project-files/{proj_file_id}/", summary="Delete a project file by ID")
async def delete_project_file(
        proj_file_id: int,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")

    user_id = token.get('user_id')

    # Check if the project file exists and belongs to the user
    result = await session.execute(select(project_files).where(
        (project_files.c.id == proj_file_id)
    ))
    proj_file = result.scalar_one_or_none()

    if not proj_file:
        raise HTTPException(status_code=404, detail="Project file not found")

    # Delete the project file
    await session.execute(project_files.delete().where(project_files.c.id == proj_file_id))
    await session.commit()

    return {"detail": "Project file deleted successfully"}


# GET Project File by ID
@seller_router.get("/project-files/{proj_file_id}/", response_model=ProjectFile, summary="Get a project file by ID")
async def get_project_file(
        proj_file_id: int,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")

    # Retrieve the project file by ID
    result = await session.execute(select(project_files).where(
        (project_files.c.id == proj_file_id)
    ))
    proj_file = result.scalar_one_or_none()

    if not proj_file:
        raise HTTPException(status_code=404, detail="Project file not found")

    return proj_file


@seller_router.post("/save_client/", summary="Save a client for the seller")
async def save_client(
        client_id: int,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")

    # Get current user_id from token
    current_user_id = token.get('user_id')

    # Look up the user with the given client_id
    result = await session.execute(
        select(user).where(user.c.id == client_id)
    )
    client_user = result.fetchone()

    if client_user is None:
        raise HTTPException(status_code=404, detail="Client not found")

    # Check if the client is the same as the current user
    if client_user[0] == current_user_id:
        raise HTTPException(status_code=400, detail="Cannot save yourself as a client")

    # Check if the client is already saved
    result = await session.execute(
        select(saved_client).where(
            (saved_client.c.seller_id == current_user_id) &
            (saved_client.c.user_id == client_id)
        )
    )
    existing_client = result.scalar_one_or_none()

    if existing_client:
        raise HTTPException(status_code=400, detail="Client already saved")

    # Save the client
    new_saved_client = saved_client.insert().values(
        seller_id=current_user_id,
        user_id=client_id
    )
    await session.execute(new_saved_client)
    await session.commit()

    return {"detail": "Client saved successfully"}


# DELETE Saved Client by ID
@seller_router.delete("/save_client/{client_id}/", summary="Delete a saved client by ID")
async def delete_saved_client(
        client_id: int,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")

    current_user_id = token.get('user_id')

    # Check if the saved client exists
    result = await session.execute(select(saved_client).where(
        (saved_client.c.seller_id == current_user_id) & (saved_client.c.user_id == client_id)
    ))
    saved_client_entry = result.scalar_one_or_none()

    if not saved_client_entry:
        raise HTTPException(status_code=404, detail="Saved client not found")

    # Delete the saved client
    await session.execute(saved_client.delete().where(
        (saved_client.c.seller_id == current_user_id) & (saved_client.c.user_id == client_id)
    ))
    await session.commit()

    return {"detail": "Saved client deleted successfully"}


@seller_router.get("/saved_clients/", summary="Get all saved clients by seller")
async def get_saved_clients(
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")

    # Get current user_id from token
    current_user_id = token.get('user_id')

    # Query to get all saved clients for the current seller
    result = await session.execute(
        select(saved_client).where(saved_client.c.seller_id == current_user_id)
    )
    saved_clients = result.fetchall()

    if not saved_clients:
        raise HTTPException(status_code=404, detail="No clients saved for this seller")

    client_list = []
    for client in saved_clients:
        client_dict = {
            "seller_id": client[0],
            "user_id": client[1]
        }
        client_list.append(client_dict)

    return client_list


# GET Saved Client by ID
@seller_router.get("/save_client/{client_id}/", summary="Get a saved client by ID")
async def get_saved_client(
        client_id: int,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")

    current_user_id = token.get('user_id')

    # Retrieve the saved client by ID and user ID
    result = await session.execute(select(saved_client).where(
        (saved_client.c.seller_id == current_user_id) & (saved_client.c.user_id == client_id)
    ))
    saved_client_entry = result.scalar_one_or_none()

    if not saved_client_entry:
        raise HTTPException(status_code=404, detail="Saved client not found")

    return saved_client_entry
