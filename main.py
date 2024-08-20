from fastapi import APIRouter, FastAPI
from auth.auth import auth_router
from client.client import router_client,router_public
from admin.admin import router_superuser




app = FastAPI(title='CogniJobs FREENLANCER', version='1.0.0')

router = APIRouter()


@router.get('/')
async def hello():
    return {'message': 'Hello, FastAPI!'}

app.include_router(router, prefix='/main')
app.include_router(auth_router, prefix='/auth')
app.include_router(router_client)
app.include_router(router_public,prefix="/public")
app.include_router(router_superuser,prefix='/superuser')




