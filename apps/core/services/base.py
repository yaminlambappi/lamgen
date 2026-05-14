from django.db import transaction

class BaseService:
    def __enter__(self):
        transaction.set_autocommit(False)
        return self

    def __exit__(self, type, value, traceback):
        if type is None:
            transaction.commit()
        else:
            transaction.rollback()

    def _validate(self, data, validator_class):
        validator = validator_class(data=data)
        validator.is_valid(raise_exception=True)
        return validator.validated_data
