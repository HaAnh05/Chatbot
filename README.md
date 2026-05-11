# Trợ Lý Học Tập

Chatbot học tập tiếng Việt cho sinh viên C++ và Python tại UET. Hỗ trợ chat, tạo quiz, flashcard, thử thách lập trình và theo dõi tiến trình học tập.

## Tính năng

- **Chat AI** — Hỏi đáp về lập trình C++/Python, hỗ trợ gửi ảnh (multimodal)
- **Quiz** — Tạo câu hỏi trắc nghiệm theo chủ đề và mức độ
- **Flashcard** — Tạo thẻ ghi nhớ để ôn tập
- **Thử thách** — Bài tập lập trình với đánh giá tự động bằng AI
- **Tiến trình** — Dashboard theo dõi quá trình học tập
- **Lịch sử** — Quản lý nhiều hội thoại qua sidebar

## Kiến trúc

```
Frontend (React + Vite)  →  Backend (FastAPI)  →  LM Studio (Gemma 4 E2B)
                                ↓
                           SQLite + ChromaDB (RAG)
```

Luồng xử lý chính:

1. Frontend gửi câu hỏi (kèm ảnh nếu có) đến backend
2. Backend lấy lịch sử hội thoại gần nhất từ SQLite
3. `EduAgent` truy vấn ChromaDB để lấy ngữ cảnh liên quan
4. Backend gọi LM Studio qua API tương thích OpenAI
5. Câu trả lời được lưu vào SQLite và trả về frontend

## Cấu trúc thư mục

```text
.
├── backend/
│   ├── main.py              # FastAPI app và tất cả API routes
│   ├── llm.py               # EduAgent + RAG + gọi LM Studio (hỗ trợ ảnh)
│   ├── grader.py            # ExerciseManager: tạo/chấm quiz, flashcard, minigame
│   ├── analytics.py         # ProgressTracker: theo dõi tiến trình học tập
│   ├── config.py            # Đọc biến môi trường
│   ├── database.py          # SQLAlchemy engine/session
│   ├── models.py            # ORM models (User, Conversation, Message, Exercise, ...)
│   └── session_manager.py   # Tạo hội thoại, lưu message
├── frontend/
│   └── src/
│       ├── api.js           # Các hàm gọi API backend
│       ├── App.jsx          # Component chính + điều hướng tab
│       ├── App.css          # Style chính
│       └── components/
│           ├── ChatInput.jsx          # Ô nhập tin nhắn + upload ảnh
│           ├── ChatMessage.jsx        # Hiển thị tin nhắn (text + ảnh)
│           ├── ConversationSidebar.jsx # Sidebar quản lý hội thoại
│           ├── QuizPanel.jsx          # Giao diện quiz trắc nghiệm
│           ├── FlashcardPanel.jsx     # Giao diện flashcard lật thẻ
│           ├── MinigamePanel.jsx      # Giao diện thử thách lập trình
│           └── ProgressDashboard.jsx  # Dashboard tiến trình
├── data/
│   ├── chroma_db/           # Vector database cho RAG
│   └── chatbot.db           # SQLite database
├── scripts/
│   └── ingest_data.py       # Nạp PDF vào ChromaDB
├── requirements.txt         # Python dependencies
└── .env                     # Biến môi trường
```

## Yêu cầu

- Python 3.10+
- Node.js 18+ và npm
- LM Studio (đã tải model Gemma 4 E2B hoặc tương đương)
- Conda (khuyến nghị) hoặc venv

## Biến môi trường

File `.env` ở thư mục gốc:

```env
LLM_BASE_URL=http://localhost:1234
LLM_MODEL=google/gemma-4-e2b
LLM_TIMEOUT=0
DATABASE_URL=sqlite:///./data/chatbot.db
```

Giải thích:

| Biến | Mô tả |
|------|-------|
| `LLM_BASE_URL` | Địa chỉ Local Server của LM Studio |
| `LLM_MODEL` | Tên model ID mà LM Studio đang expose qua API |
| `LLM_TIMEOUT` | Timeout cho request đến LM Studio (giây). Đặt `0` để tắt timeout |
| `DATABASE_URL` | Đường dẫn SQLite lưu hội thoại |

Frontend có thể dùng thêm file `frontend/.env` nếu muốn đổi API URL:

```env
VITE_API_URL=http://localhost:8000
```

Nếu không có file này, frontend mặc định gọi `http://localhost:8000`.

## Chạy project

Lưu ý: backend phải được chạy từ thư mục gốc `D:\Chatbot` để import `backend.*` hoạt động đúng.

### 1. Tạo môi trường và cài đặt dependencies

**Dùng Conda (khuyến nghị):**

```powershell
cd D:\Chatbot
conda create -n bot_env python=3.11 -y
conda activate bot_env
pip install -r requirements.txt
```

**Hoặc dùng venv:**

```powershell
cd D:\Chatbot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Khởi động LM Studio

Trong LM Studio:

1. Vào mục **Developer**
2. Load model (ví dụ: `google/gemma-4-e2b`)
3. Bật **Local Server**

Mặc định backend sẽ gọi đến `http://localhost:1234`.

### 3. Chạy backend

Mở terminal mới, kích hoạt môi trường:

```powershell
cd D:\Chatbot

# Nếu dùng Conda:
conda activate bot_env

# Nếu dùng venv:
.\.venv\Scripts\Activate.ps1

python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Backend sẵn sàng tại:

- API: `http://localhost:8000`
- Swagger docs: `http://localhost:8000/docs`

### 4. Chạy frontend

Mở terminal khác:

```powershell
cd D:\Chatbot\frontend
npm install
npm run dev
```

Frontend mặc định chạy tại `http://localhost:5173`.

## Chạy lại hàng ngày

Sau khi cài đặt xong, mỗi lần chỉ cần 3 cửa sổ:

1. **LM Studio** — Start Local Server
2. **Backend** — `python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000`
3. **Frontend** — `cd frontend` rồi `npm run dev`

## Nạp dữ liệu RAG

Script nạp dữ liệu đọc các PDF được khai báo trong `scripts/ingest_data.py` và lưu embedding vào `data/chroma_db`.

```powershell
cd D:\Chatbot
conda activate bot_env   # hoặc .\.venv\Scripts\Activate.ps1
python scripts/ingest_data.py
```

## API

### Chat

**`POST /chat`** — Gửi câu hỏi đến chatbot

```json
{
  "message": "Làm sao viết vòng lặp for?",
  "subject": "cpp",
  "conversation_id": 1,
  "image_base64": null
}
```

Phản hồi:

```json
{
  "reply": "Để viết vòng lặp for trong C++...",
  "conversation_id": 1
}
```

### Hội thoại

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| `POST` | `/conversations` | Tạo hội thoại mới |
| `GET` | `/conversations` | Lấy danh sách hội thoại |
| `GET` | `/conversations/{id}` | Lấy chi tiết hội thoại và toàn bộ tin nhắn |

### Quiz

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| `POST` | `/quiz/generate` | Tạo câu hỏi trắc nghiệm |
| `POST` | `/quiz/submit` | Nộp bài và nhận điểm |

### Flashcard

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| `POST` | `/flashcard/generate` | Tạo bộ flashcard |

### Thử thách lập trình

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| `POST` | `/minigame/start` | Tạo bài tập lập trình |
| `POST` | `/minigame/submit` | Nộp code và nhận đánh giá |

### Tiến trình

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| `GET` | `/progress/{user_id}` | Xem tiến trình học tập |
| `POST` | `/progress/update` | Cập nhật tiến trình |

## Lưu trữ dữ liệu

| Nơi | Mô tả |
|-----|-------|
| SQLite `data/chatbot.db` | Hội thoại, tin nhắn, bài tập, tiến trình |
| ChromaDB `data/chroma_db` | Vector embeddings cho RAG |
| localStorage (frontend) | Cache tạm lịch sử hội thoại |

## Múi giờ

Backend sử dụng múi giờ **GMT+7** (Asia/Ho_Chi_Minh) cho tất cả timestamp.

## Sự cố thường gặp

### Backend không kết nối được LM Studio

Kiểm tra:

- LM Studio Local Server đã start chưa
- `LLM_BASE_URL` trong `.env` có đúng không
- Model trong `.env` có trùng với model đang được load trong LM Studio không

### Frontend không gửi được request

Kiểm tra:

- Backend đã chạy ở cổng `8000`
- `VITE_API_URL` (nếu có) phải trùng với backend
- Console trình duyệt có lỗi CORS/network không

### Chatbot trả lời yếu hoặc không có ngữ cảnh

Kiểm tra:

- Thư mục `data/chroma_db` có tồn tại
- Đã chạy `python scripts/ingest_data.py` sau khi đổi PDF
- File PDF đã được khai báo trong `scripts/ingest_data.py`

### Quiz/Flashcard/Minigame bị timeout

- Tạo quiz, flashcard, minigame đều gọi trực tiếp đến LLM nên có thể mất 1-3 phút
- Đảm bảo LM Studio đang chạy và model đã được load
- Nếu quá chậm, thử giảm số lượng câu hỏi (`count` parameter)
