from crewai import Agent, Task, Crew
import google.generativeai as genai
import streamlit as st
from langchain.llms.base import LLM
from typing import Any, List, Optional
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY
import os
from langchain.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
import re
import logging

logging.basicConfig(level=logging.INFO)

# Configure the Google API
genai.configure(api_key="AIzaSyDmf0d09V7jGsuN-kfZ6Di-bF0LbCyH7_I")

class GeminiProLLM(LLM):
    model: Any
    
    def __init__(self):
        super().__init__()
        self.model = genai.GenerativeModel('gemini-1.0-pro')

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        response = self.model.generate_content(prompt)
        return response.text

    @property
    def _identifying_params(self) -> dict:
        return {"name": "GeminiPro"}

    @property
    def _llm_type(self) -> str:
        return "GeminiPro"

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def create_homework_agent():
    return Agent(
        role='Homework Creator',
        goal='Create engaging and educational homework assignments',
        backstory='You are an experienced educator with expertise in creating homework that reinforces learning objectives.',
        verbose=True,
        allow_delegation=False,
        llm=GeminiProLLM()
    )

def create_practice_questions_agent():
    return Agent(
        role='Practice Question Generator',
        goal='Generate diverse and challenging practice questions',
        backstory='You are a skilled question designer with a knack for creating questions that test understanding and critical thinking.',
        verbose=True,
        allow_delegation=False,
        llm=GeminiProLLM()
    )

def create_rag_agent():
    return Agent(
        role='RAG-based Question Generator',
        goal='Generate questions based on retrieved documents',
        backstory='You are an AI specialized in creating questions from contextual information.',
        verbose=True,
        allow_delegation=False,
        llm=GeminiProLLM()
    )

def generate_homework(subject, grade, topic, vark_preference, learning_stage, learning_objective, time_allocation, difficulty_level, required_materials, previous_knowledge, curriculum_standards, cultural_context):
    homework_agent = create_homework_agent()
    task = Task(
        description=f"""As an experienced and creative {subject} teacher for grade {grade}, design a fun and engaging homework activity on the topic of {topic} that feels like a game. The activity should:

1. Reinforce the following specific learning objective: {learning_objective}
2. Be tailored for students with a {vark_preference} learning preference
3. Be appropriate for the {learning_stage} learning stage
4. Take approximately {time_allocation} to complete
5. Have a difficulty level of {difficulty_level} out of 5
6. Use the following materials: {required_materials}
7. Build upon this previous knowledge: {previous_knowledge}
8. Align with {curriculum_standards} standards
9. Consider this cultural context: {cultural_context}
10. Incorporate elements of play or storytelling
11. Be enjoyable and not feel like a chore

Provide a detailed description of the activity, including:
- Clear instructions for students
- Educational goals and how they align with the learning objective
- How the activity caters to the specified VARK preference
- Any adaptations needed for different difficulty levels within the same learning stage
- How to present it to students in an exciting way
- Any safety considerations if using household items

Ensure the activity is engaging, educational, and appropriate for the specified grade level and learning stage.""",
        agent=homework_agent,
        expected_output="A comprehensive, fun, and engaging homework activity description, including all specified parameters, educational goals, and presentation suggestions."
    )
    crew = Crew(
        agents=[homework_agent],
        tasks=[task],
        verbose=2
    )
    result = crew.kickoff()
    return result

def generate_practice_questions(subject, grade, topic, num_questions, vark_preference, learning_stage, question_types, skill_focus, difficulty_distribution, time_per_question, use_visuals, real_world_application, blooms_taxonomy_level):
    practice_questions_agent = create_practice_questions_agent()
    
    # Load documents if needed
    # documents = load_documents(grade, subject, [topic])
    
    task = Task(
        description=f"""As an experienced {subject} teacher for grade {grade}, create {num_questions} practice questions on the topic of {topic}. Your task is to:

1. Design questions appropriate for the {learning_stage} learning stage
2. Cater to the {vark_preference} learning preference
3. Use primarily {question_types} question types
4. Focus on developing {skill_focus} skills
5. Follow this difficulty distribution: {difficulty_distribution}
6. Design each question to take approximately {time_per_question} to answer
7. {use_visuals} use visuals (diagrams, graphs, or images) in questions
8. Create questions that are {real_world_application} in nature
9. Target the {blooms_taxonomy_level} level of Bloom's Taxonomy

Ensure that the questions:
- Are clear, concise, and grade-appropriate
- Align with key learning objectives for this topic
- Promote critical thinking and understanding
- Are engaging and relevant to students

For multiple-choice questions, include 4 options with one correct answer.
For open-ended questions, provide a brief outline of what a good answer should include.

Format your response as follows:
1. [Question Type] Question text
   a) Option A (if multiple-choice)
   b) Option B
   c) Option C
   d) Option D
   Correct Answer: [Provide correct answer or answer outline for open-ended questions]
   VARK Category: [Specify which VARK category this question primarily addresses]
   Bloom's Taxonomy Level: [Specify the Bloom's Taxonomy level this question targets]

Repeat this format for all {num_questions} questions.""",
        agent=practice_questions_agent,
        expected_output=f"A set of {num_questions} well-crafted practice questions, tailored to the specified parameters, including question types, VARK preferences, learning stage, and Bloom's Taxonomy levels."
    )
    
    crew = Crew(
        agents=[practice_questions_agent],
        tasks=[task],
        verbose=2
    )
    
    result = crew.kickoff()
    return result

def retrieve_relevant_documents(subject, grade, topic):
    # TODO: Implement document retrieval logic
    # This is a placeholder function that returns an empty list
    return []

def generate_rag_based_questions(subject, grade, chapter_name, num_questions, question_type):
    file_path = f"database/{grade}/{subject.lower()}/{chapter_name.lower().replace(' ', '_')}.md"
    if not os.path.exists(file_path):
        logging.error(f"File not found: {file_path}")
        return f"Error: Relevant document not found. File path: {file_path}"

    with open(file_path, 'r', encoding='utf-8') as file:
        chapter_content = file.read()

    llm = GeminiProLLM()

    prompt = f"""You are a teacher creating a test for your students. 
    Focus EXCLUSIVELY on the following content from the {subject} chapter "{chapter_name}" for grade {grade}:

    Chapter Content:
    {chapter_content}

    Your task is to create {num_questions} {question_type} questions based STRICTLY on the above chapter content. 
    Follow these rules:

    1. Use ONLY the information provided in the chapter content above. Do not add any external information or knowledge.
    2. Create questions that cover the main ideas, key details, and important concepts presented in the chapter.
    3. Ensure that every question and answer can be directly derived from the given chapter content.
    4. Include a mix of questions about the main text (story, poem, or informational content) and any exercises or activities mentioned.
    5. Do not create questions about topics or information not explicitly mentioned in the provided chapter content.
    6. STRICTLY adhere to the format specified for each question type.

    Strictly follow the format for each question type. They should be as follows:

    For Multiple Choice questions:
    **Question X: [Difficulty]**
    [Question text]
    Options:
    A) [Option A]
    B) [Option B]
    C) [Option C]
    D) [Option D]
    Correct Answer: [Letter of correct option]

    For Fill in the Blank questions:
    **Question X: [Difficulty]**
    [Sentence with a blank represented by an underline __________ where the answer should go]
    Answer: [Correct answer]

    For Short Answer questions:
    **Question X: [Difficulty]**
    [Question text]
    Answer: [Correct answer or key points expected in the answer]

    For True/False questions:
    **Question X: [Difficulty]**
    [Statement to be judged as true or false]
    Options:
    A) True
    B) False
    Correct Answer: [A or B]

    For Essay questions:
    **Question X: [Difficulty]**
    [Essay prompt or question]
    Answer: [Key points or outline of what a good answer should include]

    Remember, EVERY question must be answerable using ONLY the information provided in the chapter content. Do not introduce any concepts, ideas, or information not explicitly stated in the given text.

    IMPORTANT: For Fill in the Blank questions, always use an underline __________ to represent the blank, and provide the exact word or phrase as the answer."""

    try:
        result = llm._call(prompt)
        logging.info(f"AI response for {subject} grade {grade}, chapter '{chapter_name}': {result}")
        return result
    except Exception as e:
        logging.error(f"Error calling LLM for {subject} grade {grade}, chapter '{chapter_name}': {str(e)}")
        return f"Error: Failed to generate questions. {str(e)}"

def save_homework_to_supabase(subject, grade, topic, content, vark_preference, learning_stage):
    data = {
        "subject": subject,
        "grade": grade,
        "topic": topic,
        "content": content,
        "vark_preference": vark_preference,
        "learning_stage": learning_stage
    }
    result = supabase.table("homeworks").insert(data).execute()
    return result

def save_practice_questions_to_supabase(subject, grade, topic, content):
    data = {
        "subject": subject,
        "grade": grade,
        "topic": topic,
        "content": content
    }
    result = supabase.table("practice_questions").insert(data).execute()
    return result

def save_rag_questions_to_supabase(subject, grade, topic, questions, question_type):
    for question in questions:
        correct_answer = question.get("correct_answer", "")
        # If it's a multiple-choice question, extract just the letter
        if question.get("options") and correct_answer.startswith(("A)", "B)", "C)", "D)")):
            correct_answer = correct_answer[0]
        
        data = {
            "subject": subject,
            "grade": grade,
            "topic": topic,
            "question_type": question_type,
            "question_text": question["question_text"],
            "correct_answer": correct_answer,
            "difficulty": question.get("difficulty", "Unknown"),
            "options": question.get("options", [])
        }
        result = supabase.table("test_questions").insert(data).execute()
    return "Questions saved successfully!"

def load_chapter_names(subject, grade):
    folder_path = f"database/{grade}/{subject.lower()}"
    if not os.path.exists(folder_path):
        return ["No chapters found"]
    
    chapter_files = [f.split('.')[0].replace('_', ' ').title() for f in os.listdir(folder_path) if f.endswith('.md')]
    return chapter_files if chapter_files else ["No chapters found"]

