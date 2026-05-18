from orchestration.services import AIOrchestrator

class BaseToolService:
    def __init__(self, user=None):
        self.user = user

    def execute(self, tool_slug, user_input):
        orchestrator = AIOrchestrator(tool_slug, user_input, self.user)
        return orchestrator.execute()
