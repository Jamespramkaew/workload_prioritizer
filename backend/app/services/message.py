from app.schemas.message_schema import MessageResponse


class MessageService:
    def __init__(self):
        self._processed_count = 0

    @property
    def processed_count(self) -> int:
        return self._processed_count

    def process_message(self, message: str) -> MessageResponse:
        if not message or not message.strip():
            raise ValueError("Message cannot be empty")
        self._processed_count += 1
        return MessageResponse(result=message)
