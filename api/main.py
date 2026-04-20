import uuid # 중복 없이 id 만들어줌 
import json
from fastapi import FastAPI, Body, HTTPException
from fastapi.responses import StreamingResponse
from redis import asyncio as aredis
from sqlalchemy import select

from connection_async import AsyncSessionFactory
from models import Conversation, Message



redis_client = aredis.from_url("redis://redis:6379", decode_responses=True) # ("redis://<ip이름>:6379")
# decode_responses=True : 문자열로 바꿔달라는 의미 

app = FastAPI()

# 복수형 conversations로 post 생성
@app.post(
    "/conversations",
    summary="대화 시작 API",
)
async def create_conversation_handler():
    async with AsyncSessionFactory() as session:
        conversation = Conversation()
        session.add(conversation)
        await session.commit()
        await session.refresh(conversation)
    return conversation


@app.get(
    "/conversations/{conversation_id}/messages",
    summary="전체 메세지 조회 API"
)
async def get_messages_handler(
    conversation_id: str
):
    async with AsyncSessionFactory() as session:
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.id.asc())
        )
        result = await session.execute(stmt)
        messages = result.scalars().all()
    return messages



@app.post(
    "/conversations/{conversation_id}/messages",
    summary="메세지 생성 API",
)
async def create_message_handler(
    conversation_id: str,
    user_input: str = Body(..., embed=True),
):
    async with AsyncSessionFactory() as session:
        # 1) 대화방 확인
        conversation = await session.get(Conversation, conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=404, detail="Conversation Not Found"
            )
        
        # 2) 사용자 메시지 생성
        user_msg = Message(
            conversation_id=conversation.id,
            role="user",
            content=user_input,
        )
        session.add(user_msg)

        # 3) 이전 대화내역 조회
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation.id)
            .order_by(Message.id.asc()) # id 기준 오름차순
        )
        result = await session.execute(stmt)
        messages = result.scalars().all()

        # Context Rot 방지
        # 1) message 개수가 N개 이상되면, 요약해서 저장
        # 2) 대화 내역 중에 주제가 바뀌면, 이전 메시지는 무시

        history = [
            {"role": m.role, "content": m.content} for m in messages
        ]

        # 4) 작업 내용을 Enqueue
        channel = conversation.id
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(channel)

        task = {"channel": channel, "messages": history}
        await redis_client.lpush("queue", json.dumps(task))

        await session.commit() # 사용자가 방금 생성한 대화 commit
    
    async def event_listener():
        assistant_text = ""

        async for message in pubsub.listen():
            if message["type"] != "message":
                continue
            
            token = message["data"]
            if token == "[DONE]":
                break

            assistant_text += token
            yield token

        # LLM 응답 메시지 저장
        async with AsyncSessionFactory() as session:
            assistant_msg = Message(
                conversation_id=conversation_id,
                role="assistant",
                content=assistant_text
            )
            session.add(assistant_msg)
            await session.commit()
        
        await pubsub.unsubscribe(channel)
        await pubsub.close()

    return StreamingResponse(
        event_listener(),
        media_type="text/event-stream",
    )

# @app.post("/chats")
# async def generate_chat_handler(
#     # 1) 요청 본문: user_input 입력
#     user_input: str = Body(..., embed=True),
#     conversation_id: str | None = Body(None, embed=True)
# ):  
#     # a) conversation_id is None -> 새로운 대화를 시작할 때
#     #   1. convrtsation 생성, message 생성, message를 enqueue
#     async with AsyncSessionFactory() as session:
#         if conversation_id is None:
#             conversation = Conversation()
#             session.add(conversation)
#             await session.flush() # flush는 임시 저장:   

#     # b) conversation_id:str -> 기존의 대화를 이어나갈 때 
#         #   1. conversation_id로 messages 조회, 2. message를 enqueue 
#         else:
#             conversation = await session.get(Conversation, conversation_id)
#             if not conversation:
#                 raise HTTPException(
#                     status_code=404,
#                     detail="conversation Not Found"
#                 )
#         # 사용자 메시지 생성
#         user_msg = Message(
#             conversation_id=conversation.id,
#             role="user",
#             content=user_input,
#         )
        
#         session.add(user_msg)
#         # 이전 메시지 조회
#         stmt = (
#             select(Message.role, Message.content)
#             .where(Message.conversation_id == conversation.id)
#             .order_by(Message.id.asc()) # id 기준 오름차순
#         )
#         result = await session.execute(stmt)
#         messages: list[dict] = result.mappings().all()

#         history =[
#             {"role":"", "content":""}
#         ]

#     # 작업 내용을 Enqueue
#     # 2) 안전하게 subscribe먼저, channel
#     channel = conversation_id # 각 대화별로 conversation.id 넘긴다 
#     pubsub = redis_client.pubsub()
#     await pubsub.subscribe(channel)


#     # 3) 처리 : queue를 통해 worker에 queue를 통해 job을 전달 (= enqueue 한다)
#     task = {"channel": channel, "messages": messages}
#     await redis_client.lpush("queue", json.dumps(task))

    # # 4) 채널 메세지 읽기(대기), 토큰 반환
    # async def event_generator():

    #     async for message in pubsub.listen():
    #         if message["type"] != "message":
    #             # 실제 메세지가 아닌 상태메세지는 무시
    #             continue

    #         token = message["data"]
    #         if token == "[DONE]":
    #             break
    #         yield token

    #     await pubsub.unsubscribe(channel)
    #     await pubsub.close()


    # # 5) 결과 수신
    # return StreamingResponse(
    #     event_generator(),
    #     media_type="text/event-stream",
    # )