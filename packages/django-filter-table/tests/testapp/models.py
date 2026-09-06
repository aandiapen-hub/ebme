from django.contrib.auth.models import AbstractUser
from django.db import models

from django_filter_table.utils import HtmxPicker

class CustomUser(AbstractUser):
    pass


class UserProfile(models.Model):
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="profile",
    )

class Tblbrands(models.Model):
    brandid = models.BigAutoField(
        db_column="BrandID", primary_key=True, verbose_name="ID"
    )
    brandname = models.CharField(
        db_column="BrandName", unique=True, verbose_name="Brand"
    )

    htmx_picker = HtmxPicker(
        enabled=True,
        search_terms=('brandname__icontains',)
    )

class Tblmodel(models.Model):
    modelname = models.CharField(
        db_column="ModelName", max_length=100, verbose_name="Model Name"
    )
    modelid = models.BigAutoField(
        db_column="ModelID", primary_key=True, verbose_name='ID'
    )
    brandid = models.ForeignKey(
        "Tblbrands",
        models.PROTECT,
        db_column="BrandID",
        verbose_name='Brand',
        related_name='model'
    )

    htmx_picker = HtmxPicker(
        enabled=True,
        search_terms=(
            'modelname__icontains',
            'brandid__brandname__icontains',
        ),
        label_str = lambda obj: f"{obj.modelname} ({obj.brandid})"
    )

class Tblassets(models.Model):
    assetid = models.BigAutoField(
        db_column="AssetID", primary_key=True, verbose_name="ID"
    )
    customerassetnumber = models.CharField(
        db_column="CustomerAssetNumber",
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Customer Asset",
    )
    customerid = models.ForeignKey(
        "Tblcustomer", models.PROTECT, db_column="CustomerID", verbose_name="Customer"
    )
    modelid = models.ForeignKey(
        Tblmodel, models.PROTECT, db_column="ModelID", verbose_name="Model"
    )

class JobView(models.Model):
    jobid = models.CharField(
        primary_key=True,
        db_column='JobID',
        verbose_name="Job",
    )
    startdate = models.DateField(blank=True, null=True, verbose_name="Start Date")
    enddate = models.DateField(blank=True, null=True, verbose_name="End Date")
    workdone = models.TextField(
        db_column="WorkDone", blank=True, null=True, verbose_name="Work Done"
    )
    serialnumber = models.CharField(
        db_column="SerialNumber",
        max_length=255,
        blank=True,
        null=True,
        verbose_name="SN",
    )
    jobstatusid = models.ForeignKey(
        "Tbljobstatus",
        models.PROTECT,
        db_column="JobStatusID",
        blank=True,
        null=True,
        verbose_name="Job Status",
    )
    technicianid = models.ForeignKey(
        "Tbltechnicianlist",
        models.PROTECT,
        db_column="TechnicianID",
        blank=True,
        null=True,
        verbose_name="Technician",
    )
    assetid = models.ForeignKey(
        Tblassets, models.PROTECT, db_column="AssetID", related_name="job_view"
    )
    modelid = models.ForeignKey(
        Tblmodel, models.PROTECT, db_column="ModelID", verbose_name="Model"
    )
    total_cost = models.DecimalField(
        db_column="Total Cost",
        max_digits=100,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Cost of parts",
    )


