from datetime import datetime, timedelta

import uuid as gen_uuid
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from starlette.status import HTTP_401_UNAUTHORIZED

from starlette.middleware.cors import CORSMiddleware

from motor import motor_asyncio

import bcrypt
import jwt
from jwt import PyJWTError

SECRET_KEY = "A RANDOM, LONG, SEQUENCE OF CHARACTERS THAT ONLY THE SERVER KNOWS"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440

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

import abc

class DBWrapper(abc.ABC):
    @abc.abstractmethod
    async def insert_one(self, table_name: str, item_dict: dict):
        pass

    @abc.abstractmethod
    async def find_one(self, table_name: str, search_params: dict):
        pass

    @abc.abstractmethod
    async def update_one(self, table_name: str, search_params: dict, data: dict):
        pass

    @abc.abstractmethod
    async def find(self, table_name: str, search_params: dict):
        pass

    @abc.abstractmethod
    async def delete_one(self, table_name: str, search_params: dict):
        pass

class MongoDBWrapper(DBWrapper):
    def __init__(self, connection_str: str, database: str):
        self.db = motor_asyncio.AsyncIOMotorClient(connection_str)[database]

    async def insert_one(self, table_name: str, item_dict: dict):
        collection = self.db.get_collection(table_name)
        await collection.insert_one(item_dict)

    async def find_one(self, table_name: str, search_params: dict):
        collection = self.db.get_collection(table_name)
        item = await collection.find_one(search_params)
        return item

    async def update_one(self, table_name: str, search_params: dict, data: dict):
        collection = self.db.get_collection(table_name)
        rt = await collection.update_one(search_params, {"$set": data})
        return rt

    async def delete_one(self, table_name: str, search_params: dict):
        collection = self.db.get_collection(table_name)
        return await collection.delete_one(search_params)

    async def find(self, table_name: str, search_params: dict):
        collection = self.db.get_collection(table_name)
        cursor = collection.find(search_params)
        rt = []
        for row in await cursor.to_list(length=100):
            rt.append(row)

        return rt

DB_ENGINE = MongoDBWrapper('mongodb://localhost', 'tinytodo')


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

class DummyUser(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    disabled: bool = False
    password: str


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

    user_dict = await DB_ENGINE.find_one('users', {'username': username})

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
    user_dict = await DB_ENGINE.find_one('users', {'username': form_data.username})

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
        item = await db.find_one('users', {'uuid': uuid})
        return item

    @staticmethod
    async def create(db, data):
        # this validates the data before we insert into the db
        uid = gen_uuid.uuid1()
        item = TodoInDB(**data)
        item.uuid = uid.hex
        await db.insert_one('todos', item.dict())
        return item

    @staticmethod
    async def update(db, data, uuid):
        return await db.update_one('todos', {'uuid': uuid}, data)

@app.post("/users")
async def create_user(dummy_user: DummyUser):
    """Create new user"""

    # FIXME: check email already exists
    item = await DB_ENGINE.find_one('users', {'username': dummy_user.username})
    if item is not None:
        raise HTTPException(status_code=409, detail="User allready exists")

    new_user = User(
        username = dummy_user.username,
        email = dummy_user.email,
        full_name = dummy_user.full_name,
    )

    hashed_password = bcrypt.hashpw(dummy_user.password.encode(), bcrypt.gensalt())

    new_user_in_db = UserInDB(
        **new_user.dict(),
        hashed_password = hashed_password
    )

    await DB_ENGINE.insert_one('users', new_user_in_db.dict())
    return new_user


@app.post("/todos")
async def create_todo(todo_item: Todo, current_user: User = Depends(get_current_active_user)):
    """Save todo item"""
    item = TodoInDB(
        title=todo_item.title,
        content=todo_item.content,
        due_date=todo_item.due_date,
        username=current_user.username
    )

    return await TodoInDB.create(DB_ENGINE, item.dict())

@app.get("/todos")
async def get_all_todos(current_user: User = Depends(get_current_active_user)):
    """Get all todo items"""

    cursor = await DB_ENGINE.find('todos', {'username': current_user.username})
    rt = []
    for row in cursor:
        rt.append(TodoInDB(**row))
    return rt

@app.get("/todos/{uuid}")
async def get_todo(uuid: str, current_user: User = Depends(get_current_active_user)):
    """Get todo item with uuid"""

    item = await DB_ENGINE.find_one('todos', {'username': current_user.username, 'uuid': uuid})
    if item is None:
        raise HTTPException(status_code=404, detail="Todo item is not found!")

    return TodoInDB(**item)

@app.delete("/todos/{uuid}")
async def get_delete(uuid: str, current_user: User = Depends(get_current_active_user)):
    """Delete todo item with uuid"""

    cursor = await DB_ENGINE.delete_one('todos', {'username': current_user.username, 'uuid': uuid})
    print({'username': current_user.username, 'uuid': uuid})
    return {'status': 'ok', 'count': cursor.deleted_count}

@app.patch("/todos/{uuid}")
async def patch_todo(uuid: str, todo_patch: TodoPatch, current_user: User = Depends(get_current_active_user)):
    """Patch todo item"""

    cursor = await DB_ENGINE.find_one('todos', {'username': current_user.username, 'uuid': uuid})

    todo_patch_dict = todo_patch.dict()
    update_query = {}
    for key in todo_patch_dict:
        if todo_patch_dict[key] is not None:
            update_query[key] = todo_patch_dict[key]

    # FIXME: Return proper result
    await TodoInDB.update(DB_ENGINE, update_query, uuid)
    cursor = await DB_ENGINE.find_one('todos', {'username': current_user.username, 'uuid': uuid})
    return TodoInDB(**cursor)
