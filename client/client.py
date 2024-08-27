from fastapi import Depends, HTTPException, APIRouter, UploadFile
from auth.utils import verify_token
from typing import List
from database import get_async_session
from sqlalchemy import insert, update, delete
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from .schemes import Gig,GigPost
from client.schemes import GigStatus
import aiofiles
from client.schemes import GigFileResponse,GigTagResponse,GigCategoryResponse,GigResponsesearch
from .schemes import GigFile,Gigfull,GigCategoryResponse,GigResponse
from models.models import (gigs_category, gigs_tags, gigs_file, 
user,gig_tag_association,saved_client,seller,user,gigs)
from fastapi.responses import JSONResponse
from client.utils import convert_to_gig_model
from enum import Enum
from fastapi import HTTPException, Query



router_client = APIRouter(tags=["Client API"])
router_public=APIRouter(tags=["Public API"])






@router_client.post('/gig',summary="Create a Gig")
async def create_gig(new_gig: GigPost, token: dict = Depends(verify_token), session: AsyncSession = Depends(get_async_session)):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")
    user_id = token.get('user_id')


    result = await session.execute(select(user).where(user.c.id == user_id))
    user_data = result.fetchone()
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    if not user_data.is_client:
        raise HTTPException(status_code=403, detail="Only clients can post gigs")


    category_result = await session.execute(select(gigs_category).where(gigs_category.c.id == new_gig.category_id))
    category_data = category_result.fetchone()
    if not category_data:
        raise HTTPException(status_code=400, detail="Category not found")

   
    existing_gig_result = await session.execute(
        select(gigs).where(
            gigs.c.gigs_title == new_gig.gigs_title,
            gigs.c.duration == new_gig.duration,
            gigs.c.price == new_gig.price,
            gigs.c.description == new_gig.description,
            gigs.c.status==True,
            gigs.c.category_id == new_gig.category_id,
            gigs.c.user_id == user_id
        )
    )

    existing_gig = existing_gig_result.fetchone()
    
    if existing_gig:
        raise HTTPException(status_code=400, detail="You have already created a gig with identical details.")


    new_gig_data = new_gig.dict()
    new_gig_data['user_id'] = user_id
    new_gig_data['status'] = True


    query = insert(gigs).values(**new_gig_data).returning(gigs.c.id)
    result = await session.execute(query)
    created_gig_id = result.fetchone()[0]
    await session.commit()

    return JSONResponse(
        status_code=201,
        content={
            "message": "Gig successfully created",
            "gig_id": created_gig_id
        }
    )



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
    # return JSONResponse(content={"gigs": user_gigs}, status_code=200)



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
    if not gig_data:
        raise HTTPException(status_code=403, detail="Gig not found")

    if gig_data.user_id !=user_id:
         raise HTTPException(status_code=403, detail="You can only delete your own gigs")
    await session.execute(delete(gigs).where(gigs.c.id == gig_id))
    await session.commit()

    return JSONResponse(
        status_code=200,
        content={"message": "Gig deleted successfully"}
    )




@router_client.put('/gigs/{gig_id}/status', response_model=GigResponse, summary="Update a Gig")
async def update_gig(
    gig_id: int,
    updated_gig: GigStatus,
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
        raise HTTPException(status_code=403, detail="You can only update your own gigs")


    query = update(gigs).where(gigs.c.id == gig_id).values(
        status=updated_gig.status
    )
    await session.execute(query)
    await session.commit()

    result = await session.execute(select(gigs).where(gigs.c.id == gig_id))
    updated_gig_data = result.fetchone()

    
    return JSONResponse(
            status_code=201,
            content={
                "message": "Status successfully updated"
            }
        )




@router_client.post('/gigs/{gig_id}/tags', summary="Add tags to a Gig")
async def add_tags_to_gig(
    gig_id: int,
    tag_ids: List[int],  
    token: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")
    user_id = token.get('user_id')

    result = await session.execute(select(gigs).where(gigs.c.id == gig_id))
    gig_data = result.fetchone()
    if not gig_data:
        raise HTTPException(status_code=403, detail="Gig not found")

    if gig_data.user_id != user_id:
        raise HTTPException(status_code=403, detail="You can only add tags to your own gigs")

    for tag_id in tag_ids:
        tag_result = await session.execute(select(gigs_tags).where(gigs_tags.c.id == tag_id))
        tag_data = tag_result.fetchone()
        if not tag_data:
            raise HTTPException(status_code=404, detail=f"Tag with ID {tag_id} not found")

        association_result = await session.execute(
            select(gig_tag_association).where(
                gig_tag_association.c.gig_id == gig_id,
                gig_tag_association.c.tag_id == tag_id
            )
        )
        existing_association = association_result.fetchone()
        if existing_association:
            raise HTTPException(status_code=400, detail=f"This tag already use")

        insert_query = insert(gig_tag_association).values(gig_id=gig_id, tag_id=tag_id)
        await session.execute(insert_query)

    await session.commit()

    return JSONResponse(
        status_code=200,
        content={"message": "Tags successfully added to the gig"}
    )





@router_client.post('/gigs_file', summary="Create a Gig File")
async def create_gig_file(file: UploadFile, gig_id: int, token: dict = Depends(verify_token), session: AsyncSession = Depends(get_async_session)):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")
    user_id = token.get('user_id')

  
    result = await session.execute(select(user).where(user.c.id == user_id))
    user_data = result.fetchone()
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    
    if file is not None:
        out_file = f'/{file.filename}'
        async with aiofiles.open(f'gig_file/{out_file}', 'wb') as f:
            content = await file.read()
            await f.write(content)
        
   
    if not user_data.is_client:
        raise HTTPException(status_code=403, detail="Only clients can post files")


    result = await session.execute(select(gigs).where(gigs.c.id == gig_id))
    gig_data = result.fetchone()
    if not gig_data:
        raise HTTPException(status_code=403, detail="Gig not found")
    if gig_data.user_id != user_id:
        raise HTTPException(status_code=403, detail="You can only add files to your own gigs")
    
    
    query = insert(gigs_file).values(gigs_id=gig_id, file_url=out_file)
    result = await session.execute(query)
    
    await session.commit()
    return JSONResponse(
        status_code=201,
        content={"message": "File successfully created"}
    )




@router_client.get('/gigs/{gig_id}/files',response_model=List[GigFile], summary="Get files for a specific gig")
async def get_gig_files(gig_id: int, token: dict = Depends(verify_token), session: AsyncSession = Depends(get_async_session)):
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
        raise HTTPException(status_code=403, detail="Gig not found")
    
    if gig_data.user_id != user_id:
        raise HTTPException(status_code=403, detail="You can only view files for your own gigs")


    result = await session.execute(select(gigs_file).where(gigs_file.c.gigs_id == gig_id))
    files = result.fetchall()

    if not files:
        raise HTTPException(status_code=404, detail="No files found for this gig")

    return files



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
    if not gig_data:
        raise HTTPException(status_code=403, detail="Gig not found")
    if  gig_data.user_id != user_id:
        raise HTTPException(status_code=403, detail="You can only delete files from your own gigs")

 
    result = await session.execute(select(gigs_file).where(gigs_file.c.id == file_id, gigs_file.c.gigs_id == gig_id))
    file_data = result.fetchone()
    if not file_data:
        raise HTTPException(status_code=404, detail="File not found for this gig")


    await session.execute(delete(gigs_file).where(gigs_file.c.id == file_id))
    await session.commit()


    return JSONResponse(
        status_code=200,
        content={"message": "File deleted successfully"}
    )



@router_client.post('/saved_sellers', summary="Save a Seller")
async def save_seller(
    seller_id: int, 
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
        raise HTTPException(status_code=403, detail="Only clients can save sellers")

    result = await session.execute(select(seller).where(seller.c.id == seller_id))
    seller_data = result.fetchone()

    if not seller_data:
        raise HTTPException(status_code=404, detail="Seller not found")

    query = insert(saved_client).values(user_id=user_id, seller_id=seller_id)
    await session.execute(query)
    await session.commit()

    return JSONResponse(
        status_code=201,
        content={"message": "Seller saved successfully"}
    )




@router_client.get('/saved_sellers', summary="Get Saved Sellers")
async def get_saved_sellers(
    token: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")
    
    user_id = token.get('user_id')
    
    result = await session.execute(select(saved_client).where(saved_client.c.user_id == user_id))
    saved_sellers = result.fetchall()

    if not saved_sellers:
        raise HTTPException(status_code=404, detail="No saved sellers found")

    sellers = []
    for ss in saved_sellers:
        sellers.append({
            "id": ss.id,
            "client_id": ss.user_id,
            "save_seller_id": ss.seller_id,
            
        })

    return sellers




@router_client.delete('/saved_sellers/{saved_seller_id}', summary="Delete Saved Seller")
async def delete_saved_seller(
    saved_seller_id: int,
    token: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not registered")
    
    user_id = token.get('user_id')
    
    result = await session.execute(select(saved_client).where(saved_client.c.id == saved_seller_id, saved_client.c.user_id == user_id))
    saved_seller_data = result.fetchone()

    if not saved_seller_data:
        raise HTTPException(status_code=404, detail="Saved seller not found")

    await session.execute(delete(saved_client).where(saved_client.c.id == saved_seller_id))
    await session.commit()

  
    return JSONResponse(
        status_code=200,
        content={"message": "Saved seller deleted successfully"}
    )



@router_client.get('/{gig_id}/full', response_model=Gigfull, summary="Get Gig with all details")
async def get_gig_with_details(gig_id: int, session: AsyncSession = Depends(get_async_session)):

    result = await session.execute(select(gigs).where(gigs.c.id == gig_id))
    gig_data = result.fetchone()
    if not gig_data:
        raise HTTPException(status_code=404, detail="Gig not found")

    result = await session.execute(select(gigs_category).where(gigs_category.c.id == gig_data.category_id))
    categories = result.fetchall()

    result = await session.execute(select(gigs_tags).join(gig_tag_association).where(gig_tag_association.c.gig_id == gig_id))
    tags = result.fetchall()

    result = await session.execute(select(gigs_file).where(gigs_file.c.gigs_id == gig_id))
    files = result.fetchall()

    return convert_to_gig_model(gig_data, categories, tags, files)








@router_public.get('/gigs', response_model=List[Gig], summary="Get all Gigs aaa User")
async def get_public_gigs(session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(gigs))
    gigs_list = result.fetchall()

    if not gigs_list:
        raise HTTPException(status_code=404, detail="No gigs found")

    return gigs_list



@router_public.get('/search/{category_name}/gigs', response_model=List[GigResponse], summary="Get all Gigs for a specific Category by Name")
async def get_gigs_by_category_name(
    category_name: str,
    session: AsyncSession = Depends(get_async_session)
):

    result = await session.execute(
        select(gigs_category.c.id).where(gigs_category.c.category_name == category_name)
    )
    category_data = result.fetchone()

    if not category_data:
        raise HTTPException(status_code=404, detail="Category not found")

    category_id = category_data.id

    result = await session.execute(
        select(gigs).where(gigs.c.category_id == category_id)
    )
    gigs_data = result.fetchall()

    if not gigs_data:
        raise HTTPException(status_code=404, detail="No gigs found for this category")

   
    gigs_list = [
        GigResponse(
            id=gig.id,
            gigs_title=gig.gigs_title,
            duration=gig.duration,
            price=gig.price,
            description=gig.description,
            status=gig.status,
            category_id=gig.category_id,
            job_type=gig.job_type,
            work_mode=gig.work_mode,
            user_id=gig.user_id
        )
        for gig in gigs_data
    ]

    return gigs_list



@router_public.get('/search/{tag_name}', response_model=List[GigResponsesearch], summary="Get gigs by tag")
async def get_gigs_by_tag(tag_name: str, session: AsyncSession = Depends(get_async_session)):

    tag_query = select(gigs_tags.c.id).where(gigs_tags.c.tag_name == tag_name)
    tag_result = await session.execute(tag_query)
    tag_data = tag_result.fetchone()
    
    if not tag_data:
        raise HTTPException(status_code=404, detail="Tag not found")

    tag_id = tag_data[0]


    gig_query = (
        select(
            gigs.c.id, gigs.c.gigs_title, gigs.c.duration, gigs.c.price, 
            gigs.c.description, gigs.c.status,gigs.c.job_type,gigs.c.work_mode, gigs.c.user_id,
            gigs_category.c.id.label("category_id"),
            gigs_category.c.category_name,
            gigs_tags.c.id.label("tag_id"), 
            gigs_tags.c.tag_name, 
            gigs_file.c.id.label("file_id"), 
            gigs_file.c.file_url
        )
        .select_from(
            gigs
            .join(gig_tag_association, gigs.c.id == gig_tag_association.c.gig_id)
            .join(gigs_tags, gigs_tags.c.id == gig_tag_association.c.tag_id)
            .join(gigs_category, gigs.c.category_id == gigs_category.c.id)
            .outerjoin(gigs_file, gigs.c.id == gigs_file.c.gigs_id)
        )
        .where(gig_tag_association.c.tag_id == tag_id)
    )
    gig_result = await session.execute(gig_query)
    gigs_data = gig_result.fetchall()

    if not gigs_data:
        raise HTTPException(status_code=404, detail="No gigs found for this tag")


    gigs_dict = {}
    for row in gigs_data:
        gig_id = row.id

        if gig_id not in gigs_dict:
            gigs_dict[gig_id] = GigResponsesearch(
                id=row.id,
                gigs_title=row.gigs_title,
                duration=row.duration,
                price=row.price,
                description=row.description,
                status=row.status,
                job_type=row.job_type,
                work_mode=row.work_mode,
                user_id=row.user_id,
                category=GigCategoryResponse(id=row.category_id, category_name=row.category_name),
                tags=[],
                files=[]
            )
        
        gig_response = gigs_dict[gig_id]

     
        if row.tag_id and not any(tag.id == row.tag_id for tag in gig_response.tags):
            gig_response.tags.append(GigTagResponse(id=row.tag_id, tag_name=row.tag_name))

 
        if row.file_id and not any(file.id == row.file_id for file in gig_response.files):
            gig_response.files.append(GigFileResponse(id=row.file_id, file_url=row.file_url))

    return list(gigs_dict.values())







