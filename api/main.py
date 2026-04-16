from fastapi import FastAPI
from sqlalchemy import text
from connection import SessionFactory


app = FastAPI()

@app.get("/health-check")
def health_check_handler():
    with SessionFactory() as session:
        stmt = text("SELECT * FROM user LIMIT 1;")
        row = session.execute(stmt).fetchone() 
    return {"user": row._asdict()} # row._asdict(): fastapi(json)error 방지를 위해 dict형태로 변환
    