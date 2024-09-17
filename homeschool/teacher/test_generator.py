from crewai import Agent
from langchain.schema import Document

class TestGenerator(Agent):
    def __init__(self, grade: int, subject: str, chapters: list, llm, raw_documents: list[Document]):
        super().__init__(
            role="Test Generator",
            goal=f"Create challenging and fair multiple-choice questions for {subject} in Grade {grade}",
            backstory=f"You are an experienced {subject} exam creator for Grade {grade}",
            allow_delegation=False,
            llm=llm
        )

        self.grade = grade
        self.subject = subject
        self.chapters = chapters
        self.raw_documents = raw_documents

    def execute(self, task_description: str) -> str:
        num_questions = int(task_description.split("Generate ")[1].split(" questions")[0])

        chapter_docs = [doc for doc in self.raw_documents if doc.metadata['chapter'] in self.chapters]

        if not chapter_docs:
            return f"No content found for the specified chapters in {self.subject} for Grade {self.grade}."

        context = "\n".join([doc.page_content for doc in chapter_docs])

        prompt = f"""
        Based SOLELY on the following content from the textbook, create {num_questions} multiple-choice questions for {self.subject} in Grade {self.grade}, covering chapters {', '.join(map(str, self.chapters))}.
        Include 4 options for each question and indicate the correct answer.
        Do not invent any information that is not present in the given content.
        If there isn't enough information to create {num_questions} questions, create as many as possible based on the available content.

        Content:
        {context[:10000]}  # Limit context to avoid token limits

        Generate questions:
        """

        questions = self.llm.generate(prompt)
        return f"Generated questions for {self.subject} in Grade {self.grade} based on the provided content:\n\n{questions}"