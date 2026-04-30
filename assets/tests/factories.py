# tests/factories.py

import factory
from factory.django import DjangoModelFactory
from assets.models import (
    Tblassets, Tblbrands, Tblmodel, Tblcustomer,
    TblAssetStatus, Tblcategories, Tblppmschedules,
    Tbljob,Tbljobstatus, Tbljobtypes,Tbltechnicianlist
    
)

CATEGORY_NAMES = ["suction", "diathermy","monitor"]
class CategoryFactory(DjangoModelFactory):
    class Meta:
        model = Tblcategories
        django_get_or_create = ('categoryname',)

    categoryname = factory.Iterator(CATEGORY_NAMES, cycle=True)

BRAND_NAMES = ["Meditech", "PulseGear", "NeuroLab"]
class BrandFactory(DjangoModelFactory):
    class Meta:
        model = Tblbrands
        django_get_or_create = ('brandname',)


    brandname = factory.Iterator(BRAND_NAMES,cycle=True)


LIMITED_CUSTOMER_NAMES = ["Customer_A", "Customer_B"]
class CustomerFactory(DjangoModelFactory):
    class Meta:
        model = Tblcustomer
        django_get_or_create = ('customer_name',)

    customer_name = factory.Iterator(LIMITED_CUSTOMER_NAMES, cycle=True)

class ModelFactory(DjangoModelFactory):
    class Meta:
        model = Tblmodel
        django_get_or_create = ('modelname',)

    modelname = factory.Faker('word')
    brandid = factory.SubFactory(BrandFactory)
    categoryid = factory.SubFactory(CategoryFactory)

ASSET_STATUS = ["Active", "Quarantined", "Decommissioned"]
class AssetStatusFactory(DjangoModelFactory):
    class Meta:
        model = TblAssetStatus
        django_get_or_create = ('status_name',)


    asset_status_id = factory.Sequence(lambda n: n + 1)
    status_name = factory.Iterator(ASSET_STATUS,cycle=True)


PPM_SCHEDULES = ['12M','24M','36M','48M']
class PpmScheduleFactory(DjangoModelFactory):
    class Meta:
        model = Tblppmschedules
        django_get_or_create = ('schedulename',)
    
    schedulename = factory.Iterator(PPM_SCHEDULES, cycle=True)
    schedulefrequency = factory.Iterator([1, 3, 6, 12], cycle=True)


class AssetFactory(DjangoModelFactory):
    class Meta:
        model = Tblassets

    modelid = factory.SubFactory(ModelFactory)
    customerid = factory.SubFactory(CustomerFactory)
    serialnumber = factory.Sequence(lambda n: 15245155412 + n)
    asset_status_id = factory.SubFactory(AssetStatusFactory)
    ppmscheduleid = factory.SubFactory(PpmScheduleFactory)


