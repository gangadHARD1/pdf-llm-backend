import pytest
from  main import app,database
from fastapi.testclient import TestClient
from unittest.mock import patch
import os



TEST_DATABASE_URL = "postgresql+asyncpg://USER:USER@localhost:5432/pdf_llm_test"

@pytest.fixture(autouse=True, scope="module")
async def override_db_url():
    # Override before test session begins
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    yield
    await database.execute("TRUNCATE documents RESTART IDENTITY CASCADE;")
    #await database.disconnect()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c



def test_read_root(client):
    response = client.get("/")
    assert response.status_code==200
    assert response.json()=={"message": "Hello, FastAPI!"}

def test_file_upload(client):
    with open("test.pdf","rb") as f:
        response = client.post("/upload", files={"file": ("test.pdf", f, "application/pdf")})
        assert response.status_code == 200
        assert response.json()["status"] == "file_upload successful"

def test_invalid_file_upload(client):
    with open("test.txt", "rb") as f:
        response = client.post("/upload", files={"file": ("test.txt", f, "text/plain")})
        assert response.status_code == 200
        assert response.json()["error"] == "Only PDF files are allowed."

def test_pagination(client):
    for i in range(15):
        with open("test.pdf","rb") as f:
            response=client.post("/upload",files={"file": (f"test_{i}.pdf", f, "application/pdf")})
            assert response.status_code == 200
    
    response=client.get("/documents?page=1&limit=10")
    assert response.status_code == 200
    assert len(response.json()["documents"]) == 10
    assert response.json()["page"]==1

    response=client.get("/documents/?page=2&limit=10")
    assert response.status_code == 200
    assert len(response.json()["documents"]) == 10
    assert response.json()["page"]==2


@patch("main.openai_call")
def test_summarise(mock_openai_call,client):
    mock_openai_call.return_value ="This is a mock summary."
    with open("test.pdf", "rb") as f:
        response = client.post("/upload", files={"file": ("test.pdf", f, "application/pdf")})
        assert response.status_code == 200
        doc_id = response.json()["doc_id"]

    response=client.get("/token")
    assert response.status_code == 200
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}


    response = client.post(f"/summarize/{doc_id}",headers=headers)

    assert response.status_code == 200
    assert "summary" in response.json()
    assert response.json()["summary"]== "This is a mock summary."

    

