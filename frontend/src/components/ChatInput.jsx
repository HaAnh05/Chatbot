/**
 * ChatInput Component
 * Input area for user messages
 */

import React, { useState, useRef } from "react";
import "./ChatInput.css";

export default function ChatInput({ onSendMessage, disabled, isLoading }) {
  const [message, setMessage] = useState("");
  const textareaRef = useRef(null);

  const handleSubmit = (e) => {
    e.preventDefault();

    if (!message.trim() || isLoading) {
      return;
    }

    onSendMessage(message);
    setMessage("");

    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e) => {
    // Send on Enter, but allow Shift+Enter for newlines
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleInput = (e) => {
    setMessage(e.target.value);

    // Auto-expand textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 120) + "px";
    }
  };

  return (
    <form className="chat-input-form" onSubmit={handleSubmit}>
      <div className="input-container">
        <textarea
          ref={textareaRef}
          className="input-textarea"
          placeholder="Nhập câu hỏi của bạn... (Shift+Enter để xuống dòng)"
          value={message}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          disabled={disabled || isLoading}
          rows={1}
        />
        <button
          className="send-button"
          type="submit"
          disabled={disabled || isLoading || !message.trim()}
        >
          {isLoading ? (
            <>
              <span className="loading-spinner"></span>
              Đang xử lý...
            </>
          ) : (
            <>
              <span className="send-icon">✉️</span>
              Gửi
            </>
          )}
        </button>
      </div>
    </form>
  );
}
