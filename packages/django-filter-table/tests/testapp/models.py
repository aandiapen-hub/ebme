from django.contrib.auth.models import AbstractUser
from django.db import models

from django_filter_table.utils import HtmxPicker
from django.urls import reverse

class Tblcustomer(models.Model):
    customer_name = models.CharField(
        db_column="Customer Name", unique=True, max_length=100, verbose_name="Customer"
    )
    customer_address = models.CharField(
        db_column="Customer Address",
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Address",
    )
    customer_phone = models.CharField(
        db_column="Customer Phone",
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Phone",
    )
    customerid = models.BigAutoField(
        db_column="CustomerID", primary_key=True
    )

class CustomUser(AbstractUser):
    customerid = models.ForeignKey(
        Tblcustomer, models.PROTECT,
        db_column="CustomerID",
        verbose_name="Customer",
        null=True,
        blank=True
    )


class UserProfile(models.Model):
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    table_settings = models.JSONField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def set_preference(self, table_name, key, value):
        """
        Update a single preference for a specific table.
        Example: set_table_preference("orders", "visible_columns",["id", "status"])
        table_settings will look like {"orders":{"visible_columns":['id','status']}}
        """
        settings = self.table_settings.get(table_name, {})
        settings[key] = value
        self.table_settings[table_name] = settings
        self.save(update_fields=['table_settings', 'updated_at'])

    def get_preference(self, table_name, key, default=None):
        return self.table_settings.get(table_name, {}).get(key, default)



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
    serialnumber = models.CharField(
        db_column="SerialNumber",
        max_length=255,
        blank=True,
        null=True,
        verbose_name="SN",
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
    htmx_picker = HtmxPicker(
        enabled=True,
        search_terms=(
            'assetid__icontains',
            'serialnumber__icontains',
        ),
        customer_scope='customerid',
    )

class JobView(models.Model):
    jobid = models.BigAutoField(
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

    def get_absolute_url(self):
        return reverse('job', kwargs={'pk': self.pk})

