/**
 * ConversationSidebar Component
 * Display conversation history and manage sessions
 */

import React from "react";
import "./ConversationSidebar.css";

export default function ConversationSidebar({
  conversations,
  activeConversationId,
  onSelectConversation,
  onNewConversation,
  isLoading,
}) {
  return (
    <aside className="conversation-sidebar">
      <div className="sidebar-header">
        <h2>Hội Thoại</h2>
        <button
          className="new-conversation-btn"
          onClick={onNewConversation}
          disabled={isLoading}
          title="Bắt đầu hội thoại mới"
        >
          ➕ Mới
        </button>
      </div>

      <div className="conversations-list">
        {conversations.length === 0 ? (
          <div className="empty-state">
            <p>Chưa có hội thoại nào</p>
            <p className="hint">Nhấp "Mới" để bắt đầu</p>
          </div>
        ) : (
          conversations.map((conv) => (
            <button
              key={conv.id}
              className={`conversation-item ${
                activeConversationId === conv.id ? "active" : ""
              }`}
              onClick={() => onSelectConversation(conv.id)}
            >
              <div className="conversation-title">{conv.title}</div>
              <div className="conversation-meta">
                <span className="subject">{conv.subject.toUpperCase()}</span>
                <span className="message-count">{conv.message_count} tin</span>
              </div>
            </button>
          ))
        )}
      </div>
    </aside>
  );
}
