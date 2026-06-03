# Trợ Lý Học Tập

Chatbot học tập tiếng Việt cho sinh viên học lập trình C++ và Python. Hệ thống được thiết kế theo tinh thần "người bạn đồng hành": không chỉ đưa đáp án, mà còn gợi ý từng bước, giải thích dễ hiểu, kiểm tra mức độ hiểu và giúp người học hình thành chiến lược giải bài.

## Tính Năng

- **Chat AI có RAG**: hỏi đáp lập trình C++/Python, truy xuất tài liệu học tập từ ChromaDB trước khi gọi LLM.
- **Đồng hành theo ngữ cảnh**: lưu lịch sử hội thoại trong SQLite và gửi các lượt gần nhất vào prompt.
- **Hỗ trợ ảnh**: gửi ảnh bằng nút upload hoặc paste trực tiếp vào ô chat, giới hạn 5MB.
- **Render nội dung học tập**: hiển thị Markdown, công thức toán bằng KaTeX và code có syntax highlighting.
- **Quản lý hội thoại**: tạo hội thoại mới, chọn lại hội thoại cũ, chọn nhiều hội thoại và xóa hàng loạt.
- **Quiz**: sinh câu hỏi trắc nghiệm theo môn học, chủ đề, độ khó; nộp bài và nhận điểm kèm giải thích.
- **Flashcard**: sinh bộ thẻ ghi nhớ theo chủ đề, lật thẻ, chuyển thẻ và trộn thẻ để ôn tập.
- **Thử thách code**: sinh bài lập trình, starter code, test case, gợi ý và đánh giá bài nộp bằng LLM.
- **Tiến trình học tập**: dashboard hiển thị mức độ tự tin, số hội thoại, số bài tập, chuỗi ngày học, chủ đề đã học và gợi ý học tiếp.
- **Logging chi tiết**: ghi log request/response LLM, reasoning nếu model trả về, sự kiện quiz/flashcard/minigame/progress vào thư mục `logs/`.

## Kiến Trúc

```text
Frontend (React + Vite)
        ↓
Backend (FastAPI)
        ├── SQLite: users, conversations, messages, exercises, progress
        ├── ChromaDB: vector database cho RAG
        └── LM Studio: local LLM qua API tương thích OpenAI
```

Luồng xử lý chính khi chat:

1. Frontend gửi câu hỏi, môn học, `conversation_id` và ảnh nếu có đến backend.
2. Backend lấy hoặc tạo hội thoại cho user `guest`.
3. Backend lấy lịch sử hội thoại gần nhất từ SQLite.
4. `EduAgent` truy vấn ChromaDB để lấy tài liệu liên quan.
5. Backend dựng prompt gồm system prompt, hướng dẫn sư phạm theo lượt hỏi, lịch sử và tài liệu RAG.
6. Backend gọi LM Studio qua `/v1/chat/completions`, có fallback sang `/api/v1/chat`.
7. Câu trả lời được lưu vào SQLite, cập nhật tiến trình và trả về frontend.

## Cấu Trúc Thư Mục

```text
.
├── backend/
│   ├── main.py              # FastAPI app và tất cả API routes
│   ├── llm.py               # EduAgent + RAG + gọi LM Studio, hỗ trợ ảnh
│   ├── grader.py            # Sinh/chấm quiz, flashcard, thử thách code
│   ├── analytics.py         # Theo dõi tiến trình và gợi ý học tập
│   ├── config.py            # Đọc biến môi trường
│   ├── database.py          # SQLAlchemy engine/session
│   ├── logger.py            # Ghi log console + file theo GMT+7
│   ├── models.py            # ORM models
│   └── session_manager.py   # Tạo/xóa hội thoại, lưu và lấy message
├── frontend/
│   ├── package.json
│   └── src/
│       ├── api.js           # Các hàm gọi API backend
│       ├── App.jsx          # Component chính + điều hướng tab
│       ├── main.jsx
│       └── components/
│           ├── ChatInput.jsx           # Nhập tin nhắn, upload/paste ảnh
│           ├── ChatMessage.jsx         # Render Markdown, toán, code, ảnh
│           ├── ConversationSidebar.jsx # Tạo/chọn/xóa nhiều hội thoại
│           ├── QuizPanel.jsx           # Giao diện quiz trắc nghiệm
│           ├── FlashcardPanel.jsx      # Giao diện flashcard lật thẻ
│           ├── MinigamePanel.jsx       # Giao diện thử thách lập trình
│           └── ProgressDashboard.jsx   # Dashboard tiến trình
├── data/
│   ├── chroma_db/           # Vector database cho RAG
│   ├── chatbot.db           # SQLite database
│   └── *.pdf                # Tài liệu học tập
├── logs/                    # Log backend/frontend và log chatbot theo ngày
├── prompts/
│   └── system_prompt.txt    # Prompt sư phạm cho vai trò đồng hành học tập
├── scripts/
│   ├── ingest_data.py       # Nạp PDF vào ChromaDB
│   └── test_bot.py          # Script test nhanh chatbot
├── requirements.txt         # Python dependencies
├── RUN.md                   # Hướng dẫn chạy nhanh
└── .env                     # Biến môi trường backend
```

## Yêu Cầu

- Python 3.10+.
- Node.js 18+ và npm.
- LM Studio hoặc local server tương thích OpenAI chat completions.
- Conda hoặc venv.

## Biến Môi Trường

File `.env` ở thư mục gốc hiện dùng:

```env
LLM_BASE_URL=http://localhost:1234
LLM_MODEL=llm
LLM_TIMEOUT=0
DATABASE_URL=sqlite:///./data/chatbot.db
```

| Biến | Mô tả |
| --- | --- |
| `LLM_BASE_URL` | Địa chỉ Local Server của LM Studio |
| `LLM_MODEL` | Model ID mà LM Studio expose, ví dụ `llm` hoặc tên model cụ thể |
| `LLM_TIMEOUT` | Timeout request đến LLM, đặt `0` để tắt timeout |
| `DATABASE_URL` | Đường dẫn SQLite lưu hội thoại, bài tập và tiến trình |

Frontend có thể dùng thêm file `frontend/.env` nếu muốn đổi API URL:

```env
VITE_API_URL=http://localhost:8000
```

Nếu không có file này, frontend mặc định gọi `http://localhost:8000`.

## Chạy Project

Lưu ý: backend nên được chạy từ thư mục gốc `D:\Chatbot` để import `backend.*` và đường dẫn `prompts/`, `data/`, `logs/` hoạt động đúng.

### 1. Cài dependencies Python

Dùng Conda:

```powershell
cd D:\Chatbot
conda create -n bot_env python=3.11 -y
conda activate bot_env
pip install -r requirements.txt
```

Hoặc dùng venv:

```powershell
cd D:\Chatbot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Khởi động LM Studio

Trong LM Studio:

1. Vào mục **Developer**.
2. Load model muốn dùng.
3. Start **Local Server**.
4. Kiểm tra model ID trong `.env` khớp với model server đang expose.

### 3. Chạy backend

```powershell
cd D:\Chatbot
conda activate bot_env
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Backend:

- API: `http://localhost:8000`
- Swagger docs: `http://localhost:8000/docs`
- Log: `logs/chatbot_YYYY-MM-DD.log`

### 4. Chạy frontend

```powershell
cd D:\Chatbot\frontend
npm install
npm run dev
```

Frontend mặc định chạy tại `http://localhost:5173`.

## Chạy Lại Hàng Ngày

Sau khi cài đặt xong, mỗi lần chỉ cần 3 cửa sổ:

1. **LM Studio**: Start Local Server.
2. **Backend**: `python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000`.
3. **Frontend**: `cd frontend` rồi `npm run dev`.

## Nạp Dữ Liệu RAG

Script `scripts/ingest_data.py` đọc các PDF được khai báo trong biến `file_paths`, chia nhỏ văn bản, tạo embedding và lưu vào `data/chroma_db`.

```powershell
cd D:\Chatbot
conda activate bot_env
python scripts/ingest_data.py
```

Mặc định script đang nạp:

```python
file_paths = ["data/C++ 2011 (V).pdf", "data/C++ 2017 (V).pdf"]
```

Khi muốn bổ sung tài liệu Python hoặc tài liệu môn học khác, thêm đường dẫn PDF vào `file_paths` rồi chạy lại script.

## Luồng Sử Dụng Trên Giao Diện

1. Chọn môn học `C++` hoặc `Python`.
2. Dùng tab **Chat** để hỏi bài, gửi ảnh hoặc xem lại câu trả lời cũ.
3. Dùng sidebar **Hội Thoại** để tạo cuộc trò chuyện mới, chọn hội thoại cũ hoặc xóa nhiều hội thoại.
4. Dùng tab **Quiz** để tạo bài trắc nghiệm theo chủ đề và độ khó.
5. Dùng tab **Flashcard** để tạo bộ thẻ ôn tập.
6. Dùng tab **Thử thách** để tạo bài lập trình, xem gợi ý và nộp code.
7. Dùng tab **Tiến trình** để xem thống kê học tập và gợi ý học tiếp.

## API

### Chat

**`POST /chat`**: gửi câu hỏi đến chatbot.

Request:

```json
{
  "message": "Hàm trong C++ là gì?",
  "subject": "cpp",
  "conversation_id": 1,
  "image_base64": null
}
```

Với ảnh, `image_base64` là chuỗi base64 không kèm prefix `data:image/...;base64,`.

Response:

```json
{
  "reply": "Hàm trong C++ là một khối code...",
  "conversation_id": 1
}
```

### Hội Thoại

| Method | Endpoint | Mô tả |
| --- | --- | --- |
| `POST` | `/conversations` | Tạo hội thoại mới |
| `GET` | `/conversations` | Lấy danh sách hội thoại |
| `GET` | `/conversations/{id}` | Lấy chi tiết hội thoại và toàn bộ tin nhắn |
| `DELETE` | `/conversations` | Xóa một hoặc nhiều hội thoại |

Payload xóa hội thoại:

```json
{
  "conversation_ids": [1, 2, 3]
}
```

### Quiz

| Method | Endpoint | Mô tả |
| --- | --- | --- |
| `POST` | `/quiz/generate` | Tạo câu hỏi trắc nghiệm |
| `POST` | `/quiz/submit` | Nộp bài và nhận điểm |

Ví dụ tạo quiz:

```json
{
  "subject": "cpp",
  "topic": "vòng lặp for",
  "difficulty": "beginner",
  "count": 5
}
```

### Flashcard

| Method | Endpoint | Mô tả |
| --- | --- | --- |
| `POST` | `/flashcard/generate` | Tạo bộ flashcard |

Ví dụ:

```json
{
  "subject": "python",
  "topic": "list",
  "count": 10
}
```

### Thử Thách Lập Trình

| Method | Endpoint | Mô tả |
| --- | --- | --- |
| `POST` | `/minigame/start` | Tạo bài tập lập trình |
| `POST` | `/minigame/submit` | Nộp code và nhận đánh giá |

Ví dụ bắt đầu thử thách:

```json
{
  "subject": "cpp",
  "topic": "mảng",
  "difficulty": "beginner"
}
```

### Tiến Trình

| Method | Endpoint | Mô tả |
| --- | --- | --- |
| `GET` | `/progress/{user_id}?subject=cpp` | Xem tiến trình học tập |
| `POST` | `/progress/update` | Cập nhật tiến trình thủ công |

Dashboard tiến trình gồm:

- `confidence_level`: mức độ tự tin ước lượng.
- `total_conversations`: số hội thoại.
- `total_exercises_completed`: số bài tập đã hoàn thành.
- `topics_covered`: chủ đề đã học.
- `recommendations`: gợi ý học tiếp.
- `learning_streak`: chuỗi ngày học.
- `weekly_progress`: hoạt động 7 ngày gần nhất.

## Lưu Trữ Dữ Liệu

| Nơi | Mô tả |
| --- | --- |
| SQLite `data/chatbot.db` | User, hội thoại, tin nhắn, bài tập, bài nộp, tiến trình |
| ChromaDB `data/chroma_db` | Vector embeddings cho RAG |
| `localStorage` frontend | Cache tạm danh sách hội thoại và tin nhắn |
| `logs/chatbot_YYYY-MM-DD.log` | Log backend, request/response LLM, quiz, flashcard, minigame, progress |

## Múi Giờ

Backend sử dụng múi giờ **GMT+7** cho timestamp và log.

## Sự Cố Thường Gặp

### Backend không kết nối được LM Studio

Kiểm tra:

- LM Studio Local Server đã start chưa.
- `LLM_BASE_URL` trong `.env` có đúng không.
- `LLM_MODEL` có trùng model đang được expose không.
- Endpoint `/v1/chat/completions` có hoạt động không.

### Backend báo `No module named uvicorn`

Bạn đang chạy nhầm Python environment. Hãy kích hoạt đúng môi trường đã cài dependencies:

```powershell
conda activate bot_env
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend không gửi được request

Kiểm tra:

- Backend đã chạy ở cổng `8000`.
- `VITE_API_URL` nếu có phải trùng backend.
- Browser console có lỗi CORS/network không.

### Chatbot trả lời yếu hoặc không có ngữ cảnh

Kiểm tra:

- Thư mục `data/chroma_db` có tồn tại.
- Đã chạy `python scripts/ingest_data.py` sau khi đổi PDF.
- File PDF đã được khai báo trong `scripts/ingest_data.py`.
- Câu hỏi có đủ rõ để retriever tìm tài liệu liên quan không.

### Quiz/Flashcard/Minigame bị timeout hoặc sai JSON

- Các chức năng này gọi trực tiếp đến LLM nên có thể mất 1-3 phút.
- Đảm bảo LM Studio đang chạy và model đã load.
- Nếu quá chậm, giảm `count`.
- Nếu model trả sai JSON, thử dùng model tuân thủ instruction tốt hơn hoặc chạy lại request.

### Ảnh không được xử lý

Kiểm tra:

- Ảnh nhỏ hơn 5MB.
- Model trong LM Studio có hỗ trợ multimodal hay không.
- Backend log có dòng `[IMAGE attached]` khi gửi request đến LLM không.
