/**
 * ChatInput Component
 * Input area for user messages with image upload support
 */

import React, { useState, useRef } from "react";
import "./ChatInput.css";

const MAX_IMAGE_SIZE = 5 * 1024 * 1024; // 5MB

export default function ChatInput({ onSendMessage, disabled, isLoading }) {
  const [message, setMessage] = useState("");
  const [imagePreview, setImagePreview] = useState(null);
  const [imageBase64, setImageBase64] = useState(null);
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);

  const processImageFile = (file) => {
    if (!file || !file.type.startsWith("image/")) return;
    if (file.size > MAX_IMAGE_SIZE) {
      alert("Kích thước ảnh tối đa là 5MB");
      return;
    }
    const reader = new FileReader();
    reader.onload = (e) => {
      const dataUrl = e.target.result;
      setImagePreview(dataUrl);
      // Strip data:image/...;base64, prefix to get raw base64
      const base64 = dataUrl.split(",")[1];
      setImageBase64(base64);
    };
    reader.readAsDataURL(file);
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) processImageFile(file);
    // Reset input so same file can be selected again
    e.target.value = "";
  };

  const handlePaste = (e) => {
    const items = e.clipboardData?.items;
    if (!items) return;
    for (const item of items) {
      if (item.type.startsWith("image/")) {
        e.preventDefault();
        const file = item.getAsFile();
        if (file) processImageFile(file);
        break;
      }
    }
  };

  const removeImage = () => {
    setImagePreview(null);
    setImageBase64(null);
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    if ((!message.trim() && !imageBase64) || isLoading) {
      return;
    }

    onSendMessage(message, imageBase64);
    setMessage("");
    setImagePreview(null);
    setImageBase64(null);

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
      {imagePreview && (
        <div className="image-preview-strip">
          <div className="image-preview-thumb">
            <img src={imagePreview} alt="Preview" />
            <button
              type="button"
              className="image-remove-btn"
              onClick={removeImage}
              title="Xóa ảnh"
            >
              ✕
            </button>
          </div>
        </div>
      )}
      <div className="input-container">
        <input
          type="file"
          ref={fileInputRef}
          accept="image/*"
          onChange={handleFileChange}
          style={{ display: "none" }}
        />
        <button
          type="button"
          className="image-upload-btn"
          onClick={() => fileInputRef.current?.click()}
          disabled={disabled || isLoading}
          title="Đính kèm ảnh"
        >
          📷
        </button>
        <textarea
          ref={textareaRef}
          className="input-textarea"
          placeholder="Nhập câu hỏi của bạn... (Shift+Enter để xuống dòng)"
          value={message}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          onPaste={handlePaste}
          disabled={disabled || isLoading}
          rows={1}
        />
        <button
          className="send-button"
          type="submit"
          disabled={disabled || isLoading || (!message.trim() && !imageBase64)}
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
