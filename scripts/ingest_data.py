import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# Danh sách các file tài liệu muốn nạp vào "bộ não" của AI
file_paths = ["data/C++ 2011 (V).pdf", "data/C++ 2017 (V).pdf"]

all_documents = []

for path in file_paths:
    if os.path.exists(path):
        print(f"--- Đang nạp file: {path} ---")
        loader = PyPDFLoader(path)
        all_documents.extend(loader.load())
    else:
        print(f"Cảnh báo: Không tìm thấy file tại {path}. Bỏ qua...")

# Tiếp tục các bước xử lý RAG như cũ
if all_documents:
    # 2. Chia nhỏ văn bản (Chunking)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = text_splitter.split_documents(all_documents)

    # 3. Tạo Vector DB
    print("Đang tạo Vector Database (có thể mất vài phút tùy vào độ dày của PDF)...")
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vector_db = Chroma.from_documents(
        documents=chunks, 
        embedding=embeddings, 
        persist_directory="./data/chroma_db"
    )
    print(f"Thành công! Đã nạp xong {len(all_documents)} trang tài liệu vào ChromaDB.")
else:
    print("Không có tài liệu nào được nạp. Hãy kiểm tra lại folder data/")
