/**
 * MinigamePanel Component
 * Coding challenges with LLM-based evaluation
 */

import React, { useState } from "react";
import * as api from "../api";
import "./MinigamePanel.css";

export default function MinigamePanel({ subject, onClose }) {
  const [phase, setPhase] = useState("setup"); // setup | playing | result
  const [topic, setTopic] = useState("");
  const [difficulty, setDifficulty] = useState("beginner");
  const [challenge, setChallenge] = useState(null);
  const [code, setCode] = useState("");
  const [showHints, setShowHints] = useState(false);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleStart = async () => {
    if (!topic.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await api.startMinigame(subject, topic, difficulty);
      if (data.error) throw new Error(data.error);
      setChallenge(data);
      setCode(data.starter_code || "");
      setResult(null);
      setShowHints(false);
      setPhase("playing");
    } catch (err) {
      setError("Không thể tạo bài tập. Vui lòng thử lại.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!code.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await api.submitMinigame(challenge.exercise_id, code);
      if (data.error) throw new Error(data.error);
      setResult(data);
      setPhase("result");
    } catch (err) {
      setError("Không thể nộp bài. Vui lòng thử lại.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleRetry = () => {
    setCode(challenge?.starter_code || "");
    setResult(null);
    setPhase("playing");
  };

  const handleNewChallenge = () => {
    setPhase("setup");
    setChallenge(null);
    setCode("");
    setResult(null);
  };

  return (
    <div className="minigame-panel">
      <div className="panel-header">
        <h2>Thử Thách Code</h2>
        <button className="close-btn" onClick={onClose}>✕</button>
      </div>

      {error && <div className="panel-error">{error}</div>}

      {phase === "setup" && (
        <div className="minigame-setup">
          <div className="form-group">
            <label>Chủ đề:</label>
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="VD: sắp xếp, đệ quy, linked list..."
              onKeyDown={(e) => e.key === "Enter" && handleStart()}
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
            onClick={handleStart}
            disabled={loading || !topic.trim()}
          >
            {loading ? "Đang tạo..." : "Bắt đầu thử thách"}
          </button>
        </div>
      )}

      {phase === "playing" && challenge && (
        <div className="minigame-playing">
          <div className="challenge-info">
            <h3>{challenge.title}</h3>
            <p className="challenge-desc">{challenge.description}</p>

            {challenge.test_cases && challenge.test_cases.length > 0 && (
              <div className="test-cases-preview">
                <div className="section-label">Test cases:</div>
                {challenge.test_cases.map((tc, i) => (
                  <div key={i} className="test-case">
                    <span className="tc-label">Test {i + 1}:</span>
                    <span className="tc-input">Input: {tc.input}</span>
                    <span className="tc-output">Expected: {tc.expected_output}</span>
                  </div>
                ))}
              </div>
            )}

            {challenge.hints && challenge.hints.length > 0 && (
              <div className="hints-section">
                <button
                  className="hints-toggle"
                  onClick={() => setShowHints((s) => !s)}
                >
                  {showHints ? "Ẩn gợi ý" : "Xem gợi ý"} ({challenge.hints.length})
                </button>
                {showHints && (
                  <ul className="hints-list">
                    {challenge.hints.map((h, i) => (
                      <li key={i}>{h}</li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </div>

          <div className="code-editor-section">
            <div className="editor-label">Code của bạn:</div>
            <textarea
              className="code-editor"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="Viết code ở đây..."
              spellCheck={false}
            />
          </div>

          <div className="minigame-actions">
            <button
              className="primary-btn"
              onClick={handleSubmit}
              disabled={loading || !code.trim()}
            >
              {loading ? "Đang chấm..." : "Nộp bài"}
            </button>
            <button className="secondary-btn" onClick={handleNewChallenge}>
              Bài mới
            </button>
          </div>
        </div>
      )}

      {phase === "result" && result && (
        <div className="minigame-result">
          <div className={`result-banner ${result.passed ? "passed" : "failed"}`}>
            <div className="result-icon">{result.passed ? "✓" : "✗"}</div>
            <div className="result-title">
              {result.passed ? "Hoàn thành!" : "Chưa đạt"}
            </div>
            <div className="result-score">Điểm: {result.score}/100</div>
          </div>

          <div className="result-feedback">
            <div className="section-label">Nhận xét:</div>
            <p>{result.feedback}</p>
          </div>

          {result.test_results && result.test_results.length > 0 && (
            <div className="test-results">
              <div className="section-label">Kết quả test:</div>
              {result.test_results.map((tr, i) => (
                <div
                  key={i}
                  className={`test-result-item ${tr.passed ? "passed" : "failed"}`}
                >
                  <span className="tr-icon">{tr.passed ? "✓" : "✗"}</span>
                  <span className="tr-label">{tr.test}</span>
                </div>
              ))}
            </div>
          )}

          <div className="result-actions">
            <button className="primary-btn" onClick={handleRetry}>Thử lại</button>
            <button className="secondary-btn" onClick={handleNewChallenge}>Bài mới</button>
            <button className="secondary-btn" onClick={onClose}>Quay lại</button>
          </div>
        </div>
      )}
    </div>
  );
}
