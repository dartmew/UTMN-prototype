# main.py
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase
from sqlalchemy import Column, Integer, String
from typing import List, Optional
import csv
import io

# -------------------------- Настройка базы данных --------------------------
SQLALCHEMY_DATABASE_URL = "sqlite:///./students.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

# -------------------------- Модель данных --------------------------
class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    last_name = Column(String(50), nullable=False)   # Фамилия
    first_name = Column(String(50), nullable=False)  # Имя
    faculty = Column(String(50), nullable=False)     # Факультет
    course = Column(String(100), nullable=False)     # Курс (предмет)
    grade = Column(Integer, nullable=False)          # Оценка

    def __repr__(self):
        return f"<Student {self.last_name} {self.first_name} {self.course}>"

# -------------------------- Инициализация таблиц --------------------------
Base.metadata.create_all(bind=engine)

# -------------------------- Зависимость для сессий --------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------------- FastAPI приложение --------------------------
app = FastAPI(title="Students API")

# ============================================================
#  1.  CRUD  (INSERT, SELECT, UPDATE, DELETE)
# ============================================================

# Создать студента
@app.post("/students/", response_model=dict)
def create_student(
    last_name: str,
    first_name: str,
    faculty: str,
    course: str,
    grade: int,
    db: Session = Depends(get_db)
):
    student = Student(
        last_name=last_name,
        first_name=first_name,
        faculty=faculty,
        course=course,
        grade=grade
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return {"message": "Студент создан", "id": student.id}

# Получить список всех студентов (можно с пагинацией)
@app.get("/students/")
def get_all_students(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    students = db.query(Student).offset(skip).limit(limit).all()
    return students

# Получить одного студента по id
@app.get("/students/{student_id}")
def get_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Студент не найден")
    return student

# Обновить студента
@app.put("/students/{student_id}")
def update_student(
    student_id: int,
    last_name: Optional[str] = None,
    first_name: Optional[str] = None,
    faculty: Optional[str] = None,
    course: Optional[str] = None,
    grade: Optional[int] = None,
    db: Session = Depends(get_db)
):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Студент не найден")
    if last_name is not None:
        student.last_name = last_name
    if first_name is not None:
        student.first_name = first_name
    if faculty is not None:
        student.faculty = faculty
    if course is not None:
        student.course = course
    if grade is not None:
        student.grade = grade
    db.commit()
    db.refresh(student)
    return student

# Удалить студента
@app.delete("/students/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Студент не найден")
    db.delete(student)
    db.commit()
    return {"message": "Студент удалён"}

# ============================================================
#  2.  Заполнение из CSV  (функция + эндпоинт)
# ============================================================

def fill_from_csv(file_path: str = "C:\Projects\Institute\Prototype\T4HW4\students.csv"):
    """Заполнение таблицы данными из CSV (очищает таблицу перед вставкой)."""
    db = SessionLocal()
    try:
        # Очистка таблицы (по желанию; можно удалить, если нужна дозагрузка)
        db.query(Student).delete()
        with open(file_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                student = Student(
                    last_name=row["Фамилия"],
                    first_name=row["Имя"],
                    faculty=row["Факультет"],
                    course=row["Курс"],
                    grade=int(row["Оценка"])
                )
                db.add(student)
        db.commit()
        print(f"Загружено {db.query(Student).count()} записей.")
    except Exception as e:
        db.rollback()
        print(f"Ошибка загрузки: {e}")
    finally:
        db.close()

# Эндпоинт для запуска импорта
@app.post("/load-csv")
def load_csv(db: Session = Depends(get_db)):
    fill_from_csv()
    return {"message": "Данные из CSV загружены"}

# ============================================================
#  3.  Специальные запросы
# ============================================================

# Студенты по факультету
@app.get("/faculty/{faculty}/students")
def get_students_by_faculty(faculty: str, db: Session = Depends(get_db)):
    students = db.query(Student).filter(Student.faculty == faculty).all()
    return students

# Уникальные курсы (предметы)
@app.get("/courses/unique")
def get_unique_courses(db: Session = Depends(get_db)):
    courses = db.query(Student.course).distinct().all()
    return [course[0] for course in courses]

# Студенты по курсу с оценкой ниже 30
@app.get("/course/{course}/lowgrades")
def get_students_low_grades(course: str, db: Session = Depends(get_db)):
    students = db.query(Student).filter(
        Student.course == course,
        Student.grade < 30
    ).all()
    return students

# Средний балл по факультету
@app.get("/faculty/{faculty}/average-grade")
def get_average_grade_by_faculty(faculty: str, db: Session = Depends(get_db)):
    avg = db.query(func.avg(Student.grade)).filter(Student.faculty == faculty).scalar()
    if avg is None:
        raise HTTPException(status_code=404, detail="Нет данных по факультету")
    return {"faculty": faculty, "average_grade": round(avg, 2)}

# ============================================================
#  4.  Экспорт в CSV (задание повышенной сложности)
# ============================================================
@app.get("/export/csv")
def export_csv(db: Session = Depends(get_db)):
    students = db.query(Student).all()
    output = io.StringIO()
    writer = csv.writer(output)
    # Заголовок в точности как исходный CSV
    writer.writerow(["Фамилия", "Имя", "Факультет", "Курс", "Оценка"])
    for s in students:
        writer.writerow([s.last_name, s.first_name, s.faculty, s.course, s.grade])
    # Возвращаем как plain text
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(content=output.getvalue(), media_type="text/csv")

# ============================================================
# Запуск
# ============================================================
if __name__ == "__main__":
    import uvicorn
    # При старте можно автоматически загрузить данные из CSV,
    # но только если таблица пуста (чтобы не дублировать)
    db = SessionLocal()
    if db.query(Student).count() == 0:
        fill_from_csv()
    db.close()
    
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)