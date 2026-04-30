# tests/factories.py

import factory
from factory.django import DjangoModelFactory
from assets.tests.factories import AssetFactory,ModelFactory
from assets.models import (
    Tbljob, Tbljobstatus,Tbljobtypes, Tbltechnicianlist,
    Tbltesteqused,Tblcheckslists, Tbltestscarriedout,
    Tbltestresult,Tblpartsused)

from parts.models import Tblpartslist



#job factories
JOB_TECHNICIAN = ["Alice","Bob"]
class JobTechnicianFactory(DjangoModelFactory):
    class Meta:
        model = Tbltechnicianlist
        django_get_or_create = ('name',)


    name = factory.Iterator(JOB_TECHNICIAN,cycle=True)
    technicianid = factory.Sequence(lambda n: 10000 + n)



JOB_STATUS = ["Inprogress","Completed","Not Started"]
class JobStatusFactory(DjangoModelFactory):
    class Meta:
        model = Tbljobstatus
        django_get_or_create = ('jobstatus',)


    jobstatus = factory.Iterator(JOB_STATUS,cycle=True)
    jobstatusid = factory.Sequence(lambda n: 10000 + n)

JOB_TYPES = ["PPM","Repair"]
class JobTypeFactory(DjangoModelFactory):
    class Meta:
        model = Tbljobtypes
        django_get_or_create = ('jobtypename',)


    jobtypename = factory.Iterator(JOB_TYPES,cycle=True)
    jobtypeid = factory.Sequence(lambda n: 10000 + n)



class JobFactory(DjangoModelFactory):
    class Meta:
        model = Tbljob

    jobstartdate = factory.Faker('date_between', start_date='-2y', end_date='-1y')
    jobenddate = factory.Faker('date_between', start_date='-1y', end_date='today')
    workdone = factory.Faker('sentence', nb_words=10) 
    jobstatusid = factory.SubFactory(JobStatusFactory)
    technicianid = factory.SubFactory(JobTechnicianFactory)
    assetid = factory.SubFactory(AssetFactory)
    jobtypeid = factory.SubFactory(JobTypeFactory)


#test equipment used factory
TESTEQID = [1,2,3]

class TestEquipmentUsedFactory(DjangoModelFactory):
    class Meta:
        model = Tbltesteqused
    
    jobid = factory.SubFactory(JobFactory)
    test_eq = None



CHECKS = [
    "Visual Inspection",
    "Function Test",
    "Safety Check",
    "Calibration Check",
    "Performance Test",
    "Electrical Safety Test",
    "Pressure Test",
    "Alignment Check",
    "Leak Test",
    "Operational Test"
]
class ChecklistsFactory(DjangoModelFactory):
    class Meta:
        model = Tblcheckslists
        django_get_or_create = ('testname',)

    testname = factory.Iterator(CHECKS, cycle=True)
    test_description = factory.Faker('sentence', nb_words=10) 
    modelid = factory.SubFactory(ModelFactory)

RESULTNAME = ["Pass","Fail","N/A"]
RESULTID =[1,2,3]
class TestResultFactory(DjangoModelFactory):
    class Meta:
        model = Tbltestresult
        django_get_or_create = ('resultname',)

    resultname = factory.Iterator(RESULTNAME, cycle=True)
    resultid = factory.Iterator(RESULTID, cycle=True)


class TestsCarriedOutFactory(DjangoModelFactory):
    class Meta:
        model = Tbltestscarriedout

    jobid = factory.SubFactory(JobFactory)
    checkid = factory.SubFactory(ChecklistsFactory)
    resultid = factory.SubFactory(TestResultFactory)


PARTTNAME = ["Nut","Bolt","Battery"]
PARTID = [1,2,3]

#spare parts factory
class PartsListFactory(DjangoModelFactory):
    class Meta:
        model = Tblpartslist
        django_get_or_create = ('short_name',)
    part_number = factory.Iterator(PARTID,cycle=True)
    short_name = factory.Iterator(PARTTNAME,cycle=True)


class PartsUsedFactory(DjangoModelFactory):
    class Meta:
        model = Tblpartsused

    jobid = factory.SubFactory(JobFactory)
    quantity = factory.Faker('random_int', min=1, max=10)
    partid = factory.SubFactory(PartsListFactory)
    unitprice = factory.Faker('random_int', min=1, max=100)
