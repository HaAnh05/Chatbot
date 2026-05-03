/**
 * API Service Layer
 * Handles all communication with backend
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

/**
 * Send chat message to backend
 * @param {string} message - User message
 * @param {string} subject - Subject (cpp, python, etc.)
 * @param {number} conversationId - Conversation ID (optional)
 * @returns {Promise<{reply: string, conversation_id: number}>}
 */
export async function sendChatMessage(message, subject = "cpp", conversationId = null) {
  try {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message,
        subject,
        conversation_id: conversationId,
      }),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Chat error:", error);
    throw error;
  }
}

/**
 * Create new conversation
 * @param {string} subject - Subject (cpp, python, etc.)
 * @param {string} title - Conversation title (optional)
 * @returns {Promise<{id: number, subject: string, title: string, created_at: string}>}
 */
export async function createConversation(subject = "cpp", title = null) {
  try {
    const response = await fetch(`${API_BASE_URL}/conversations`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        subject,
        title,
      }),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Create conversation error:", error);
    throw error;
  }
}

/**
 * Get all conversations
 * @returns {Promise<{conversations: Array}>}
 */
export async function getConversations() {
  try {
    const response = await fetch(`${API_BASE_URL}/conversations`);

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Get conversations error:", error);
    throw error;
  }
}

/**
 * Get single conversation with all messages
 * @param {number} conversationId - Conversation ID
 * @returns {Promise<{id: number, subject: string, title: string, messages: Array}>}
 */
export async function getConversation(conversationId) {
  try {
    const response = await fetch(`${API_BASE_URL}/conversations/${conversationId}`);

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Get conversation error:", error);
    throw error;
  }
}
