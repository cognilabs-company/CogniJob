import secrets

import aiofiles
import jwt

from datetime import datetime, timedelta
from config import SECRET
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi import Depends, HTTPException, UploadFile


algorithm = 'HS256'
security = HTTPBearer()


def generate_token(user_id: int):
    jti_access = secrets.token_urlsafe(32)
    jti_refresh = secrets.token_urlsafe(32)

    payload_access = {
        'type': 'access',
        'exp': datetime.utcnow() + timedelta(minutes=30),
        'user_id': user_id,
        'jti': jti_access
    }
    payload_refresh = {
        'type': 'refresh',
        'exp': datetime.utcnow() + timedelta(days=1),
        'user_id': user_id,
        'jti': jti_refresh
    }
    access_token = jwt.encode(payload_access, SECRET, algorithm=algorithm)
    refresh_token = jwt.encode(payload_refresh, SECRET, algorithm=algorithm)
    return {
        'access': access_token,
        'refresh': refresh_token
    }


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET, algorithms=[algorithm])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail='Token is expired!')
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail='Token invalid!')


async def upload_photo(file_upload: UploadFile):
    out_photo = f'files/{file_upload.filename}'
    async with aiofiles.open(f'seller_photos/{out_photo}', 'wb') as f:
        content = await file_upload.read()
        await f.write(content)


async def upload_file(file_upload: UploadFile):
    out_file = f'files/{file_upload.filename}'
    async with aiofiles.open(f'seller_cv/{out_file}', 'wb') as f:
        content = await file_upload.read()
        await f.write(content)
