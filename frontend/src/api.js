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
export async function sendChatMessage(message, subject = "cpp", conversationId = null, imageBase64 = null) {
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
        image_base64: imageBase64,
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

// ============ Quiz / Flashcard / Minigame / Progress API ============

export async function generateQuiz(subject, topic, difficulty = "beginner", count = 5) {
  const response = await fetch(`${API_BASE_URL}/quiz/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ subject, topic, difficulty, count }),
  });
  if (!response.ok) throw new Error(`API error: ${response.status}`);
  return await response.json();
}

export async function submitQuiz(exerciseId, answers, userId = 1) {
  const response = await fetch(`${API_BASE_URL}/quiz/submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ exercise_id: exerciseId, answers, user_id: userId }),
  });
  if (!response.ok) throw new Error(`API error: ${response.status}`);
  return await response.json();
}

export async function generateFlashcards(subject, topic, count = 10) {
  const response = await fetch(`${API_BASE_URL}/flashcard/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ subject, topic, count }),
  });
  if (!response.ok) throw new Error(`API error: ${response.status}`);
  return await response.json();
}

export async function startMinigame(subject, topic, difficulty = "beginner") {
  const response = await fetch(`${API_BASE_URL}/minigame/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ subject, topic, difficulty }),
  });
  if (!response.ok) throw new Error(`API error: ${response.status}`);
  return await response.json();
}

export async function submitMinigame(exerciseId, submittedCode, userId = 1) {
  const response = await fetch(`${API_BASE_URL}/minigame/submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ exercise_id: exerciseId, submitted_code: submittedCode, user_id: userId }),
  });
  if (!response.ok) throw new Error(`API error: ${response.status}`);
  return await response.json();
}

export async function getProgress(userId = 1, subject = "cpp") {
  const response = await fetch(`${API_BASE_URL}/progress/${userId}?subject=${subject}`);
  if (!response.ok) throw new Error(`API error: ${response.status}`);
  return await response.json();
}
