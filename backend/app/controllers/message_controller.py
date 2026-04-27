from app.schemas.message_schema import MessageRequest, MessageResponse
from app.services.message import MessageService


class MessageController:
    """Controller for handling message-related endpoints"""
    
    def __init__(self):
        self.service = MessageService()
    
    def echo_message(self, request: MessageRequest) -> MessageResponse:
        """
        Handle echo message request
        
        Args:
            request: MessageRequest containing the message
            
        Returns:
            MessageResponse with the processed message
        """
        return self.service.process_message(request.message)
