import google.generativeai as genai
import os

# Cách 1: Tự điền key trực tiếp vào đây để test cho nhanh
my_key = "AIzaSyBeKvYKse1jEmFPvRV1o1jwz0A0nBWPsOU" # Dán key của bạn vào đây
genai.configure(api_key=my_key)

try:
    print("Danh sách model bạn có quyền dùng:")
    models = genai.list_models()
    for m in models:
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
except Exception as e:
    print(f"Vẫn lỗi rồi Hà Anh ơi: {e}")