import factory
from factory.django import DjangoModelFactory
from django.contrib.auth import get_user_model

User = get_user_model()
class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    user_name = factory.Sequence(lambda n: f"user{n}")
    email = factory.Sequence(lambda n: f"user{n}@test.com")
    password = factory.PostGenerationMethodCall("set_password", "pass123")
    password='testpass',
    first_name='test',
    last_name='test',
