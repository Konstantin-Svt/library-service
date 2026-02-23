from rest_framework.serializers import ModelSerializer

from books.models import Book


class BookSerializer(ModelSerializer):
    class Meta:
        model = Book
        fields = ("id", "title", "author", "cover", "inventory", "daily_fee")
