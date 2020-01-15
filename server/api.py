from datetime import datetime, timedelta

import uuid as gen_uuid
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from starlette.status import HTTP_401_UNAUTHORIZED

from starlette.middleware.cors import CORSMiddleware

from motor import motor_asyncio

import bcrypt
import jwt
from jwt import PyJWTError

SECRET_KEY = "A RANDOM, LONG, SEQUENCE OF CHARACTERS THAT ONLY THE SERVER KNOWS"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440

# There are better ways, get it and implement it
db = motor_asyncio.AsyncIOMotorClient('mongodb://localhost')['tinytodo']

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")


class User(BaseModel):
    username: str
    email: str = None
    full_name: str = None
    disabled: bool = None


class UserInDB(User):
    hashed_password: str


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception

    except PyJWTError:
        raise credentials_exception

    user_dict = await db.users.find_one({'username': username})

    if not user_dict:
        raise credentials_exception

    print(user_dict)

    user = UserInDB(**user_dict)

    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user_dict = await db.users.find_one({'username': form_data.username})

    if not user_dict:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    print(user_dict)

    user = UserInDB(**user_dict)

    if not bcrypt.checkpw(form_data.password.encode(), user.hashed_password.encode()):
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


class Todo(BaseModel):
    """Basic todo item"""
    title: str
    content: str
    due_date: datetime = None
    is_done: bool = False

class TodoPatch(BaseModel):
    """Basic todo item"""
    title: str = None
    content: str = None
    due_date: datetime = None
    is_done: bool = None


class TodoInDB(Todo):
    """Todo item in* db"""
    username: str
    uuid: str = None

    @staticmethod
    async def get_by_uuid(db, uuid):
        item = await db.todos.find_one({'uuid': uuid})
        return item

    @staticmethod
    async def create(db, data):
        # this validates the data before we insert into the db
        uid = gen_uuid.uuid1()
        item = TodoInDB(**data)
        item.uuid = uid.hex
        db.todos.insert_one(item.dict())
        return item

    @staticmethod
    async def update(db, data, uuid):
        return await db.todos.update_one({'uuid': uuid}, {"$set": data})

@app.post("/todos")
async def create_todo(todo_item: Todo, current_user: User = Depends(get_current_active_user)):
    """Save todo item"""
    item = TodoInDB(
        title=todo_item.title,
        content=todo_item.content,
        due_date=todo_item.due_date,
        username=current_user.username
    )

    return await TodoInDB.create(db, item.dict())

@app.get("/todos")
async def get_all_todos(current_user: User = Depends(get_current_active_user)):
    """Get all todo items"""

    cursor = db.todos.find({'username': current_user.username})
    rt = []
    for row in await cursor.to_list(length=100):
        rt.append(TodoInDB(**row))
    return rt

@app.get("/todos/{uuid}")
async def get_todo(uuid: str, current_user: User = Depends(get_current_active_user)):
    """Get todo item with uuid"""

    cursor = await db.todos.find_one({'username': current_user.username, 'uuid': uuid})
    return TodoInDB(**cursor)

@app.delete("/todos/{uuid}")
async def get_delete(uuid: str, current_user: User = Depends(get_current_active_user)):
    """Delete todo item with uuid"""

    cursor = await db.todos.delete_one({'username': current_user.username, 'uuid': uuid})
    print({'username': current_user.username, 'uuid': uuid})
    return {'status': 'ok', 'count': cursor.deleted_count}

@app.patch("/todos/{uuid}")
async def patch_todo(uuid: str, todo_patch: TodoPatch, current_user: User = Depends(get_current_active_user)):
    """Patch todo item"""

    cursor = await db.todos.find_one({'username': current_user.username, 'uuid': uuid})

    todo_patch_dict = todo_patch.dict()
    update_query = {}
    for key in todo_patch_dict:
        if todo_patch_dict[key] is not None:
            update_query[key] = todo_patch_dict[key]

    # FIXME: Return proper result
    await TodoInDB.update(db, update_query, uuid)
    cursor = await db.todos.find_one({'username': current_user.username, 'uuid': uuid})
    return TodoInDB(**cursor)

