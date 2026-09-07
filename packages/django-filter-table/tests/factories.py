import factory

import random
from datetime import timedelta
from factory.django import DjangoModelFactory
from django.contrib.auth import get_user_model
from .testapp.models import(
    Tblcustomer,
    Tblassets,
    Tblbrands,
    Tblmodel,
    JobView,
)

User = get_user_model()
class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

BRAND_NAMES = ["Meditech", "PulseGear", "NeuroLab"]
class BrandFactory(DjangoModelFactory):
    class Meta:
        model = Tblbrands
        django_get_or_create = ('brandname',)


    brandname = factory.Iterator(BRAND_NAMES,cycle=True)

class ModelFactory(DjangoModelFactory):
    class Meta:
        model = Tblmodel
        django_get_or_create = ('modelname',)

    modelname = factory.Faker('word')
    brandid = factory.SubFactory(BrandFactory)

LIMITED_CUSTOMER_NAMES = ["Customer_A", "Customer_B"]
class CustomerFactory(DjangoModelFactory):
    class Meta:
        model = Tblcustomer
        django_get_or_create = ('customer_name',)

    customer_name = factory.Iterator(LIMITED_CUSTOMER_NAMES, cycle=True)

class AssetFactory(DjangoModelFactory):
    class Meta:
        model = Tblassets

    modelid = factory.SubFactory(ModelFactory)
    customerid = factory.SubFactory(CustomerFactory)
    serialnumber = factory.Sequence(lambda n: 15245155412 + n)
    customerassetnumber = factory.Sequence(lambda n: 1 + n)


class JobFactory(DjangoModelFactory):
    class Meta:
        model = JobView


    enddate = factory.Faker(
        "date_between",
        start_date="-3y",
        end_date="today",
    )

    startdate = factory.LazyAttribute(
        lambda obj: obj.enddate - timedelta(days=random.randint(1, 14))
    )
    workdone = factory.Faker('sentence', nb_words=10) 
    assetid = factory.SubFactory(AssetFactory)
    modelid = factory.LazyAttribute(
        lambda obj: obj.assetid.modelid
    )

