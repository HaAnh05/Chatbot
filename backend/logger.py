"""
Logging module - Ghi log toàn bộ quá trình xử lý
Ghi ra cả console và file log
"""

import logging
import os
import sys
from datetime import datetime, timezone, timedelta

GMT7 = timezone(timedelta(hours=7))

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)-12s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class GMT7Formatter(logging.Formatter):
    """Formatter dùng múi giờ GMT+7"""

    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, tz=GMT7)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.strftime(DATE_FORMAT)


def get_logger(name: str) -> logging.Logger:
    """Tạo logger với tên module, ghi ra console + file"""
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # Console handler - INFO trở lên
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(GMT7Formatter(LOG_FORMAT, DATE_FORMAT))
    logger.addHandler(console)

    # File handler - DEBUG trở lên, ghi tất cả
    today = datetime.now(GMT7).strftime("%Y-%m-%d")
    log_file = os.path.join(LOG_DIR, f"chatbot_{today}.log")
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(GMT7Formatter(LOG_FORMAT, DATE_FORMAT))
    logger.addHandler(file_handler)

    return logger


def log_llm_request(logger, model, messages, payload=None):
    """Log request gửi đến LLM"""
    logger.info("=" * 60)
    logger.info("LLM REQUEST")
    logger.info(f"  Model: {model}")
    logger.info(f"  Messages count: {len(messages)}")

    for i, msg in enumerate(messages):
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        if isinstance(content, list):
            # Multimodal message
            text_parts = [p.get("text", "") for p in content if isinstance(p, dict) and p.get("type") == "text"]
            has_image = any(isinstance(p, dict) and p.get("type") == "image_url" for p in content)
            content_preview = " ".join(text_parts)[:200]
            logger.info(f"  [{i}] {role}: {content_preview}")
            if has_image:
                logger.info(f"       + [IMAGE attached]")
        else:
            content_str = str(content)
            if len(content_str) > 300:
                logger.debug(f"  [{i}] {role} (full): {content_str}")
                logger.info(f"  [{i}] {role}: {content_str[:300]}...")
            else:
                logger.info(f"  [{i}] {role}: {content_str}")

    if payload:
        logger.debug(f"  Payload keys: {list(payload.keys())}")
        logger.debug(f"  Temperature: {payload.get('temperature')}")


def log_llm_response(logger, response_data, elapsed_sec=None):
    """Log response từ LLM, bao gồm thinking/reasoning"""
    logger.info("-" * 60)
    logger.info("LLM RESPONSE")
    if elapsed_sec is not None:
        logger.info(f"  Time: {elapsed_sec:.1f}s")

    choices = response_data.get("choices", [])
    if not choices:
        logger.warning("  No choices in response!")
        return

    message = choices[0].get("message", {})

    # Log thinking/reasoning content
    reasoning = message.get("reasoning_content", "")
    if reasoning:
        logger.info("  THINKING:")
        for line in reasoning.split("\n"):
            if line.strip():
                logger.info(f"    {line.strip()}")
    else:
        logger.info("  THINKING: (none)")

    # Log content
    content = message.get("content", "")
    if isinstance(content, str):
        if len(content) > 500:
            logger.debug(f"  CONTENT (full): {content}")
            logger.info(f"  CONTENT: {content[:500]}...")
        else:
            logger.info(f"  CONTENT: {content}")
    elif isinstance(content, list):
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                text = part.get("text", "")
                logger.info(f"  CONTENT: {text[:500]}")

    # Log usage
    usage = response_data.get("usage", {})
    if usage:
        logger.info(f"  Tokens: prompt={usage.get('prompt_tokens', '?')}, "
                     f"completion={usage.get('completion_tokens', '?')}, "
                     f"total={usage.get('total_tokens', '?')}")

    finish_reason = choices[0].get("finish_reason", "")
    if finish_reason:
        logger.info(f"  Finish reason: {finish_reason}")

    logger.info("=" * 60)


def log_quiz_event(logger, event, details=None):
    """Log sự kiện quiz"""
    logger.info(f"[QUIZ] {event}")
    if details:
        for k, v in details.items():
            logger.info(f"  {k}: {v}")


def log_flashcard_event(logger, event, details=None):
    """Log sự kiện flashcard"""
    logger.info(f"[FLASHCARD] {event}")
    if details:
        for k, v in details.items():
            logger.info(f"  {k}: {v}")


def log_minigame_event(logger, event, details=None):
    """Log sự kiện minigame"""
    logger.info(f"[MINIGAME] {event}")
    if details:
        for k, v in details.items():
            logger.info(f"  {k}: {v}")


def log_progress_event(logger, event, details=None):
    """Log sự kiện progress"""
    logger.info(f"[PROGRESS] {event}")
    if details:
        for k, v in details.items():
            logger.info(f"  {k}: {v}")
