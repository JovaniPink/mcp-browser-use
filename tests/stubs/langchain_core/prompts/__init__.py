class ChatPromptTemplate:
    @staticmethod
    def from_messages(msgs):
        return ChatPromptTemplate()
    def __or__(self, other):
        return self
    def invoke(self, data):
        return ''

class MessagesPlaceholder:
    def __init__(self, variable_name=''):
        pass
