
FROM python:3.13-slim
WORKDIR /app
# 관례적으로 app을 많이 씀, (내 폴더를 따로 둘거다)
COPY . .
# 현재 폴더의 파일 전부를 docker 안으로 옮긴다
RUN pip install -r requirements.txt
# RUN 이미지를 만드는 과정에서 실행함
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
# CMD docker 안에있는 프로그램 실행,  "0.0.0.0" 모든 ip주로를 허용한다. 
