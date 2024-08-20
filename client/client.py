from fastapi import FastAPI, Depends, HTTPException, APIRouter, UploadFile
from auth.utils import verify_token
from typing import List
from database import get_async_session
from sqlalchemy import insert, update, delete
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from .schemes import Gig,GigPost
from models.models import user,gigs
from datetime import datetime
from .schemes import   GigFilePost,GigFile,GigCategoryfull,GigFilefull,Gigfull,GigTag,GigTagfull,GigCategoryResponse
from .schemes import GigResponse
from .schemes import  GigCategory
from .schemes import GigCategoryBase
from models.models import gigs_category, gigs_tags, gigs_file, user,gig_tag_association
from fastapi.responses import JSONResponse


router_client = APIRouter(tags=["Client API"])
router_public=APIRouter(tags=["Public API"])








@router_client.post('/gigs', response_model=Gig, summary="Create a Gig")
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
    



    new_gig_data = new_gig.dict()
    new_gig_data['user_id'] = user_id
   

    query = insert(gigs).values(**new_gig_data).returning(gigs)
    result = await session.execute(query)
    created_gig = result.fetchone()
    await session.commit()
    
    return JSONResponse(
        status_code=201,
        content={
            "message": "Gig successfully created"
        })


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


from client.schemes import GigStatus

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



@router_client.get('/tag', response_model=List[GigTag], summary="Get all tags")
async def get_tags(session: AsyncSession = Depends(get_async_session)):
    query = select(gigs_tags)
    result = await session.execute(query)
    tags_data = result.fetchall()
    

    tags_list = [GigTag(id=row.id, tag_name=row.tag_name) for row in tags_data]

    if not tags_list:
        raise HTTPException(status_code=404, detail="No tags found")

    return tags_list



# @router_client.get('/gigs/tags', summary="Get all gigs with their tags")
# async def get_all_gigs(session: AsyncSession = Depends(get_async_session)):
 
#     gig_result = await session.execute(select(gigs))
#     gigs_data = gig_result.fetchall()

   
#     tag_result = await session.execute(
#         select(gigs.c.id, gigs_tags.c.id, gigs_tags.c.tag_name)
#         .select_from(gigs.join(gig_tag_association, gigs.c.id == gig_tag_association.c.gig_id)
#                       .join(gigs_tags, gig_tag_association.c.tag_id == gigs_tags.c.id))
#     )
#     tags_data = tag_result.fetchall()


#     gig_tags_dict = {}
#     for gig in gigs_data:
#         gig_id = gig.id
#         if gig_id not in gig_tags_dict:
#             gig_tags_dict[gig_id] = {
#                 "id": gig.id,
#                 "gigs_title": gig.gigs_title,
#                 "tags": []
#             }
#         for tag in tags_data:
#             if tag.id == gig_id:
#                 gig_tags_dict[gig_id]["tags"].append({
#                     "id": tag.id,
#                     "tag_name": tag.tag_name
#                 })

   
#     return {"gigs": list(gig_tags_dict.values())}



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
    if not gig_data or gig_data.user_id != user_id:
        raise HTTPException(status_code=403, detail="You can only add tags to your own gigs")

   
    for tag_id in tag_ids:
        tag_result = await session.execute(select(gigs_tags).where(gigs_tags.c.id == tag_id))
        tag_data = tag_result.fetchone()
        if not tag_data:
            raise HTTPException(status_code=404, detail=f"Tag with ID {tag_id} not found")

       
        insert_query = insert(gig_tag_association).values(gig_id=gig_id, tag_id=tag_id)
        await session.execute(insert_query)

    await session.commit()

    return JSONResponse(
        status_code=200,
        content={"message": "Tags successfully added to the gig"}
    )

@router_client.get('/search/{tag_name}', response_model=List[GigResponse], summary="Get gigs by tag")
async def get_gigs_by_tag(tag_name: str, session: AsyncSession = Depends(get_async_session)):
 
    tag_query = select(gigs_tags.c.id).where(gigs_tags.c.tag_name == tag_name)
    tag_result = await session.execute(tag_query)
    tag_data = tag_result.fetchone()
    
    if not tag_data:
        raise HTTPException(status_code=404, detail="Tag not found")

    tag_id = tag_data[0]

    
    gig_query = (
        select(gigs)
        .select_from(
            gigs.join(gig_tag_association, gigs.c.id == gig_tag_association.c.gig_id)
        )
        .where(gig_tag_association.c.tag_id == tag_id)
    )
    gig_result = await session.execute(gig_query)
    gigs_data = gig_result.fetchall()

    if not gigs_data:
        raise HTTPException(status_code=404, detail="No gigs found for this tag")

 
    gigs_list = [
        GigResponse(
            id=gig.id,
            gigs_title=gig.gigs_title,
            duration=gig.duration,
            price=gig.price,
            description=gig.description,
            status=gig.status,
            category_id=gig.category_id,
            user_id=gig.user_id
        ) for gig in gigs_data
    ]

    return gigs_list







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
    if not gig_data or gig_data.user_id != user_id:
        raise HTTPException(status_code=403, detail="You can only view files for your own gigs")


    result = await session.execute(select(gigs_file).where(gigs_file.c.gigs_id == gig_id))
    files = result.fetchall()

    if not files:
        raise HTTPException(status_code=404, detail="No files found for this gig")

    return files


import aiofiles
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
    if not gig_data or gig_data.user_id != user_id:
        raise HTTPException(status_code=403, detail="You can only add files to your own gigs")
    
    
    query = insert(gigs_file).values(gigs_id=gig_id, file_url=out_file)
    result = await session.execute(query)
    
    await session.commit()
    return {"success": True}







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


















@router_public.get('/gigs', response_model=List[Gig], summary="Get all Gigs aaa User")
async def get_public_gigs(session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(gigs))
    gigs_list = result.fetchall()

    if not gigs_list:
        raise HTTPException(status_code=404, detail="No gigs found")

    return gigs_list



def convert_to_gig_model(gig_data, categories, tags, files):
    categories_list = [GigCategoryfull(id=cat.id, category_name=cat.category_name) for cat in categories]
    tags_list = [GigTagfull(id=tag.id, tag_name=tag.tag_name) for tag in tags]
    files_list = [GigFilefull(id=file.id, file_url=file.file_url) for file in files]

    return Gigfull(
        id=gig_data.id,
        gigs_title=gig_data.gigs_title,
        duration=gig_data.duration,
        price=gig_data.price,
        description=gig_data.description,
        user_id=gig_data.user_id,
        categories=categories_list,
        tags=tags_list,
        files=files_list
    )


@router_public.get('/gigs/{gig_id}/full', response_model=Gigfull, summary="Get Gig with all details")
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



@router_public.get('/categories', response_model=List[GigCategoryResponse], summary="Get all Gig Categories")
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



from fastapi import HTTPException, Query
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
            user_id=gig.user_id
        )
        for gig in gigs_data
    ]

    return gigs_list




from models.models import saved_client,seller


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

    return {"detail": "Seller saved successfully"}

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
            "seller_id": ss.seller_id,
            "user_id": ss.user_id,
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

    return {"detail": "Saved seller deleted successfully"}





