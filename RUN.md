# RUN Guide

File nay dung de chay nhanh project `d:\Chatbot` ma khong can doc toan bo `README.md`.

## Chay nhanh moi ngay

Can 3 cua so.

### Cua so 1: LM Studio

Trong LM Studio:

1. Vao `Developer`
2. Load model
3. Start `Local Server`

### Cua so 2: Backend

```powershell
cd d:\Chatbot
.\.venv\Scripts\Activate.ps1
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Backend:

- API: `http://localhost:8000`
- Docs: `http://localhost:8000/docs`

### Cua so 3: Frontend

```powershell
cd d:\Chatbot\frontend
npm run dev
```

Frontend:

- UI: `http://localhost:5173`

## Chay lan dau

### 1. Tao virtual environment va cai Python packages

```powershell
cd d:\Chatbot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Cai packages cho frontend

```powershell
cd d:\Chatbot\frontend
npm install
```

### 3. Cau hinh backend

File `.env` dang dung:

```env
LLM_BASE_URL=http://localhost:1234
LLM_MODEL=llm
LLM_TIMEOUT=0
DATABASE_URL=sqlite:///./data/chatbot.db
```

`LLM_TIMEOUT=0` nghia la khong timeout request den LM Studio.

### 4. Neu can, nap lai du lieu RAG

Chi can khi ban thay doi PDF hoac muon tao lai vector DB.

```powershell
cd d:\Chatbot
.\.venv\Scripts\Activate.ps1
python scripts/ingest_data.py
```

## Thu tu khoi dong dung

1. Start LM Studio Local Server
2. Chay backend FastAPI
3. Chay frontend Vite
4. Mo `http://localhost:5173`

## Kiem tra nhanh

Neu muon kiem tra backend co song khong:

```powershell
Invoke-WebRequest http://localhost:8000/conversations
```

Neu muon kiem tra LM Studio co song khong:

```powershell
Invoke-WebRequest http://localhost:1234/api/v1/models
```

## Loi thuong gap

### 1. `Khong ket noi duoc LM Studio`

Nguyen nhan thuong gap:

- chua start `Local Server`
- `LLM_BASE_URL` sai
- `LLM_MODEL` khong trung model dang duoc expose

### 2. Frontend khong load duoc chat

Kiem tra:

- backend da chay cong `8000`
- frontend dang goi dung `VITE_API_URL`
- browser console co loi network hay khong

### 3. Backend chay nhung chat khong co ngu canh RAG

Kiem tra:

- thu muc `data/chroma_db` con ton tai
- da chay lai `python scripts/ingest_data.py` sau khi doi PDF

### 4. PowerShell chan kich hoat venv

Neu gap loi execution policy:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## Debug raw output

Route `/chat` dang `print` toan bo raw output cua model ra terminal backend:

- Neu model lo thinking
- Neu model lap lai cau tra loi
- Neu model tra ve sai format

ban se thay truc tiep o cua so chay `uvicorn`.

## Lenh tom tat

```powershell
# Backend
cd d:\Chatbot
.\.venv\Scripts\Activate.ps1
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd d:\Chatbot\frontend
npm run dev
```
