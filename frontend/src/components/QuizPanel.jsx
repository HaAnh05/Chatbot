/**
 * QuizPanel Component
 * Generate and take multiple-choice quizzes
 */

import React, { useState } from "react";
import * as api from "../api";
import "./QuizPanel.css";

export default function QuizPanel({ subject, onClose }) {
  const [phase, setPhase] = useState("setup"); // setup | taking | results
  const [topic, setTopic] = useState("");
  const [difficulty, setDifficulty] = useState("beginner");
  const [questions, setQuestions] = useState([]);
  const [exerciseId, setExerciseId] = useState(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedAnswers, setSelectedAnswers] = useState({});
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleGenerate = async () => {
    if (!topic.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await api.generateQuiz(subject, topic, difficulty);
      if (data.error) throw new Error(data.error);
      setQuestions(data.questions);
      setExerciseId(data.exercise_id);
      setSelectedAnswers({});
      setCurrentIndex(0);
      setPhase("taking");
    } catch (err) {
      setError("Không thể tạo bài quiz. Vui lòng thử lại.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectAnswer = (questionIndex, optionIndex) => {
    setSelectedAnswers((prev) => ({ ...prev, [questionIndex]: optionIndex }));
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError(null);
    try {
      const answers = Object.entries(selectedAnswers).map(([qIdx, sIdx]) => ({
        question_index: parseInt(qIdx),
        selected_index: sIdx,
      }));
      const data = await api.submitQuiz(exerciseId, answers);
      if (data.error) throw new Error(data.error);
      setResults(data);
      setPhase("results");
    } catch (err) {
      setError("Không thể nộp bài. Vui lòng thử lại.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleRetry = () => {
    setPhase("setup");
    setQuestions([]);
    setSelectedAnswers({});
    setResults(null);
    setExerciseId(null);
  };

  const currentQ = questions[currentIndex];
  const answeredCount = Object.keys(selectedAnswers).length;

  return (
    <div className="quiz-panel">
      <div className="panel-header">
        <h2>Bài Kiểm Tra</h2>
        <button className="close-btn" onClick={onClose}>✕</button>
      </div>

      {error && <div className="panel-error">{error}</div>}

      {phase === "setup" && (
        <div className="quiz-setup">
          <div className="form-group">
            <label>Chủ đề:</label>
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="VD: vòng lặp for, hàm, con trỏ..."
              onKeyDown={(e) => e.key === "Enter" && handleGenerate()}
            />
          </div>
          <div className="form-group">
            <label>Độ khó:</label>
            <select value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>
              <option value="beginner">Cơ bản</option>
              <option value="intermediate">Trung bình</option>
              <option value="advanced">Nâng cao</option>
            </select>
          </div>
          <button
            className="primary-btn"
            onClick={handleGenerate}
            disabled={loading || !topic.trim()}
          >
            {loading ? "Đang tạo..." : "Tạo bài trắc nghiệm"}
          </button>
        </div>
      )}

      {phase === "taking" && currentQ && (
        <div className="quiz-taking">
          <div className="quiz-progress">
            Câu {currentIndex + 1} / {questions.length}
            <span className="answered-count">Đã trả lời: {answeredCount}/{questions.length}</span>
          </div>

          <div className="quiz-question">
            <h3>{currentQ.question}</h3>
            <div className="quiz-options">
              {currentQ.options.map((opt, oIdx) => (
                <button
                  key={oIdx}
                  className={`quiz-option ${selectedAnswers[currentIndex] === oIdx ? "selected" : ""}`}
                  onClick={() => handleSelectAnswer(currentIndex, oIdx)}
                >
                  <span className="option-letter">{String.fromCharCode(65 + oIdx)}</span>
                  <span className="option-text">{opt}</span>
                </button>
              ))}
            </div>
          </div>

          <div className="quiz-nav">
            <button
              className="nav-btn"
              onClick={() => setCurrentIndex((i) => Math.max(0, i - 1))}
              disabled={currentIndex === 0}
            >
              ← Trước
            </button>
            <div className="question-dots">
              {questions.map((_, i) => (
                <button
                  key={i}
                  className={`dot ${i === currentIndex ? "active" : ""} ${selectedAnswers[i] !== undefined ? "answered" : ""}`}
                  onClick={() => setCurrentIndex(i)}
                />
              ))}
            </div>
            <button
              className="nav-btn"
              onClick={() => setCurrentIndex((i) => Math.min(questions.length - 1, i + 1))}
              disabled={currentIndex === questions.length - 1}
            >
              Tiếp →
            </button>
          </div>

          <button
            className="primary-btn submit-btn"
            onClick={handleSubmit}
            disabled={loading || answeredCount < questions.length}
          >
            {loading ? "Đang chấm..." : "Nộp bài"}
          </button>
        </div>
      )}

      {phase === "results" && results && (
        <div className="quiz-results">
          <div className="score-display">
            <div className="score-number">{results.score}/{results.total}</div>
            <div className="score-text">{results.feedback}</div>
          </div>

          <div className="results-detail">
            {results.results.map((r, i) => (
              <div key={i} className={`result-item ${r.is_correct ? "correct" : "wrong"}`}>
                <div className="result-header">
                  <span className="result-index">Câu {i + 1}</span>
                  <span className="result-badge">{r.is_correct ? "Đúng" : "Sai"}</span>
                </div>
                <div className="result-question">{questions[i]?.question}</div>
                {!r.is_correct && (
                  <div className="result-explanation">
                    Đáp án đúng: {String.fromCharCode(65 + r.correct_index)}
                    {r.explanation && <p>{r.explanation}</p>}
                  </div>
                )}
              </div>
            ))}
          </div>

          <div className="results-actions">
            <button className="primary-btn" onClick={handleRetry}>Làm lại</button>
            <button className="secondary-btn" onClick={onClose}>Quay lại</button>
          </div>
        </div>
      )}
    </div>
  );
}
