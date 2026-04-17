import uuid # 중복 없이 id 만들어줌 
import json
from fastapi import FastAPI, Body
from fastapi.responses import StreamingResponse
from redis import asyncio as aredis


redis_client = aredis.from_url("redis://redis:6379", decode_responses=True) # ("redis://<ip이름>:6379")
# decode_responses=True : 문자열로 바꿔달라는 의미 

app = FastAPI()

@app.post("/chats")
async def generate_chat_handler(
    # 1) 요청 본문: user_input 입력
    user_input: str = Body(..., embed=True)
):  
    # 2) 안전하게 subscribe먼저, channel

    channel = str(uuid.uuid4())
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(channel)

    # 3) 처리 : queue를 통해 worker에 queue를 통해 job을 전달 (= enqueue 한다)
    task = {"channel": channel, "user_input": user_input}
    await redis_client.lpush("queue", json.dumps(task))

    # 4) 채널 메세지 읽기(대기), 토큰 반환
    async def event_generator():

        async for message in pubsub.listen():
            if message["type"] != "message":
                # 실제 메세지가 아닌 상태메세지는 무시
                continue

            token = message["data"]
            if token == "[DONE]":
                break
            yield token

        await pubsub.unsubscribe(channel)
        await pubsub.close()


    # 5) 결과 수신
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )