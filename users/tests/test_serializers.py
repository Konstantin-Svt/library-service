from django.test import TestCase

from users.serializers import UserSerializer


class TestSerializer(TestCase):
    def test_create_serializer_ignores_is_staff(self):
        serializer = UserSerializer(data={
            "email": "test@test.com",
            "password": "testpass123456",
            "is_staff": True
        })
        serializer.is_valid()
        self.assertNotIn("is_staff", serializer.data)

    def test_create_serializer_ignores_manual_id(self):
        serializer = UserSerializer(data={
            "email": "test@test.com",
            "password": "testpass123456",
            "id": "54"
        })
        serializer.is_valid()
        self.assertNotIn("id", serializer.data)
