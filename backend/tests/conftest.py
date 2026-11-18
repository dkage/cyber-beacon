import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user(
        username="pilot", email="pilot@example.test", password="test-password-982"
    )


@pytest.fixture
def other_user(db):
    return get_user_model().objects.create_user(
        username="other", email="other@example.test", password="test-password-982"
    )


@pytest.fixture
def client(user):
    client = APIClient()
    client.force_authenticate(user)
    return client
