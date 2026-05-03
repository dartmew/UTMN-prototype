from fastapi import FastAPI
import uvicorn


app = FastAPI()

LANGUAGES = {
    1: 'C++',
    2: 'JS',
    3: 'Python'
}


@app.get('/')
async def root():
    return {'mes': 'hello world'}


@app.get('/lang/{item_id}')
async def lang(item_id):
    return {'lang': LANGUAGES.get(int(item_id), 'unknown')}


@app.get('/sum/')
async def sum(a: int = 0, b: int = 0):
    return{'sum': a+b}


if __name__ == "__main__":
    uvicorn.run(
        'main:app',
        host='0.0.0.0',
        port=8000,
        reload = True
    )