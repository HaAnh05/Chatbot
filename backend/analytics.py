"""
Progress Analytics & Student Tracking
Tracks learning progress, topic coverage, and provides insights
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from backend.database import SessionLocal
from backend.models import User, Conversation, Message, StudentProgress, Exercise, ExerciseSubmission, now_gmt7
from backend.logger import get_logger, log_progress_event
from collections import defaultdict

logger = get_logger("analytics")


class ProgressTracker:
    """Track and analyze student learning progress"""

    def __init__(self):
        self.db = SessionLocal()
        logger.debug("ProgressTracker initialized")

    def update_progress(self, user_id: int, subject: str, conversation_id: int) -> StudentProgress:
        """Update student progress based on conversation activity"""
        log_progress_event(logger, "Updating progress", {
            "user_id": user_id,
            "subject": subject,
            "conversation_id": conversation_id,
        })
        try:
            # Get or create progress record
            progress = self.db.query(StudentProgress).filter(
                StudentProgress.user_id == user_id,
                StudentProgress.subject == subject
            ).first()

            if not progress:
                progress = StudentProgress(
                    user_id=user_id,
                    subject=subject,
                    topics_covered="{}",
                    confidence_level=0.0,
                    total_conversations=0,
                    total_exercises_completed=0
                )
                self.db.add(progress)

            # Analyze conversation for topics
            conversation = self.db.query(Conversation).filter(
                Conversation.id == conversation_id
            ).first()

            if conversation:
                # Extract topics from conversation messages
                topics = self._extract_topics_from_conversation(conversation_id)
                current_topics = self._parse_topics(progress.topics_covered)

                # Update topic coverage
                for topic, confidence in topics.items():
                    current_topics[topic] = max(current_topics.get(topic, 0), confidence)

                progress.topics_covered = self._serialize_topics(current_topics)
                progress.total_conversations += 1

                # Calculate overall confidence
                if current_topics:
                    progress.confidence_level = sum(current_topics.values()) / len(current_topics)

                progress.last_updated = now_gmt7()

            self.db.commit()
            self.db.refresh(progress)
            return progress

        except Exception as e:
            self.db.rollback()
            raise e
        finally:
            self.db.close()

    def get_progress_summary(self, user_id: int, subject: str) -> Dict:
        """Get comprehensive progress summary"""
        log_progress_event(logger, "Getting progress summary", {
            "user_id": user_id,
            "subject": subject,
        })
        try:
            progress = self.db.query(StudentProgress).filter(
                StudentProgress.user_id == user_id,
                StudentProgress.subject == subject
            ).first()

            if not progress:
                return {
                    "subject": subject,
                    "confidence_level": 0.0,
                    "total_conversations": 0,
                    "total_exercises_completed": 0,
                    "topics_covered": {},
                    "recommendations": ["Bắt đầu học với các khái niệm cơ bản"],
                    "last_updated": None
                }

            topics = self._parse_topics(progress.topics_covered)

            # Generate recommendations based on progress
            recommendations = self._generate_recommendations(topics, subject)

            return {
                "subject": subject,
                "confidence_level": progress.confidence_level,
                "total_conversations": progress.total_conversations,
                "total_exercises_completed": progress.total_exercises_completed,
                "topics_covered": topics,
                "recommendations": recommendations,
                "last_updated": progress.last_updated.isoformat() if progress.last_updated else None
            }

        except Exception as e:
            raise e
        finally:
            self.db.close()

    def get_learning_analytics(self, user_id: int) -> Dict:
        """Get detailed learning analytics across all subjects"""
        log_progress_event(logger, "Getting learning analytics", {"user_id": user_id})
        try:
            # Get all progress records
            progress_records = self.db.query(StudentProgress).filter(
                StudentProgress.user_id == user_id
            ).all()

            # Get conversation history
            conversations = self.db.query(Conversation).filter(
                Conversation.user_id == user_id
            ).order_by(Conversation.created_at.desc()).limit(50).all()

            # Analyze learning patterns
            analytics = {
                "subjects": {},
                "total_conversations": len(conversations),
                "learning_streak": self._calculate_streak(conversations),
                "most_active_subject": None,
                "recent_topics": [],
                "weekly_progress": self._get_weekly_progress(conversations),
                "strengths": [],
                "weaknesses": []
            }

            # Process each subject
            for progress in progress_records:
                topics = self._parse_topics(progress.topics_covered)
                analytics["subjects"][progress.subject] = {
                    "confidence": progress.confidence_level,
                    "topics_count": len(topics),
                    "exercises_completed": progress.total_exercises_completed
                }

            # Find most active subject
            if analytics["subjects"]:
                most_active = max(analytics["subjects"].items(),
                                key=lambda x: x[1]["topics_count"])
                analytics["most_active_subject"] = most_active[0]

            # Extract recent topics
            recent_convs = conversations[:10]
            for conv in recent_convs:
                topics = self._extract_topics_from_conversation(conv.id)
                analytics["recent_topics"].extend(list(topics.keys())[:3])

            analytics["recent_topics"] = list(set(analytics["recent_topics"][:10]))

            # Identify strengths and weaknesses
            all_topics = {}
            for progress in progress_records:
                topics = self._parse_topics(progress.topics_covered)
                all_topics.update(topics)

            if all_topics:
                sorted_topics = sorted(all_topics.items(), key=lambda x: x[1], reverse=True)
                analytics["strengths"] = [topic for topic, conf in sorted_topics[:5] if conf > 0.7]
                analytics["weaknesses"] = [topic for topic, conf in sorted_topics[-5:] if conf < 0.4]

            return analytics

        except Exception as e:
            raise e
        finally:
            self.db.close()

    def _extract_topics_from_conversation(self, conversation_id: int) -> Dict[str, float]:
        """Extract topics discussed in a conversation with confidence scores"""
        messages = self.db.query(Message).filter(
            Message.conversation_id == conversation_id,
            Message.role == "user"
        ).all()

        topics = {}

        # Simple keyword-based topic extraction
        topic_keywords = {
            "cpp": {
                "variables": ["biến", "variable", "int", "string", "float"],
                "loops": ["vòng lặp", "for", "while", "loop", "lặp"],
                "functions": ["hàm", "function", "def", "return"],
                "arrays": ["mảng", "array", "vector", "list"],
                "pointers": ["con trỏ", "pointer", "address"],
                "classes": ["lớp", "class", "object", "oop"],
                "inheritance": ["kế thừa", "inheritance", "extends"],
                "templates": ["template", "generic", "typename"]
            },
            "python": {
                "variables": ["biến", "variable", "int", "str", "float"],
                "loops": ["vòng lặp", "for", "while", "loop"],
                "functions": ["hàm", "function", "def", "return"],
                "lists": ["list", "mảng", "array"],
                "dictionaries": ["dict", "dictionary", "key-value"],
                "classes": ["class", "object", "oop"],
                "modules": ["module", "import", "package"],
                "comprehensions": ["comprehension", "list comprehension"]
            }
        }

        for message in messages:
            content = message.content.lower()

            # Check all subjects and topics
            for subject, subject_topics in topic_keywords.items():
                for topic, keywords in subject_topics.items():
                    if any(keyword in content for keyword in keywords):
                        # Increase confidence if topic is mentioned multiple times
                        topics[topic] = min(1.0, topics.get(topic, 0) + 0.3)

        return topics

    def _parse_topics(self, topics_str: str) -> Dict[str, float]:
        """Parse topics JSON string to dict"""
        try:
            import json
            return json.loads(topics_str) if topics_str else {}
        except:
            return {}

    def _serialize_topics(self, topics_dict: Dict[str, float]) -> str:
        """Serialize topics dict to JSON string"""
        try:
            import json
            return json.dumps(topics_dict)
        except:
            return "{}"

    def _generate_recommendations(self, topics: Dict[str, float], subject: str) -> List[str]:
        """Generate learning recommendations based on progress"""
        recommendations = []

        if not topics:
            recommendations.append("Bắt đầu học với các khái niệm cơ bản")
            return recommendations

        # Find weak areas
        weak_topics = [topic for topic, conf in topics.items() if conf < 0.5]

        if weak_topics:
            recommendations.append(f"Cần ôn tập lại: {', '.join(weak_topics[:3])}")

        # Suggest next topics based on current progress
        if subject == "cpp":
            cpp_progression = [
                "variables", "loops", "functions", "arrays",
                "pointers", "classes", "inheritance", "templates"
            ]
        else:  # python
            cpp_progression = [
                "variables", "loops", "functions", "lists",
                "dictionaries", "classes", "modules", "comprehensions"
            ]

        # Find next topic to learn
        learned_topics = set(topics.keys())
        for topic in cpp_progression:
            if topic not in learned_topics:
                recommendations.append(f"Chủ đề tiếp theo nên học: {topic}")
                break

        # General recommendations
        if len(topics) > 5:
            recommendations.append("Thử làm bài tập thực hành để củng cố kiến thức")

        if max(topics.values()) > 0.8:
            recommendations.append("Bạn đã khá vững, thử học chủ đề nâng cao")

        return recommendations[:3]  # Limit to 3 recommendations

    def _calculate_streak(self, conversations: List[Conversation]) -> int:
        """Calculate current learning streak in days"""
        if not conversations:
            return 0

        # Get unique dates when conversations occurred
        dates = set()
        for conv in conversations:
            dates.add(conv.created_at.date())

        sorted_dates = sorted(dates, reverse=True)

        streak = 0
        current_date = now_gmt7().date()

        for date in sorted_dates:
            if date == current_date:
                streak += 1
                current_date -= timedelta(days=1)
            elif date == current_date - timedelta(days=1):
                streak += 1
                current_date = date
            else:
                break

        return streak

    def _get_weekly_progress(self, conversations: List[Conversation]) -> Dict[str, int]:
        """Get conversation count by day for the last 7 days"""
        weekly = defaultdict(int)
        week_ago = now_gmt7() - timedelta(days=7)

        for conv in conversations:
            if conv.created_at >= week_ago:
                day = conv.created_at.strftime("%Y-%m-%d")
                weekly[day] += 1

        return dict(weekly)

    def close(self):
        """Close database session"""
        self.db.close()
