import aiofiles
from fastapi import UploadFile
from client.schemes import GigCategoryfull,GigTagfull,GigFilefull,Gigfull


async def upload_file(file_upload: UploadFile):
    out_file = f'files/{file_upload.filename}'
    async with aiofiles.open(f'gig_file/{out_file}', 'wb') as f:
        content = await file_upload.read()
        await f.write(content)


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
        job_type=gig_data.job_type,
        work_mode=gig_data.work_mode,
        categories=categories_list,
        tags=tags_list,
        files=files_list
    )        