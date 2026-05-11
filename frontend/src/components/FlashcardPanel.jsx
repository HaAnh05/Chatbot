/**
 * FlashcardPanel Component
 * Study with flip-card flashcards
 */

import React, { useState } from "react";
import * as api from "../api";
import "./FlashcardPanel.css";

export default function FlashcardPanel({ subject, onClose }) {
  const [phase, setPhase] = useState("setup"); // setup | studying
  const [topic, setTopic] = useState("");
  const [cards, setCards] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleGenerate = async () => {
    if (!topic.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await api.generateFlashcards(subject, topic);
      if (data.error) throw new Error(data.error);
      setCards(data.cards);
      setCurrentIndex(0);
      setIsFlipped(false);
      setPhase("studying");
    } catch (err) {
      setError("Không thể tạo flashcard. Vui lòng thử lại.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleFlip = () => setIsFlipped((f) => !f);

  const handlePrev = () => {
    setCurrentIndex((i) => Math.max(0, i - 1));
    setIsFlipped(false);
  };

  const handleNext = () => {
    setCurrentIndex((i) => Math.min(cards.length - 1, i + 1));
    setIsFlipped(false);
  };

  const handleShuffle = () => {
    const shuffled = [...cards].sort(() => Math.random() - 0.5);
    setCards(shuffled);
    setCurrentIndex(0);
    setIsFlipped(false);
  };

  const handleReset = () => {
    setPhase("setup");
    setCards([]);
    setCurrentIndex(0);
    setIsFlipped(false);
  };

  const currentCard = cards[currentIndex];

  return (
    <div className="flashcard-panel">
      <div className="panel-header">
        <h2>Flashcard</h2>
        <button className="close-btn" onClick={onClose}>✕</button>
      </div>

      {error && <div className="panel-error">{error}</div>}

      {phase === "setup" && (
        <div className="flashcard-setup">
          <div className="form-group">
            <label>Chủ đề:</label>
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="VD: biến, hàm, mảng..."
              onKeyDown={(e) => e.key === "Enter" && handleGenerate()}
            />
          </div>
          <button
            className="primary-btn"
            onClick={handleGenerate}
            disabled={loading || !topic.trim()}
          >
            {loading ? "Đang tạo..." : "Tạo flashcard"}
          </button>
        </div>
      )}

      {phase === "studying" && currentCard && (
        <div className="flashcard-studying">
          <div className="flashcard-progress">
            {currentIndex + 1} / {cards.length}
          </div>

          <div className={`flashcard ${isFlipped ? "flipped" : ""}`} onClick={handleFlip}>
            <div className="flashcard-inner">
              <div className="flashcard-front">
                <div className="card-label">Câu hỏi</div>
                <div className="card-content">{currentCard.front}</div>
                <div className="card-hint">Nhấn để lật</div>
              </div>
              <div className="flashcard-back">
                <div className="card-label">Đáp án</div>
                <div className="card-content">{currentCard.back}</div>
                <div className="card-hint">Nhấn để lật lại</div>
              </div>
            </div>
          </div>

          <div className="flashcard-nav">
            <button
              className="nav-btn"
              onClick={handlePrev}
              disabled={currentIndex === 0}
            >
              ← Trước
            </button>
            <button className="nav-btn shuffle-btn" onClick={handleShuffle}>
              Trộn
            </button>
            <button
              className="nav-btn"
              onClick={handleNext}
              disabled={currentIndex === cards.length - 1}
            >
              Tiếp →
            </button>
          </div>

          <div className="flashcard-actions">
            <button className="secondary-btn" onClick={handleReset}>Tạo bộ mới</button>
            <button className="secondary-btn" onClick={onClose}>Quay lại</button>
          </div>
        </div>
      )}
    </div>
  );
}
