"""Model factories for test data generation using factory-boy.

Provides a `UserFactory` that generates realistic test users with
pre-hashed passwords.
"""

import uuid

import factory

from app.core.security import hash_password
from app.models.user import User

__all__: list[str] = ["UserFactory"]


class UserFactory(factory.Factory):
    """Factory for creating User model instances in tests.

    Usage:
        user = UserFactory()
        user = UserFactory(email="custom@example.com")
        user = UserFactory.build()  # does not persist
    """

    class Meta:
        model = User

    id = factory.LazyFunction(uuid.uuid4)
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    username = factory.Sequence(lambda n: f"user{n}")
    hashed_password = factory.LazyFunction(lambda: hash_password("Password1"))
    is_active = True
    is_superuser = False
