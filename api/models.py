# 대화내용 유지할 수 있는 code 만들기 
import uuid
import datetime

from sqlalchemy import String, DateTime, Integer, ForeignKey, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


# 1:N 관계 Conversation(1) : Message(M) 
class Conversation(Base):
    __tablename__ = "conversation"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=uuid.uuid4,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), # mysql에게 시간을 직접 추가하는 명령어
    )

class Message(Base):
    __tablename__ = "message"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    conversation_id:Mapped[str] = mapped_column(
        ForeignKey("conversation.id")
    )
    role: Mapped[str] = mapped_column(String(10)) # user/ assistant (미리 약속된 단어- 고정값)
    content: Mapped[str] = mapped_column(Text) # 대용량의 text 저장할 때 사용
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(),
    )


    
