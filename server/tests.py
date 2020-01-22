from starlette.testclient import TestClient
from api import app, MongoDBWrapper
import api

from motor import motor_asyncio

from datetime import datetime

now = datetime.now()
formated_date = now.strftime("%Y%m%d_%H%M%S")

db_name = f"testtinytodo_{formated_date}".format()

client = TestClient(app)
api.DB_ENGINE = MongoDBWrapper('mongodb://localhost', db_name)

def test_get_items_without_token():
    response = client.get("/todos")
    assert response.status_code == 401

def test_get_items_with_wrong_token():
    response = client.get("/todos", headers={'Authorization': 'Bearer ' + 'WRONG_TOKEN'})
    assert response.status_code == 401

def test_login():

    response = client.post("/users",
                           json={
                               "username": "askinozgur",
                               "email": "user@example.com",
                               "full_name": "Aşkın Özgür",
                               "disabled": False,
                               "password": "secret pass"
                           })

    print(response.json())

    assert response.status_code == 200

    response = client.post("/token",
                           data={
                               'username': 'askinozgur',
                               'password': 'secret pass'
                           })

    assert response.status_code == 200


def test_get_items_with_token():

    response = client.post("/token",
                           data={
                               'username': 'askinozgur',
                               'password': 'secret pass'
                           })

    assert response.status_code == 200
    json_response = response.json()

    response = client.get("/todos", headers={'Authorization': 'Bearer ' + json_response["access_token"]})
    assert response.status_code == 200


def test_add_new_todo():

    # Authenticate
    response = client.post("/token",
                           data={
                               'username': 'askinozgur',
                               'password': 'secret pass'
                           })

    assert response.status_code == 200
    json_response = response.json()

    headers = {'Authorization': 'Bearer ' + json_response["access_token"]}

    item = {
        "title": "Test Item 1",
        "content": "Test Content 1",
        "due_date": "2020-01-18T15:54:33.016Z",
        "is_done": False
    }

    # Create New Todo
    response = client.post("/todos",
                           headers=headers,
                           json=item)

    assert response.status_code == 200
    uuid = response.json()['uuid']

    response = client.get("/todos", headers=headers)
    assert response.status_code == 200

    # Check item really created
    all_items = response.json()
    item_found = False
    for _item in all_items:
        if _item['uuid'] == uuid:
            item_found = True
            break

    assert item_found == True


    # Check get item
    response = client.get("/todos/{}".format(uuid),
                          headers=headers)

    assert response.json()['title'] == "Test Item 1"

    # Check patch item
    response = client.patch("/todos/{}".format(uuid),
                            headers=headers,
                            json={'title': 'Test Patch Item 1'})

    assert response.status_code == 200
    assert response.json()['title'] == 'Test Patch Item 1'

    response = client.get("/todos/{}".format(uuid),
                          headers=headers)

    assert response.status_code == 200
    assert response.json()['title'] == 'Test Patch Item 1'

    # Check delete item
    response = client.delete("/todos/{}".format(uuid),
                            headers=headers)

    assert response.status_code == 200

    response = client.get("/todos/{}".format(uuid),
                          headers=headers)

    assert response.status_code == 404
