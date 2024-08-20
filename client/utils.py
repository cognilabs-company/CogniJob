import aiofiles
from fastapi import UploadFile


async def upload_file(file_upload: UploadFile):
    out_file = f'files/{file_upload.filename}'
    async with aiofiles.open(f'gig_file/{out_file}', 'wb') as f:
        content = await file_upload.read()
        await f.write(content)