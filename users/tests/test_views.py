from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase, APIClient


class TestViews(APITestCase):
    def setUp(self):
        self.client = APIClient()

    def test_user_creation_with_email_as_login(self):
        url = reverse("users:create")
        response = self.client.post(
            url, data={"email": "test@test.com", "password": "testpass12345"}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(get_user_model().objects.count(), 1)
