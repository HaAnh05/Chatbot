import os
from typing import Dict, List, Optional

import requests
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from backend.config import LLM_BASE_URL, LLM_MODEL, LLM_TIMEOUT

SYSTEM_PROMPT_PATH = "prompts/system_prompt.txt"


class EduAgent:
    """
    Educational Agent su dung local LLM server.
    """

    SUBJECTS = {
        "cpp": {"collection_name": "cpp_docs"},
        "python": {"collection_name": "python_docs"},
    }

    def __init__(self, subject: str = "cpp"):
        self.subject = subject if subject in self.SUBJECTS else "cpp"
        self.config = self.SUBJECTS[self.subject]
        self.model = LLM_MODEL
        self.base_url = LLM_BASE_URL
        self.timeout = None if LLM_TIMEOUT <= 0 else LLM_TIMEOUT

        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self.db = Chroma(
            persist_directory="./data/chroma_db",
            embedding_function=embeddings,
        )

        if os.path.exists(SYSTEM_PROMPT_PATH):
            with open(SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
                self.system_instruction = f.read()
        else:
            self.system_instruction = (
                "Ban la tro ly hoc tap chuyen giai bai tap C++/Python tai UET."
            )

    def _build_messages(
        self,
        user_query: str,
        context_text: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        image_base64: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        guidance_text = self._build_turn_guidance(
            user_query=user_query,
            conversation_history=conversation_history,
        )
        messages = [
            {
                "role": "system",
                "content": (
                    f"{self.system_instruction}\n\n"
                    "Luu y quan trong: hay tra loi truc tiep cho cau hoi moi nhat cua hoc sinh. "
                    "Lich su hoi thoai chi la boi canh, khong phai mau de lap lai.\n\n"
                    "Tai lieu tham khao de giai bai:\n"
                    f"{context_text or 'Khong co tai lieu lien quan.'}"
                ),
            },
            {"role": "system", "content": guidance_text},
        ]

        if conversation_history:
            for msg in conversation_history[-5:]:
                role = "assistant" if msg.get("role") == "assistant" else "user"
                messages.append({"role": role, "content": msg.get("content", "")})

        if image_base64:
            user_content = [
                {"type": "text", "text": user_query},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
                },
            ]
            messages.append({"role": "user", "content": user_content})
        else:
            messages.append({"role": "user", "content": user_query})
        return messages

    def _build_turn_guidance(
        self,
        user_query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        query = user_query.strip().lower()

        if any(token in query for token in ["la gi", "là gì", "nghia la gi", "nghĩa là gì", "what is"]):
            mode = (
                "Day la cau hoi ve khai niem. "
                "Hay giai thich dung thuat ngu hoc sinh vua hoi, bang ngon ngu don gian, "
                "neu hop thi them mot vi du doi thuong ngan. "
                "Khong quay lai lap nguyen bai toan truoc do."
            )
        elif any(token in query for token in ["loi", "lỗi", "error", "bug", "sai o dau", "sai ở đâu"]):
            mode = (
                "Day la cau hoi giai quyet loi. "
                "Hay dong vai tro nguoi dong hanh go loi: chi ra dau hieu can kiem tra, "
                "gia thuyet co the sai, va mot buoc kiem chung tiep theo. "
                "Khong sua hoan chinh ca bai."
            )
        elif any(token in query for token in ["lam sao", "làm sao", "cach", "cách", "how do", "how to"]):
            mode = (
                "Day la cau hoi xin huong lam. "
                "Hay dua ra chien luoc giai quyet tung phan, nhan manh cach nghi truoc khi nghi den dap an."
            )
        else:
            mode = (
                "Hay uu tien lam ro muc tieu cua hoc sinh, giai thich ngan gon, va dua mot goi y vua du de hoc sinh tu di tiep."
            )

        prior_assistant = ""
        if conversation_history:
            assistant_messages = [
                msg.get("content", "").strip()
                for msg in conversation_history
                if msg.get("role") == "assistant" and msg.get("content")
            ]
            if assistant_messages:
                prior_assistant = (
                    "Cau tra loi truoc cua ban co the chua toi uu. "
                    "Neu hoc sinh dang hoi y moi, dung lap lai noi dung nay: "
                    f"{assistant_messages[-1][:240]}"
                )

        return (
            "Huong dan su pham cho luot nay:\n"
            f"- {mode}\n"
            "- Tra loi nhu mot nguoi ban dong hanh hoc tap: than thien, ro rang, khong len lop.\n"
            "- Neu dung vi du doi thuong, chi can 1 vi du ngan va sat y.\n"
            "- Ket thuc bang mot cau bat dau bang 'Do ban ...?' .\n"
            f"- {prior_assistant or 'Khong lap lai nguyen van cau tra loi truoc do.'}"
        )

    def _extract_text_content(self, payload: Dict) -> str:
        choices = payload.get("choices")
        if isinstance(choices, list) and choices:
            message = choices[0].get("message", {})
            content = message.get("content", "")
            if isinstance(content, str):
                return content.strip()
            if isinstance(content, list):
                parts = []
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        parts.append(str(item.get("text", "")))
                return "\n".join(part for part in parts if part).strip()

        message = payload.get("message", {})
        if isinstance(message, dict):
            content = message.get("content", "")
            if isinstance(content, str):
                return content.strip()

        for key in ("text", "output_text", "response", "content"):
            value = payload.get(key)
            if isinstance(value, str):
                return value.strip()

        raise ValueError(f"Khong doc duoc noi dung tra loi tu LM Studio: {payload}")

    def _call_lm_studio(self, messages: List[Dict[str, str]]) -> str:
        openai_payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.5,
            "stream": False,
        }
        direct_payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.5,
            "stream": False,
        }
        attempts = [
            (f"{self.base_url}/v1/chat/completions", openai_payload),
            (f"{self.base_url}/api/v1/chat", direct_payload),
        ]

        last_error = None
        saw_connection_error = False
        saw_timeout_error = False
        for url, payload in attempts:
            try:
                response = requests.post(url, json=payload, timeout=self.timeout)
                response.raise_for_status()
                return self._extract_text_content(response.json())
            except requests.exceptions.ConnectionError as exc:
                saw_connection_error = True
                last_error = exc
            except requests.exceptions.Timeout as exc:
                saw_timeout_error = True
                last_error = exc
            except (requests.exceptions.RequestException, ValueError) as exc:
                last_error = exc

        if saw_connection_error:
            raise requests.exceptions.ConnectionError(str(last_error))
        if saw_timeout_error:
            raise requests.exceptions.Timeout(str(last_error))
        raise RuntimeError(str(last_error))

    def ask(
        self,
        user_query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        image_base64: Optional[str] = None,
    ) -> str:
        try:
            retriever = self.db.as_retriever(search_kwargs={"k": 2})
            docs = retriever.invoke(user_query)
            context_text = "\n".join(doc.page_content for doc in docs)

            messages = self._build_messages(
                user_query=user_query,
                context_text=context_text,
                conversation_history=conversation_history,
                image_base64=image_base64,
            )
            return self._call_lm_studio(messages)
        except requests.exceptions.ConnectionError:
            return (
                "Khong ket noi duoc LM Studio tai "
                f"{self.base_url}. Hay mo Local Server va load model `{self.model}` truoc."
            )
        except requests.exceptions.Timeout:
            return (
                "Request den LM Studio bi timeout. Neu ban muon tat timeout, dat "
                "`LLM_TIMEOUT=0` trong `.env` roi khoi dong lai backend."
            )
        except Exception as e:
            return f"Da xay ra loi: {str(e)}"
