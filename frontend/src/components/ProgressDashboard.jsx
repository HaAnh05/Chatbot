/**
 * ProgressDashboard Component
 * Display learning progress, analytics, and recommendations
 */

import React, { useState, useEffect } from "react";
import * as api from "../api";
import "./ProgressDashboard.css";

export default function ProgressDashboard({ subject, onClose }) {
  const [progress, setProgress] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadProgress();
  }, [subject]);

  const loadProgress = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getProgress(1, subject);
      if (data.error) throw new Error(data.error);
      setProgress(data.summary);
      setAnalytics(data.analytics);
    } catch (err) {
      setError("Không thể tải tiến trình.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="progress-panel">
        <div className="panel-header">
          <h2>Tiến Trình Học Tập</h2>
          <button className="close-btn" onClick={onClose}>✕</button>
        </div>
        <div className="progress-loading">Đang tải...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="progress-panel">
        <div className="panel-header">
          <h2>Tiến Trình Học Tập</h2>
          <button className="close-btn" onClick={onClose}>✕</button>
        </div>
        <div className="panel-error">{error}</div>
        <button className="secondary-btn" onClick={loadProgress}>Thử lại</button>
      </div>
    );
  }

  const confidencePercent = Math.round((progress?.confidence_level || 0) * 100);
  const topics = progress?.topics_covered || {};
  const topicEntries = Object.entries(topics).sort((a, b) => b[1] - a[1]);

  return (
    <div className="progress-panel">
      <div className="panel-header">
        <h2>Tiến Trình Học Tập</h2>
        <button className="close-btn" onClick={onClose}>✕</button>
      </div>

      {/* Stats Cards */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-value">{confidencePercent}%</div>
          <div className="stat-label">Mức độ tự tin</div>
          <div className="stat-bar">
            <div
              className="stat-bar-fill"
              style={{ width: `${confidencePercent}%` }}
            />
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{progress?.total_conversations || 0}</div>
          <div className="stat-label">Cuộc hội thoại</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{progress?.total_exercises_completed || 0}</div>
          <div className="stat-label">Bài tập đã làm</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{analytics?.learning_streak || 0}</div>
          <div className="stat-label">Chuỗi ngày học</div>
        </div>
      </div>

      {/* Topics */}
      {topicEntries.length > 0 && (
        <div className="section">
          <h3>Chủ đề đã học</h3>
          <div className="topic-badges">
            {topicEntries.map(([topic, conf]) => {
              const level = conf > 0.7 ? "strong" : conf > 0.4 ? "medium" : "weak";
              return (
                <div key={topic} className={`topic-badge ${level}`}>
                  <span className="topic-name">{topic}</span>
                  <span className="topic-conf">{Math.round(conf * 100)}%</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Recommendations */}
      {progress?.recommendations && progress.recommendations.length > 0 && (
        <div className="section">
          <h3>Gợi ý</h3>
          <ul className="recommendations-list">
            {progress.recommendations.map((rec, i) => (
              <li key={i}>{rec}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Weekly Progress */}
      {analytics?.weekly_progress && Object.keys(analytics.weekly_progress).length > 0 && (
        <div className="section">
          <h3>Hoạt động 7 ngày qua</h3>
          <div className="weekly-dots">
            {Array.from({ length: 7 }, (_, i) => {
              const date = new Date();
              date.setDate(date.getDate() - (6 - i));
              const key = date.toISOString().split("T")[0];
              const count = analytics.weekly_progress[key] || 0;
              return (
                <div key={i} className="day-column">
                  <div
                    className={`day-dot ${count > 0 ? "active" : ""}`}
                    style={{ opacity: count > 0 ? Math.min(1, 0.3 + count * 0.2) : 0.2 }}
                    title={`${key}: ${count} hội thoại`}
                  />
                  <span className="day-label">
                    {["CN", "T2", "T3", "T4", "T5", "T6", "T7"][date.getDay()]}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Strengths & Weaknesses */}
      {analytics && (
        <div className="sw-section">
          {analytics.strengths && analytics.strengths.length > 0 && (
            <div className="sw-block strengths">
              <h4>Điểm mạnh</h4>
              {analytics.strengths.map((s, i) => (
                <span key={i} className="sw-tag strong">{s}</span>
              ))}
            </div>
          )}
          {analytics.weaknesses && analytics.weaknesses.length > 0 && (
            <div className="sw-block weaknesses">
              <h4>Cần cải thiện</h4>
              {analytics.weaknesses.map((w, i) => (
                <span key={i} className="sw-tag weak">{w}</span>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="progress-actions">
        <button className="secondary-btn" onClick={loadProgress}>Làm mới</button>
        <button className="secondary-btn" onClick={onClose}>Quay lại</button>
      </div>
    </div>
  );
}
