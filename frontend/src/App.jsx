/**
 * Main App Component
 * Root application with chat, conversation history, and state management
 */

import React, { useState, useEffect, useRef } from "react";
import ChatMessage from "./components/ChatMessage";
import ChatInput from "./components/ChatInput";
import ConversationSidebar from "./components/ConversationSidebar";
import * as api from "./api";
import "./App.css";

export default function App() {
  // State management
  const [conversations, setConversations] = useState([]);
  const [activeConversationId, setActiveConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [subject, setSubject] = useState("cpp");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const subjectLabel = subject === "cpp" ? "C++" : "Python";

  // Refs
  const messagesEndRef = useRef(null);
  const loadedConversationRef = useRef(null);

  // Auto-scroll to bottom when messages change
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load conversations from localStorage or API on mount
  useEffect(() => {
    loadConversations();
  }, []);

  // Save messages to localStorage whenever they change
  useEffect(() => {
    if (activeConversationId) {
      const key = `conv_${activeConversationId}`;
      localStorage.setItem(key, JSON.stringify(messages));
    }
  }, [messages, activeConversationId]);

  /**
   * Load all conversations
   */
  const loadConversations = async () => {
    try {
      const data = await api.getConversations();
      setConversations(data.conversations || []);

      // Select first conversation if available
      if (data.conversations && data.conversations.length > 0) {
        const firstConv = data.conversations[0];
        setActiveConversationId(firstConv.id);
        loadMessages(firstConv.id);
      } else {
        // If no existing conversation, create one automatically
        const newConv = await api.createConversation(subject);
        setConversations([newConv]);
        setActiveConversationId(newConv.id);
        setMessages([]);
      }
    } catch (err) {
      console.error("Failed to load conversations:", err);
      // Try loading from localStorage
      const saved = localStorage.getItem("conversations");
      if (saved) {
        const parsedConversations = JSON.parse(saved);
        setConversations(parsedConversations);
        if (parsedConversations.length > 0) {
          setActiveConversationId(parsedConversations[0].id);
          loadMessages(parsedConversations[0].id);
        }
      }
    }
  };

  /**
   * Load messages for specific conversation
   */
  const loadMessages = async (convId) => {
    try {
      // Try loading from localStorage first
      const localKey = `conv_${convId}`;
      const localData = localStorage.getItem(localKey);
      if (localData) {
        setMessages(JSON.parse(localData));
        return;
      }

      // Fall back to API
      const data = await api.getConversation(convId);
      if (data.messages) {
        const formattedMessages = data.messages.map((msg) => ({
          role: msg.role,
          content: msg.content,
          timestamp: msg.timestamp,
        }));
        setMessages(formattedMessages);
        localStorage.setItem(localKey, JSON.stringify(formattedMessages));
      }
    } catch (err) {
      console.error("Failed to load messages:", err);
      setMessages([]);
    }
  };

  /**
   * Create new conversation
   */
  const handleNewConversation = async () => {
    try {
      setIsLoading(true);
      const newConv = await api.createConversation(subject);
      
      // Update conversations list
      const updatedConversations = [newConv, ...conversations];
      setConversations(updatedConversations);
      localStorage.setItem("conversations", JSON.stringify(updatedConversations));
      
      // Switch to new conversation
      setActiveConversationId(newConv.id);
      setMessages([]);
      setError(null);
    } catch (err) {
      setError("Không thể tạo hội thoại mới");
      console.error("Failed to create conversation:", err);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Send message to chatbot
   */
  const handleSendMessage = async (messageText) => {
    if (!messageText.trim() || !activeConversationId) {
      return;
    }

    try {
      setIsLoading(true);
      setError(null);

      // Add user message to UI immediately
      const userMessage = {
        role: "user",
        content: messageText,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMessage]);

      // Send to backend
      const response = await api.sendChatMessage(
        messageText,
        subject,
        activeConversationId
      );

      // Add assistant response
      const assistantMessage = {
        role: "assistant",
        content: response.reply,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      setError("Không thể gửi tin nhắn. Vui lòng thử lại.");
      console.error("Failed to send message:", err);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Handle conversation selection
   */
  const handleSelectConversation = (convId) => {
    setActiveConversationId(convId);
    loadMessages(convId);
    
    // Update subject based on conversation
    const conv = conversations.find((c) => c.id === convId);
    if (conv) {
      setSubject(conv.subject);
    }
  };

  /**
   * Handle subject change
   */
  const handleSubjectChange = (newSubject) => {
    setSubject(newSubject);
  };

  return (
    <div className="app-container">
      {/* Sidebar */}
      <ConversationSidebar
        conversations={conversations}
        activeConversationId={activeConversationId}
        onSelectConversation={handleSelectConversation}
        onNewConversation={handleNewConversation}
        isLoading={isLoading}
      />

      {/* Main Chat Area */}
      <main className="chat-main">
        {/* Header */}
        <header className="chat-header">
          <div>
            <h1>Trợ Lý Học Tập</h1>
            <p>Giải thích rõ ràng, thân thiện và dễ hiểu.</p>
          </div>

          {/* Subject Selector */}
          <div className="subject-selector">
            <label htmlFor="subject-select">Môn học:</label>
            <select
              id="subject-select"
              value={subject}
              onChange={(e) => handleSubjectChange(e.target.value)}
              disabled={isLoading}
            >
              <option value="cpp">C++</option>
              <option value="python">Python</option>
            </select>
          </div>
        </header>

        {/* Messages Area */}
        <div className="chat-messages-container">
          {messages.length === 0 && !error && (
            <div className="welcome-message">
              <h2>Chào mừng! 👋</h2>
              <p>Hãy hỏi tôi bất kỳ câu hỏi gì về lập trình {subject.toUpperCase()}</p>
              <div className="example-questions">
                <p className="subtitle">Ví dụ:</p>
                {subject === "cpp" ? (
                  <ul>
                    <li>
                      <button
                        className="suggestion-btn"
                        onClick={() => handleSendMessage("Làm sao viết vòng lặp for?")}
                        disabled={isLoading}
                      >
                        Làm sao viết vòng lặp for?
                      </button>
                    </li>
                    <li>
                      <button
                        className="suggestion-btn"
                        onClick={() => handleSendMessage("Hàm trong C++ là gì?")}
                        disabled={isLoading}
                      >
                        Hàm trong C++ là gì?
                      </button>
                    </li>
                    <li>
                      <button
                        className="suggestion-btn"
                        onClick={() => handleSendMessage("Mảng (array) hoạt động như thế nào?")}
                        disabled={isLoading}
                      >
                        Mảng (array) hoạt động như thế nào?
                      </button>
                    </li>
                  </ul>
                ) : (
                  <ul>
                    <li>
                      <button
                        className="suggestion-btn"
                        onClick={() => handleSendMessage("Làm sao viết vòng lặp for trong Python?")}
                        disabled={isLoading}
                      >
                        Làm sao viết vòng lặp for trong Python?
                      </button>
                    </li>
                    <li>
                      <button
                        className="suggestion-btn"
                        onClick={() => handleSendMessage("List trong Python là gì?")}
                        disabled={isLoading}
                      >
                        List trong Python là gì?
                      </button>
                    </li>
                    <li>
                      <button
                        className="suggestion-btn"
                        onClick={() => handleSendMessage("Hàm lambda dùng để làm gì?")}
                        disabled={isLoading}
                      >
                        Hàm lambda dùng để làm gì?
                      </button>
                    </li>
                  </ul>
                )}
              </div>
            </div>
          )}

          {messages.map((msg, idx) => (
            <ChatMessage
              key={idx}
              role={msg.role}
              content={msg.content}
              timestamp={msg.timestamp}
            />
          ))}

          {error && <div className="error-message">{error}</div>}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <ChatInput
          onSendMessage={handleSendMessage}
          disabled={!activeConversationId}
          isLoading={isLoading}
        />
      </main>
    </div>
  );
}
