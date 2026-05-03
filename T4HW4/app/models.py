from sqlalchemy import Column, Integer, String
from app.database import Base

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    last_name = Column(String(50), nullable=False)
    first_name = Column(String(50), nullable=False)
    faculty = Column(String(50), nullable=False)
    course = Column(String(100), nullable=False)  # предмет (например, "Мат. Анализ")
    grade = Column(Integer, nullable=False)

    def __repr__(self):
        return f"<Student {self.last_name} {self.first_name} {self.course}>"