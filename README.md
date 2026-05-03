# Educational Chatbot

Chatbot hoc tap tieng Viet cho C++ va Python, gom:

- `backend/`: FastAPI API, luu lich su hoi thoai bang SQLite, truy van RAG bang Chroma.
- `frontend/`: giao dien React + Vite.
- `data/`: PDF tai lieu, vector store `chroma_db`, va file SQLite `chatbot.db`.

Project hien tai dung **LM Studio Local Server** de sinh cau tra loi.

## Kien truc nhanh

Luong xu ly chinh:

1. Frontend gui cau hoi den backend.
2. Backend lay lich su hoi thoai gan nhat.
3. `EduAgent` truy van Chroma de lay context lien quan.
4. Backend goi LM Studio qua HTTP API.
5. Cau tra loi duoc luu vao SQLite va tra ve frontend.

## Cau truc thu muc

```text
.
|-- backend/
|   |-- main.py              # FastAPI app va API routes
|   |-- llm.py               # EduAgent + RAG + goi LM Studio
|   |-- config.py            # Doc bien moi truong
|   |-- database.py          # SQLAlchemy engine/session
|   |-- models.py            # ORM models
|   `-- session_manager.py   # Tao hoi thoai, luu message
|-- frontend/
|   |-- src/
|   |-- package.json
|   `-- vite.config.js
|-- data/
|   |-- chroma_db/           # Vector database
|   `-- chatbot.db           # SQLite database
|-- prompts/
|   `-- system_prompt.txt
|-- scripts/
|   `-- ingest_data.py       # Nap PDF vao Chroma
|-- requirements.txt         # Python dependencies dung o root
`-- .env                     # Bien moi truong cho backend
```

## Yeu cau

- Python 3.10+
- Node.js 18+ va npm
- LM Studio

## Bien moi truong

File `.env` o thu muc goc:

```env
LLM_BASE_URL=http://localhost:1234
LLM_MODEL=llm
LLM_TIMEOUT=0
DATABASE_URL=sqlite:///./data/chatbot.db
```

Giai thich:

- `LLM_BASE_URL`: dia chi Local Server cua LM Studio.
- `LLM_MODEL`: ten model id ma LM Studio dang expose qua API.
- `LLM_TIMEOUT`: timeout cho request den LM Studio, tinh bang giay. Dat `0` de tat timeout.
- `DATABASE_URL`: duong dan SQLite luu hoi thoai.

Frontend co the dung them file `frontend/.env` neu ban muon doi API URL:

```env
VITE_API_URL=http://localhost:8000
```

Neu khong co file nay, frontend mac dinh van goi `http://localhost:8000`.

## Chay project

Luu y: backend nen duoc chay tu thu muc goc `d:\Chatbot` de import `backend.*` hoat dong dung.

### 1. Tao virtual environment va cai Python packages

```powershell
cd d:\Chatbot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Khoi dong LM Studio

Trong LM Studio:

1. Vao `Developer`
2. Load model ban muon dung
3. Start `Local Server`

Mac dinh backend se goi den `http://localhost:1234`.

### 3. Chay backend

Mo terminal moi, kich hoat lai virtual environment neu can, sau do chay:

```powershell
cd d:\Chatbot
.\.venv\Scripts\Activate.ps1
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Backend san sang tai:

- `http://localhost:8000`
- Swagger docs: `http://localhost:8000/docs`

Luu y debug:

- Route `/chat` hien dang `print` raw model output ra terminal backend.
- Neu model sinh ra thinking hay noi dung loi, ban se thay truc tiep o terminal.

### 4. Chay frontend

Mo terminal khac:

```powershell
cd d:\Chatbot\frontend
npm install
npm run dev
```

Frontend mac dinh chay tai `http://localhost:5173`.

## Chay lai hang ngay

Sau khi cai dat xong, moi lan chi can 3 cua so:

1. LM Studio Local Server
2. `python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000`
3. `cd frontend` va `npm run dev`

## Nap du lieu RAG

Script nap du lieu hien tai doc cac PDF duoc khai bao trong `scripts/ingest_data.py` va luu embedding vao `data/chroma_db`.

Chay lenh:

```powershell
cd d:\Chatbot
.\.venv\Scripts\Activate.ps1
python scripts/ingest_data.py
```

## API chinh

### `POST /chat`

Gui cau hoi den chatbot.

Request:

```json
{
  "message": "Lam sao viet vong lap for?",
  "subject": "cpp",
  "conversation_id": 1
}
```

Response:

```json
{
  "reply": "...",
  "conversation_id": 1
}
```

### `POST /conversations`

Tao hoi thoai moi.

### `GET /conversations`

Lay danh sach hoi thoai.

### `GET /conversations/{conversation_id}`

Lay chi tiet mot hoi thoai va toan bo message.

## Luu tru du lieu

- SQLite: `data/chatbot.db`
- Chroma vector store: `data/chroma_db`
- localStorage o frontend: cache tam lich su hoi thoai

## Cac van de thuong gap

### Backend bao khong ket noi duoc LM Studio

Kiem tra:

- LM Studio Local Server da start chua
- `LLM_BASE_URL` co dung khong
- model trong `.env` co trung voi model dang duoc expose khong

### Frontend khong gui duoc request

Kiem tra:

- backend da chay o cong `8000`
- `VITE_API_URL` neu co thi phai trung voi backend
- console browser co loi CORS/network khong

### Chatbot tra loi yeu hoac khong co context

Kiem tra:

- thu muc `data/chroma_db` co ton tai
- da chay `python scripts/ingest_data.py` sau khi doi PDF
- file PDF can dung da duoc khai bao trong `scripts/ingest_data.py`

## Ghi chu

- README nay phan anh code hien tai trong repo.
