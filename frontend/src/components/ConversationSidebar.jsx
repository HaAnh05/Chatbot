/**
 * ConversationSidebar Component
 * Display conversation history and manage sessions
 */

import React, { useEffect, useMemo, useState } from "react";
import "./ConversationSidebar.css";

export default function ConversationSidebar({
  conversations,
  activeConversationId,
  onSelectConversation,
  onNewConversation,
  onDeleteConversations,
  isLoading,
}) {
  const [isSelecting, setIsSelecting] = useState(false);
  const [selectedIds, setSelectedIds] = useState(new Set());

  const conversationIds = useMemo(
    () => conversations.map((conv) => conv.id),
    [conversations]
  );
  const selectedCount = selectedIds.size;
  const allSelected = conversations.length > 0 && selectedCount === conversations.length;

  useEffect(() => {
    setSelectedIds((previousIds) => {
      const availableIds = new Set(conversationIds);
      const nextIds = new Set(
        Array.from(previousIds).filter((id) => availableIds.has(id))
      );
      return nextIds.size === previousIds.size ? previousIds : nextIds;
    });

    if (conversations.length === 0) {
      setIsSelecting(false);
    }
  }, [conversationIds, conversations.length]);

  const handleToggleSelectionMode = () => {
    if (isSelecting) {
      setSelectedIds(new Set());
    }
    setIsSelecting(!isSelecting);
  };

  const handleToggleConversation = (conversationId) => {
    setSelectedIds((previousIds) => {
      const nextIds = new Set(previousIds);
      if (nextIds.has(conversationId)) {
        nextIds.delete(conversationId);
      } else {
        nextIds.add(conversationId);
      }
      return nextIds;
    });
  };

  const handleSelectAll = () => {
    setSelectedIds(allSelected ? new Set() : new Set(conversationIds));
  };

  const handleDeleteSelected = async () => {
    const ids = Array.from(selectedIds);
    if (ids.length === 0) {
      return;
    }

    const confirmed = window.confirm(`Xoa ${ids.length} hoi thoai da chon?`);
    if (!confirmed) {
      return;
    }

    await onDeleteConversations(ids);
    setSelectedIds(new Set());
    setIsSelecting(false);
  };

  const renderConversationContent = (conv) => (
    <>
      <div className="conversation-title">{conv.title}</div>
      <div className="conversation-meta">
        <span className="subject">{conv.subject.toUpperCase()}</span>
        <span className="message-count">{conv.message_count} tin</span>
      </div>
    </>
  );

  return (
    <aside className="conversation-sidebar">
      <div className="sidebar-header">
        <h2>Hoi Thoai</h2>
        <div className="sidebar-actions">
          <button
            type="button"
            className={`select-mode-btn ${isSelecting ? "active" : ""}`}
            onClick={handleToggleSelectionMode}
            disabled={isLoading || conversations.length === 0}
            title="Chon hoi thoai de xoa"
          >
            {isSelecting ? "Huy" : "Chon"}
          </button>
          <button
            type="button"
            className="new-conversation-btn"
            onClick={onNewConversation}
            disabled={isLoading || isSelecting}
            title="Bat dau hoi thoai moi"
          >
            + Moi
          </button>
        </div>
      </div>

      {isSelecting && (
        <div className="selection-toolbar">
          <span className="selection-count">{selectedCount} da chon</span>
          <button
            type="button"
            className="select-all-btn"
            onClick={handleSelectAll}
            disabled={isLoading || conversations.length === 0}
          >
            {allSelected ? "Bo chon" : "Chon tat ca"}
          </button>
          <button
            type="button"
            className="delete-selected-btn"
            onClick={handleDeleteSelected}
            disabled={isLoading || selectedCount === 0}
          >
            Xoa
          </button>
        </div>
      )}

      <div className="conversations-list">
        {conversations.length === 0 ? (
          <div className="empty-state">
            <p>Chua co hoi thoai nao</p>
            <p className="hint">Nhan "Moi" de bat dau</p>
          </div>
        ) : (
          conversations.map((conv) =>
            isSelecting ? (
              <label
                key={conv.id}
                className={`conversation-item selectable ${
                  activeConversationId === conv.id ? "active" : ""
                } ${selectedIds.has(conv.id) ? "selected" : ""}`}
              >
                <input
                  className="conversation-checkbox"
                  type="checkbox"
                  checked={selectedIds.has(conv.id)}
                  onChange={() => handleToggleConversation(conv.id)}
                  disabled={isLoading}
                />
                <span className="conversation-content">
                  {renderConversationContent(conv)}
                </span>
              </label>
            ) : (
              <button
                key={conv.id}
                type="button"
                className={`conversation-item ${
                  activeConversationId === conv.id ? "active" : ""
                }`}
                onClick={() => onSelectConversation(conv.id)}
              >
                {renderConversationContent(conv)}
              </button>
            )
          )
        )}
      </div>
    </aside>
  );
}
