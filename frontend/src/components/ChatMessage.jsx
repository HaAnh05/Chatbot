/**
 * ChatMessage Component
 * Display individual chat messages with role styling
 */

import React from "react";
import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import rehypeHighlight from "rehype-highlight";
import "highlight.js/styles/github-dark.css";
import "katex/dist/katex.min.css";
import "./ChatMessage.css";

export default function ChatMessage({ role, content, timestamp, imageBase64 }) {
  const isUser = role === "user";

  return (
    <div className={`chat-message ${isUser ? "user" : "assistant"}`}>
      <div className="message-header">
        <span className="role">{isUser ? "Bạn" : "Trợ lý"}</span>
        {timestamp && (
          <span className="timestamp">{new Date(timestamp).toLocaleTimeString("vi-VN")}</span>
        )}
      </div>
      <div className="message-content">
        {imageBase64 && (
          <div className="message-image">
            <img src={`data:image/jpeg;base64,${imageBase64}`} alt="Ảnh đã gửi" />
          </div>
        )}
        <ReactMarkdown
          remarkPlugins={[remarkMath]}
          rehypePlugins={[rehypeHighlight, rehypeKatex]}
          components={{
            p: ({ children }) => <p className="message-paragraph">{children}</p>,
            li: ({ children }) => <li className="message-list-item">{children}</li>,
          }}
        >
          {content}
        </ReactMarkdown>
      </div>
    </div>
  );
}
