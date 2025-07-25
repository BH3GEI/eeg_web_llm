class DifyUserConfig:
    def __init__(self,
                 api_key:str = None,
                 base_url:str = None,
                 user:str = None):
        """
        Initialize the chatbot configuration.

        This constructor sets up the necessary configuration parameters for the chatbot.
        Each parameter has a default value to be used if no explicit value is provided.

        Parameters:
        - api_key (str): API key for the chatbot, used for authentication.
        - base_url (str): Base URL for the chatbot service.
        - conversation_id (str): ID of the conversation, used to track the context of the dialogue.
        - user (str): Identifier for the user utilizing the chatbot.

        Returns:
        No return value. This method only initializes the chatbot object.
        """
        self.api_key = api_key
        self.base_url = base_url
        self.user = user