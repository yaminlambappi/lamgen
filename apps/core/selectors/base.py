from django.core.paginator import Paginator

class BaseSelector:
    def __init__(self, model):
        self.model = model

    def get_all(self):
        return self.model.objects.all()

    def get_paginated(self, page_number, per_page=10):
        objects = self.get_all()
        paginator = Paginator(objects, per_page)
        return paginator.get_page(page_number)
