import random
from supabase import create_client, Client
from ..config import SUPABASE_URL, SUPABASE_KEY
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class AdaptiveAgent:
    def __init__(self, user_id):
        self.user_id = user_id
        self.student_profile = self.load_student_profile()
        self.question_history = []
        self.vectorizer = TfidfVectorizer()
        self.correct_phrases = [
            "Great job!", "Excellent work!", "You nailed it!", "Spot on!",
            "Perfect!", "You're on fire!", "Fantastic!", "Brilliant!",
            "You've got this!", "Impressive!", "Well done!", "Superb!",
        ]
        self.incorrect_phrases = [
            "Nice try!", "Almost there!", "Keep going!", "Don't give up!",
            "You're making progress!", "You can do it!", "Keep at it!",
            "You're learning!", "Every mistake is a chance to learn!",
            "You're getting closer!", "Keep pushing yourself!",
        ]

    def load_student_profile(self):
        # Fetch student profile from database
        response = supabase.table("student_profiles").select("*").eq("custom_id", self.user_id).execute()
        if response.data:
            return response.data[0]
        else:
            # Create a new profile if it doesn't exist
            new_profile = {
                "custom_id": self.user_id,
                "strengths": [],
                "weaknesses": [],
                "difficulty_preference": "medium"
            }
            supabase.table("student_profiles").insert(new_profile).execute()
            return new_profile

    def evaluate_answer(self, question, user_answer, correct_answer):
        question_type = question['question_type']
        
        if question_type in ['Multiple Choice', 'True/False']:
            is_correct = user_answer.lower() == correct_answer.lower()
            similarity = 1.0 if is_correct else 0.0
        elif question_type == 'Fill in the Blank':
            is_correct = user_answer.strip().lower() == correct_answer.strip().lower()
            similarity = 1.0 if is_correct else 0.0
        else:  # Short Answer
            answer_vectors = self.vectorizer.fit_transform([user_answer, correct_answer])
            similarity = cosine_similarity(answer_vectors[0], answer_vectors[1])[0][0]
            is_correct = similarity > 0.8  # You can adjust this threshold

        # Update student profile based on performance
        self.update_profile(question, is_correct)

        return is_correct, similarity

    def update_profile(self, question, is_correct):
        topic = question['topic']
        difficulty = question['difficulty']

        if is_correct:
            if topic not in self.student_profile['strengths']:
                self.student_profile['strengths'].append(topic)
            if topic in self.student_profile['weaknesses']:
                self.student_profile['weaknesses'].remove(topic)
        else:
            if topic not in self.student_profile['weaknesses']:
                self.student_profile['weaknesses'].append(topic)

        # Adjust difficulty preference
        if is_correct and difficulty == 'hard':
            self.student_profile['difficulty_preference'] = 'hard'
        elif not is_correct and difficulty == 'easy':
            self.student_profile['difficulty_preference'] = 'easy'

        # Update profile in database
        supabase.table("student_profiles").update(self.student_profile).eq("custom_id", self.user_id).execute()

        # Add question to history
        self.question_history.append({
            'topic': topic,
            'difficulty': difficulty,
            'is_correct': is_correct
        })

    def select_next_question(self, subject, chapter, available_questions):
        # Filter questions based on difficulty preference
        preferred_difficulty = self.student_profile['difficulty_preference']
        suitable_questions = [q for q in available_questions if q['difficulty'] == preferred_difficulty]

        if not suitable_questions:
            suitable_questions = available_questions

        # Prioritize questions from weak topics
        weak_topic_questions = [q for q in suitable_questions if q['topic'] in self.student_profile['weaknesses']]

        if weak_topic_questions:
            return random.choice(weak_topic_questions)
        else:
            return random.choice(suitable_questions)

    def generate_feedback(self, question, is_correct, similarity=None):
        if is_correct:
            feedback = random.choice(self.correct_phrases) + " "
        else:
            feedback = random.choice(self.incorrect_phrases) + " "
        
        if question['question_type'] == 'Short Answer' and similarity is not None:
            feedback += f"Your answer was {similarity:.2%} similar to the correct answer. "

        if not is_correct:
            feedback += f"The correct answer is: {question['correct_answer']}. "

        # Add topic-specific feedback
        topic = question['topic']
        if topic in self.student_profile['weaknesses']:
            feedback += random.choice([
                f"Let's focus on improving your understanding of {topic}. ",
                f"{topic} seems challenging. Let's work on it together! ",
                f"With more practice, you'll master {topic} in no time! "
            ])
        elif topic in self.student_profile['strengths']:
            feedback += random.choice([
                f"You're showing great strength in {topic}! ",
                f"Keep up the excellent work in {topic}! ",
                f"Your understanding of {topic} is impressive! "
            ])

        return feedback

    def generate_summary(self):
        summary = "Test Summary:\n"
        summary += f"Strengths: {', '.join(self.student_profile['strengths'])}\n"
        summary += f"Areas for Improvement: {', '.join(self.student_profile['weaknesses'])}\n"
        summary += f"Current difficulty level: {self.student_profile['difficulty_preference']}\n"
        
        # Calculate overall performance
        total_questions = len(self.question_history)
        correct_answers = sum(1 for q in self.question_history if q['is_correct'])
        performance = correct_answers / total_questions if total_questions > 0 else 0
        
        summary += f"\nOverall Performance: {performance:.2%}\n"
        
        # Provide personalized recommendations
        if performance < 0.5:
            summary += "\nRecommendation: Consider reviewing the material and practicing more. You've got this!\n"
        elif performance < 0.8:
            summary += "\nRecommendation: You're doing well! Focus on your weaker areas to improve further.\n"
        else:
            summary += "\nRecommendation: Excellent work! Challenge yourself with harder questions to keep growing.\n"
        
        return summary

    def analyze_performance_trend(self):
        if len(self.question_history) < 5:
            return "Not enough data to analyze performance trend."
        
        recent_performance = [q['is_correct'] for q in self.question_history[-5:]]
        trend = sum(recent_performance) / len(recent_performance)
        
        if trend > 0.8:
            return "Your recent performance is excellent! Keep up the great work!"
        elif trend > 0.6:
            return "You're showing good progress. Keep pushing yourself!"
        else:
            return "Your recent performance suggests you might need some extra practice. Don't give up!"
