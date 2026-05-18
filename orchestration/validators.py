from jsonschema import validate
from jsonschema.exceptions import ValidationError

class ResponseValidator:
    def __init__(self, schema):
        self.schema = schema

    def validate(self, data):
        try:
            validate(instance=data, schema=self.schema)
            return True, None
        except ValidationError as e:
            return False, e.message
