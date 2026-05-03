import csv
from app.database import SessionLocal, engine
from app.models import Student, Base

# Создаём таблицы (если ещё не созданы)
Base.metadata.create_all(bind=engine)

def import_data():
    db = SessionLocal()
    try:
        with open('C:\Projects\Institute\Prototype\T3HW3\students.csv', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                student = Student(
                    last_name=row['Фамилия'],
                    first_name=row['Имя'],
                    faculty=row['Факультет'],
                    course=row['Курс'],
                    grade=int(row['Оценка'])
                )
                db.add(student)
        db.commit()
        print("Данные успешно загружены.")
    except Exception as e:
        db.rollback()
        print(f"Ошибка: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    import_data()