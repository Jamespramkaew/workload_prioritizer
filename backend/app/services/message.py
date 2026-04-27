from app.schemas.message_schema import MessageResponse


class MessageService:
    """Service for handling message operations"""
    
    @staticmethod
    def process_message(message: str) -> MessageResponse:
        """
        Process the incoming message and return it as a result
        
        Args:
            message: The input message to process
            
        Returns:
            MessageResponse containing the processed message
        """
        # Add any business logic here if needed
        return MessageResponse(result=message)
