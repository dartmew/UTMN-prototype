from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict
import operator
import re

app = FastAPI()

# -------------------- Модели данных --------------------
class EvaluateRequest(BaseModel):
    expression: str
    variables: Dict[str, float] = {}

# -------------------- Вспомогательные функции парсинга --------------------
def tokenize(expr: str) -> list:
    """Разбивает строку выражения на токены (числа, переменные, операторы, скобки)."""
    token_pattern = re.compile(r'(\d+\.?\d*|[a-zA-Z_]\w*|[+\-*/()])')
    tokens = token_pattern.findall(expr.replace(' ', ''))
    # Приведение оператора унарного минуса (например, -a или (-b)) – для простоты опустим,
    # считаем что выражение корректно и все минусы бинарные.
    return tokens

def shunting_yard(tokens: list, variables: Dict[str, float]) -> list:
    """Преобразует инфиксное выражение в обратную польскую запись (ОПЗ)."""
    output = []
    operators = []
    precedence = {'+': 1, '-': 1, '*': 2, '/': 2}
    associativity = {'+': 'L', '-': 'L', '*': 'L', '/': 'L'}

    for token in tokens:
        if re.match(r'^\d+\.?\d*$', token):      # число
            output.append(float(token))
        elif re.match(r'^[a-zA-Z_]\w*$', token): # переменная
            if token not in variables:
                raise HTTPException(status_code=400, detail=f"Variable '{token}' not provided")
            output.append(variables[token])
        elif token in precedence:
            while (operators and operators[-1] != '(' and
                   ((associativity[token] == 'L' and precedence[token] <= precedence[operators[-1]]) or
                    (associativity[token] == 'R' and precedence[token] < precedence[operators[-1]]))):
                output.append(operators.pop())
            operators.append(token)
        elif token == '(':
            operators.append(token)
        elif token == ')':
            while operators and operators[-1] != '(':
                output.append(operators.pop())
            if not operators or operators[-1] != '(':
                raise HTTPException(status_code=400, detail="Mismatched parentheses")
            operators.pop()  # удаляем '('
        else:
            raise HTTPException(status_code=400, detail=f"Invalid token: {token}")

    while operators:
        if operators[-1] == '(':
            raise HTTPException(status_code=400, detail="Mismatched parentheses")
        output.append(operators.pop())

    return output

def evaluate_rpn(rpn: list) -> float:
    """Вычисляет значение выражения в ОПЗ."""
    stack = []
    ops = {
        '+': operator.add,
        '-': operator.sub,
        '*': operator.mul,
        '/': operator.truediv
    }

    for token in rpn:
        if isinstance(token, (int, float)):
            stack.append(token)
        else:
            if len(stack) < 2:
                raise HTTPException(status_code=400, detail="Invalid expression")
            b = stack.pop()
            a = stack.pop()
            if token == '/' and b == 0:
                raise HTTPException(status_code=400, detail="Division by zero")
            stack.append(ops[token](a, b))
    
    if len(stack) != 1:
        raise HTTPException(status_code=400, detail="Invalid expression")
    
    return stack[0]


# -------------------- Простые операции (задание 1) --------------------
@app.get("/sum/")
async def sum_op(a: float, b: float):
    return {"result": a + b}


@app.get("/subtract/")
async def subtract_op(a: float, b: float):
    return {"result": a - b}


@app.get("/multiply/")
async def multiply_op(a: float, b: float):
    return {"result": a * b}


@app.get("/divide/")
async def divide_op(a: float, b: float):
    if b == 0:
        raise HTTPException(status_code=400, detail="Division by zero")
    return {"result": a / b}


# -------------------- Вычисление сложного выражения (задание 2) --------------------
@app.post("/evaluate")
async def evaluate(request: EvaluateRequest):
    tokens = tokenize(request.expression)
    rpn = shunting_yard(tokens, request.variables)
    result = evaluate_rpn(rpn)
    return {"result": result}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        'main:app',
        host='0.0.0.0',
        port=8000,
        reload=True
    )
