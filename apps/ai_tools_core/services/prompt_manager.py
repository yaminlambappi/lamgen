from ..models import PromptTemplate

class PromptManager:
    @classmethod
    def get_prompt(cls, tool_slug: str, user_input: str) -> str:
        try:
            prompt_template = PromptTemplate.objects.get(tool_slug=tool_slug, is_active=True)
            return f"{prompt_template.system_prompt}\n{prompt_template.user_prompt_template.format(user_input=user_input)}"
        except PromptTemplate.DoesNotExist:
            raise ValueError(f"Prompt for tool \'{tool_slug}\' not found.")
