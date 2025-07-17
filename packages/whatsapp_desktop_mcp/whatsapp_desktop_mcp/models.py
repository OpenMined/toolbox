from pydantic import BaseModel


class ContactMatch(BaseModel):
    query: str
    contact_name: str
    contact_id: str
    score: float


class ContactMatchResponse(BaseModel):
    matches: list[ContactMatch]


class MessageResponse(BaseModel):
    chat_name: str
    message_text: str
    message_date: int
    sender_name: str
    is_group_chat: bool

    @classmethod
    def from_sql_row(cls, row):
        return cls(
            chat_name=row[1],
            message_text=row[2],
            message_date=row[3],
            sender_name=row[4],
            is_group_chat=row[5],
        )


class ChatResponse(BaseModel):
    chat_name: str | None
    messages: list[MessageResponse]

    def print(self):
        print(f"=== Chat: {self.chat_name} ===")
        for message in self.messages:
            if message.is_group_chat:
                print(
                    f"# {message.sender_name} ({message.message_date}): {message.message_text}"
                )
            else:
                print(
                    f"# {message.sender_name} ({message.message_date}): {message.message_text}"
                )


class MultipleChatsResponse(BaseModel):
    chats: list[ChatResponse]
