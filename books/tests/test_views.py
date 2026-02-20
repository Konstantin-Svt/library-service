from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient, APITestCase

from books.models import Book


class TestViews(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client = APIClient()

    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            email="user@admin.com", password="testuser123"
        )
        self.client.force_authenticate(self.user)

    def test_create_book(self):
        url = reverse("books:book-list")
        response = self.client.post(
            path=url,
            data={
                "title": "Test Book1",
                "author": "Test Author2",
                "cover": "SOFT",
                "inventory": "10",
                "daily_fee": "1.00",
            },
        )
        book = Book.objects.get(pk=1)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Book.objects.count(), 1)
        self.assertEqual(book.title, "Test Book1")
        self.assertEqual(book.author, "Test Author2")

    def test_patch_book(self):
        data = {
            "title": "Test Book",
            "author": "Test Author",
            "cover": "SOFT",
            "inventory": "10",
            "daily_fee": "1.00",
        }
        book = Book.objects.create(**data)
        url = reverse("books:book-detail", kwargs={"pk": 1})
        response = self.client.patch(url, data={"title": "New Title"})
        book.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(book.title, "New Title")

    def test_delete_book(self):
        data = {
            "title": "Test Book",
            "author": "Test Author",
            "cover": "SOFT",
            "inventory": "10",
            "daily_fee": "1.00",
        }
        Book.objects.create(**data)
        url = reverse("books:book-detail", kwargs={"pk": 1})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Book.objects.count(), 0)

    def test_create_book_admin_only(self):
        self.user.is_staff = False
        self.user.save()
        url = reverse("books:book-list")
        response = self.client.post(
            path=url,
            data={
                "title": "Test Book",
                "author": "Test Author",
                "cover": "SOFT",
                "inventory": "10",
                "daily_fee": "1.00",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Book.objects.count(), 0)

    def test_patch_delete_book_admin_only(self):
        self.user.is_staff = False
        self.user.save()
        data = {
            "title": "Test Book",
            "author": "Test Author",
            "cover": "SOFT",
            "inventory": "10",
            "daily_fee": "1.00",
        }
        book = Book.objects.create(**data)
        url = reverse("books:book-detail", kwargs={"pk": 1})
        response = self.client.patch(url, data={"title": "New Title"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertNotEqual(book.title, "New Title")

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Book.objects.count(), 1)
