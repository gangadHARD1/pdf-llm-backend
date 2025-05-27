# PDF-llm

A FastAPI application for uploading, storing, and querying PDF documents using PostgreSQL and OpenAI GPT for summarization and Q&A.

---

## Features

- **Upload PDF files** and store their metadata in PostgreSQL.
- **Summarize** PDF content using OpenAI GPT.
- **Ask questions** about PDF content using OpenAI GPT.
- **JWT authentication** for protected endpoints.
- **Pagination** for listing uploaded documents.

---

## Requirements

- Python 3.11+
- PostgreSQL
- [OpenAI API Key](https://platform.openai.com/)
- Docker (optional, for containerized setup)

---

## Setup

### 1. Clone the repository

```sh
git clone <your-repo-url>
cd PDF-llm/App
```

### 2. Install dependencies

```sh
python -m venv venv
venv\Scripts\activate  # On Windows
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file or use `env_file.env` as a template:

```env
DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/pdf_llm_db"
OPEN_API_KEY="sk-..."
```

Or set them in your shell before running the app.

### 4. Run PostgreSQL

You can use Docker Compose:

```sh
docker-compose up db
```

Or run your own PostgreSQL instance.

### 5. Run the FastAPI app

```sh
uvicorn main:app --reload
```

---

## API Endpoints

### Authentication

- `GET /token`  
  Get a JWT token for testing (no password required in demo).

### PDF Upload

- `POST /upload`  
  Upload a PDF file (requires JWT).

### Summarize PDF

- `POST /summarize/{doc_id}`  
  Summarize the PDF content (requires JWT).

### Query PDF

- `POST /Query/{doc_id}/{Question}`  
  Ask a question about the PDF content.

### List Documents

- `GET /documents?page=1&limit=10`  
  Paginated list of uploaded documents.

### Get Document

- `GET /documents/{doc_id}`  
  Retrieve PDF metadata and extracted text.

---

## Running Tests

```sh
pytest
```

---

## Docker

To run the app and database with Docker Compose:

```sh
docker-compose up --build
```

---

## Notes

- Place your OpenAI API key and database URL in your environment or `.env` file.
- Uploaded PDFs are stored in the `pdf_storage/` directory.
- For production, update `SECRET_KEY` and secure your endpoints.

---

## License

MIT License
