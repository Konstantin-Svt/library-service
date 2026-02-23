from django.apps import AppConfig


class BorrowingsConfig(AppConfig):
    name = "borrowings"

    def ready(self):
        import borrowings.signals
