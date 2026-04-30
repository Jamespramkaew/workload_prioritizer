from app.schemas.message_schema import MessageRequest, MessageResponse
from app.services.message import MessageService


class MessageController:
    def __init__(self):
        self._service = MessageService()

    @property
    def service(self) -> MessageService:
        return self._service

    def echo_message(self, request: MessageRequest) -> MessageResponse:
        return self._service.process_message(request.message)
