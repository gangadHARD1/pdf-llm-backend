# main.py

from fastapi import FastAPI,UploadFile,File
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String,TIMESTAMP,insert
from databases import Database
from contextlib import asynccontextmanager
from PyPDF2 import PdfReader
from datetime import datetime
import openai 
import os
from jose import JWTError, jwt
from datetime import timedelta
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, HTTPException, status
from mangum import Mangum

openai.api_key =os.getenv("OPEN_API_KEY")
database_url = os.getenv("DATABASE_URL")





database=Database(database_url)
metadata=MetaData()
documents=Table(
    "documents",
    metadata,
    Column("id",Integer,primary_key=True),
    Column("filename",String(255),nullable=False),
    Column("timestamp",TIMESTAMP,nullable=False),
)

engine = create_engine(str(database_url).replace("+asyncpg", ""), future=True)
metadata.create_all(engine)  



@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()  
    yield
    await database.disconnect()  

app = FastAPI(lifespan=lifespan)

#for 
handler = Mangum(app)

SECRET_KEY = "secret-key"  
ALGORITHM = "HS256"

security = HTTPBearer()

def create_access_token(data: dict, expires_delta: timedelta = timedelta(hours=1)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_jwt(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    return verify_jwt(credentials.credentials)

@app.get("/token")
def generate_token():
    access_token = create_access_token(data={"sub": "testuser"})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/")
def read_root():
    return {"message": "Hello, Welcome to my pdf paresr!"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if file.content_type!= "application/pdf":
        return {"error": "Only PDF files are allowed."}
    
    ts=datetime.now()
    #ts = ts.strftime("%Y-%m-%d %H:%M:%S")
    query=insert(documents).values(
        filename=file.filename,
        timestamp=ts
    )
    await database.execute(query)
    query = documents.select().with_only_columns(documents.c.id).where(documents.c.filename == file.filename, documents.c.timestamp == ts)
    result = await database.fetch_one(query)
    id = result['id'] if result else None

    if not id:
        return {"error": "Failed to save document metadata."}
    
    file_location=f"pdf_storage/{id}.pdf"
    with open(file_location, "wb") as f:
        content=await file.read()
        f.write(content)
    
   
    return {"status": "file_upload successful", "filename": file.filename,"doc_id":id}

            
@app.get("/documents/{doc_id}")
async def get_document(doc_id: int):
    read_file=PdfReader(f"pdf_storage/{doc_id}.pdf")
    if not read_file:
        return {"error": "Document not found."}
    text_content = ""
    for page in read_file.pages:
        text_content += page.extract_text() or ""
    
    query=documents.select().with_only_columns(documents.c.timestamp,documents.c.filename).where(
        documents.c.id == doc_id
    )
    result=await database.fetch_one(query)
    if not result:
        return {"error": "Document metadata not found."}
    ts = result['timestamp']
    filename = result['filename']
    
    return {"message": "Document retrieved successfully.","text_content": text_content, "timestamp": ts, "filename": filename}



#api_call
def openai_call(text_content: str,prompt=None):
    try:
        if prompt is None:
            prompt = f"Summarize the following in 2 sentences:\n{text_content}"

        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message["content"]
    except openai.NotFoundError:
        return "this is mock summary as i dont have the paid version of openai api, please use your own key to get the real summary"

@app.post("/summarize/{doc_id}")
async def summarize_document(doc_id: int,user:dict = Depends(get_current_user)):
    read_file=PdfReader(f"pdf_storage/{doc_id}.pdf")
    if not read_file:
        return {"error": "Document not found."}
    text_content = ""
    for page in read_file.pages:
        text_content += page.extract_text() or ""
    summary=openai_call(text_content)
    return {
        "message": "Document summarized successfully.","summary": summary}


@app.post("/Query/{doc_id}/{Question}")
async def query_document(doc_id: int,Question: str):
    read_file=PdfReader(f"pdf_storage/{doc_id}.pdf")
    if not read_file:
        return {"error": "Document not found."}
    text_content = ""
    for page in read_file.pages:
        text_content += page.extract_text() or ""
    prompt = f"Answer the following question based on the document content:\n{text_content}\nQuestion: {Question}"
    answer=openai_call(text_content,prompt)
    
    return {"message": "Document queried successfully.", "answer": answer}

@app.get("/documents")
async def get_page(page:int=1,limit:int=10):

    query=documents.select().with_only_columns(documents.c.id,documents.c.filename,documents.c.timestamp).offset((page-1)*limit).limit(limit)
    results=await database.fetch_all(query)
    if not results:
        return {"error": "No documents found."}
    documents_list = []
    for result in results:
        documents_list.append({
            "id": result['id'],
            "filename": result['filename'],
            "timestamp": result['timestamp']
        })
    return {"documents": documents_list, "page": page}



