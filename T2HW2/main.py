from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator, ValidationError
from datetime import datetime
from typing import Optional, Dict, Any
import re

app = FastAPI()

# ---------------------- UserRegistration ----------------------
class UserRegistration(BaseModel):
    username: str = Field(..., min_length=3, max_length=20, pattern=r'^[a-zA-Z0-9_]+$')
    email: EmailStr
    password: str = Field(..., min_length=8)
    password_confirm: str
    age: int = Field(..., ge=18, le=120)
    registration_date: datetime = Field(default_factory=datetime.now)
    real_name: str = Field(..., min_length=2)
    phone: str = Field(..., pattern=r'^\+\d{1}-\d{3}-\d{2}-\d{2}$')

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not re.search(r'[0-9]', v):
            raise ValueError('Пароль должен содержать хотя бы одну цифру')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Пароль должен содержать хотя бы одну заглавную букву')
        if not re.search(r'[a-z]', v):
            raise ValueError('Пароль должен содержать хотя бы одну строчную букву')
        return v

    @model_validator(mode='after')
    def check_passwords_match(self) -> 'UserRegistration':
        if self.password != self.password_confirm:
            raise ValueError('Пароли не совпадают')
        return self

    @field_validator('real_name')
    @classmethod
    def validate_real_name(cls, v: str) -> str:
        if v[0].islower():
            raise ValueError('Имя должно начинаться с заглавной буквы')
        return v

    # Отключаем password_confirm из сериализации
    class Config:
        json_schema_extra = {
            "exclude": ["password_confirm"]
        }

    def model_dump(self, **kwargs):
        kwargs.setdefault('exclude', set()).add('password_confirm')
        return super().model_dump(**kwargs)

# ---------------------- RecursiveModel (бонус) ----------------------
class RecursiveModel(BaseModel):
    data: str
    child: Optional['RecursiveModel'] = None   # forward reference в кавычках

# ---------------------- Эндпоинты ----------------------
@app.post("/register")
async def register_user(data: Dict[str, Any]):
    try:
        user = UserRegistration(**data)
        return {"message": "Пользователь успешно зарегистрирован", "user": user.model_dump()}
    except ValidationError as e:
        errors = [f"{err['loc'][0]}: {err['msg']}" for err in e.errors()]
        raise HTTPException(status_code=422, detail=errors)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/recursive")
async def recursive(data: RecursiveModel):
    return data

# ---------------------- Запуск ----------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        'main:app',
        host='0.0.0.0',
        port=8000,
        reload=True
    )