import json

class ResponseParser:
    def parse(self, response: str):
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Handle cases where the response is not a valid JSON
            # This could involve more sophisticated parsing logic
            return {"error": "Invalid JSON response"}
