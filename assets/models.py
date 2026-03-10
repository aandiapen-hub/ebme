# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False  ` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from django.utils.timezone import now
from django.urls import reverse

from django.core.validators import MinValueValidator


class Tblassets(models.Model):
    assetid = models.BigAutoField(
        db_column="AssetID", primary_key=True
    )  # Field name made lowercase.
    customerassetnumber = models.CharField(
        db_column="CustomerAssetNumber", max_length=255, blank=True, null=True
    )  # Field name made lowercase.
    customerid = models.ForeignKey(
        "Tblcustomer", models.PROTECT, db_column="CustomerID"
    )  # Field name made lowercase.
    modelid = models.ForeignKey(
        "Tblmodel", models.PROTECT, db_column="ModelID"
    )  # Field name made lowercase.
    serialnumber = models.CharField(
        db_column="SerialNumber", max_length=255
    )  # Field name made lowercase.
    lastppmdate = models.DateField(blank=True, null=True)
    lastrepairdate = models.DateField(blank=True, null=True)
    lastjobdate = models.DateField(blank=True, null=True)
    creationdate = models.DateField(default=now, blank=True)
    contractid = models.ForeignKey(
        "TblmaintContracts",
        models.PROTECT,
        db_column="contractid",
        blank=True,
        null=True,
    )
    installationdate = models.DateField(default=now, blank=True)
    unitprice = models.DecimalField(
        max_digits=12, decimal_places=4, blank=True, null=True
    )
    ordernumber = models.CharField(blank=True, null=True)
    ordervalue = models.DecimalField(
        max_digits=12, decimal_places=4, blank=True, null=True
    )
    nextppmdate = models.DateField(blank=True, null=True)
    ppmscheduleid = models.ForeignKey(
        "Tblppmschedules",
        models.PROTECT,
        db_column="ppmscheduleid",
        default=1,
        blank=True,
        null=True,
    )
    softwareversion = models.CharField(blank=True, null=True)
    locationid = models.ForeignKey(
        "Tbllocations", models.PROTECT, db_column="locationid", blank=True, null=True
    )
    asset_status_id = models.ForeignKey(
        "TblAssetStatus",
        models.PROTECT,
        blank=True,
        db_column="asset_status_id",
        default=1,
    )
    support_level = models.ForeignKey(
        "TblSupportLevel", models.PROTECT, blank=True, null=True
    )
    prod_date = models.DateField(blank=True, null=True)
    is_test_eq = models.BooleanField(blank=True, null=True, default=False)
    next_calibration_date = models.DateField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "tblAssets"
        unique_together = (("serialnumber", "modelid"),)
        permissions = [
            ("bulk_change_assets", "Can perform bulk updates"),
        ]

    def __str__(self):
        return f"{self.assetid}"

    def get_absolute_url(self):
        return reverse("assets:view_asset", kwargs={"pk": self.pk})


class AssetView(models.Model):
    assetid = models.BigIntegerField(
        db_column="AssetID", blank=True, primary_key=True, verbose_name="Asset ID"
    )  # Field name made lowercase.
    customerassetnumber = models.CharField(
        db_column="CustomerAssetNumber",
        max_length=255,
        blank=True,
        null=True,
        verbose_name="CustomerAsset",
    )  # Field name made lowercase.
    customerid = models.ForeignKey(
        "Tblcustomer", models.PROTECT, db_column="CustomerID", verbose_name="Customer"
    )  # Field name made lowercase.
    modelid = models.ForeignKey(
        "Tblmodel", models.PROTECT, db_column="ModelID", verbose_name="Model"
    )  # Field name made lowercase.
    serialnumber = models.CharField(
        db_column="SerialNumber",
        max_length=255,
        blank=True,
        null=True,
        verbose_name="SN",
    )  # Field name made lowercase.
    lastppmdate = models.DateField(blank=True, null=True, verbose_name="Last PPM Date")
    lastrepairdate = models.DateField(
        blank=True, null=True, verbose_name="Last Repair Date"
    )
    lastjobdate = models.DateField(blank=True, null=True, verbose_name="Last Job Date")
    creationdate = models.DateField(blank=True, null=True, verbose_name="Creation Date")
    contractid = models.BigIntegerField(blank=True, null=True)
    installationdate = models.DateField(
        blank=True, null=True, verbose_name="Installation Date"
    )
    unitprice = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        blank=True,
        null=True,
        verbose_name="Unit Price",
    )
    ordernumber = models.CharField(blank=True, null=True, verbose_name="OrderNumber")
    ordervalue = models.DecimalField(
        max_digits=12, decimal_places=4, blank=True, null=True
    )
    nextppmdate = models.DateField(blank=True, null=True, verbose_name="Next PPM Date")
    ppmscheduleid = models.ForeignKey(
        "Tblppmschedules",
        models.PROTECT,
        db_column="ppmscheduleid",
        default=1,
        null=True,
        verbose_name="PPMSchedule",
    )
    softwareversion = models.CharField(blank=True, null=True, verbose_name="Software")
    locationid = models.ForeignKey(
        "Tbllocations",
        models.PROTECT,
        db_column="locationid",
        blank=True,
        null=True,
        verbose_name="Location",
    )
    asset_status_id = models.ForeignKey(
        "TblAssetStatus",
        models.PROTECT,
        db_column="asset_status_id",
        blank=True,
        null=True,
        verbose_name="Asset Status",
    )
    support_level_id = models.BigIntegerField(
        blank=True, null=True, verbose_name="Support Level"
    )
    customername = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="CustomerName"
    )
    modelname = models.CharField(
        db_column="ModelName",
        max_length=100,
        blank=True,
        null=True,
        verbose_name="ModelName",
    )  # Field name made lowercase.
    brandname = models.CharField(
        db_column="BrandName", blank=True, null=True, verbose_name="Brand Name"
    )  # Field name made lowercase.
    brandid = models.ForeignKey(
        "Tblbrands",
        models.PROTECT,
        db_column="BrandID",
        blank=True,
        null=True,
        verbose_name="Brand",
    )  # Field name made lowercase.
    categoryid = models.ForeignKey(
        "Tblcategories",
        models.PROTECT,
        db_column="categoryid",
        blank=True,
        null=True,
        verbose_name="Category",
    )
    locationname = models.CharField(blank=True, null=True, verbose_name="LocationName")
    sitename = models.CharField(blank=True, null=True, verbose_name="SiteName")
    categoryname = models.CharField(blank=True, null=True, verbose_name="CategoryName")
    schedulename = models.CharField(blank=True, null=True)
    status_name = models.CharField(blank=True, null=True, verbose_name="StatusName")
    support_level_name = models.CharField(blank=True, null=True)
    ppm_compliance = models.TextField(
        blank=True, null=True, verbose_name="PPM_Compliance"
    )

    class Meta:
        managed = False
        db_table = "asset_view"

        ordering = ("assetid",)

    def __str__(self):
        return f"{self.brandname} - {self.modelname} - {self.serialnumber} ({self.categoryname})"

    def get_absolute_url(self):
        return reverse("assets:view_asset", kwargs={"pk": self.pk})


class JobView(models.Model):
    jobid = models.BigIntegerField(
        db_column="JobID", primary_key=True, verbose_name="Job"
    )
    startdate = models.DateField(blank=True, null=True, verbose_name="Start Date")
    enddate = models.DateField(blank=True, null=True, verbose_name="End Date")
    workdone = models.TextField(
        db_column="WorkDone", blank=True, null=True, verbose_name="Work Done"
    )  # Field name made lowercase.
    jobstatusid = models.ForeignKey(
        "Tbljobstatus",
        models.PROTECT,
        db_column="JobStatusID",
        blank=True,
        null=True,
        verbose_name="Job Status",
    )  # Field name made lowercase.
    technicianid = models.ForeignKey(
        "Tbltechnicianlist",
        models.PROTECT,
        db_column="TechnicianID",
        blank=True,
        null=True,
        verbose_name="Technician",
    )  # Field name made lowercase.
    assetid = models.ForeignKey(
        AssetView, models.PROTECT, db_column="AssetID", related_name="jobs"
    )  # Field name made lowercase.
    technician_name = models.CharField(
        db_column="Technician Name",
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Technician",
    )  # Field name made lowercase. Field renamed to remove unsuitable characters.
    partsperjob = models.TextField(
        db_column="PartsPerJob", blank=True, null=True, verbose_name="Parts Used"
    )  # Field name made lowercase.
    testsperjob = models.TextField(
        db_column="TestsPerJob", blank=True, null=True, verbose_name="Checklist"
    )  # Field name made lowercase.
    modelid = models.ForeignKey(
        "Tblmodel", models.PROTECT, db_column="ModelID", verbose_name="Model"
    )  # Field name made lowercase.
    serialnumber = models.CharField(
        db_column="SerialNumber",
        max_length=255,
        blank=True,
        null=True,
        verbose_name="SN",
    )  # Field name made lowercase.
    customerid = models.ForeignKey(
        "Tblcustomer",
        models.PROTECT,
        db_column="CustomerID",
        blank=True,
        null=True,
        verbose_name="Customer",
    )  # Field name made lowercase.
    model = models.CharField(
        db_column="Model", max_length=100, blank=True, null=True
    )  # Field name made lowercase.
    customer = models.CharField(
        db_column="Customer", max_length=100, blank=True, null=True
    )  # Field name made lowercase.
    jobstatus = models.CharField(
        db_column="JobStatus",
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Status",
    )  # Field name made lowercase.
    jobtypename = models.CharField(
        max_length=50, blank=True, null=True, verbose_name="Job Type Name"
    )
    total_cost = models.DecimalField(
        db_column="Total Cost",
        max_digits=100,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Cost of parts",
    )
    customerasset = models.CharField(
        db_column="CustomerAsset",
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Cust Asset No",
    )  # Field name made lowercase.
    customer_address = models.CharField(
        db_column="Customer Address",
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Customer Addr",
    )  # Field name made lowercase. Field renamed to remove unsuitable characters.
    customer_phone = models.CharField(
        db_column="Customer Phone",
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Customer Phone",
    )  # Field name made lowercase. Field renamed to remove unsuitable characters.
    brandname = models.CharField(
        db_column="BrandName", blank=True, null=True, verbose_name="Brand"
    )  # Field name made lowercase.
    customer_postcode = models.CharField(
        db_column="Customer Postcode",
        blank=True,
        null=True,
        verbose_name="Customer Postcode",
    )  # Field name made lowercase. Field renamed to remove unsuitable characters.
    brandid = models.ForeignKey(
        "Tblbrands",
        models.PROTECT,
        db_column="BrandID",
        blank=True,
        null=True,
        verbose_name="Brand",
    )  # Field name made lowercase.
    jobtypeid = models.ForeignKey(
        "Tbljobtypes", models.PROTECT, db_column="jobtypeid", verbose_name="Job Type"
    )

    class Meta:
        managed = False
        db_table = "jobSummary"
        ordering = ("jobid",)

    def __str__(self):
        return f"{self.jobid} - {self.model} - {self.serialnumber} - {self.jobstatus} - {self.customer} "

    def get_absolute_url(self):
        return reverse("jobs:job_summary", kwargs={"pk": self.pk})


class Tblbrands(models.Model):
    brandid = models.BigAutoField(
        db_column="BrandID", primary_key=True, verbose_name="ID"
    )  # Field name made lowercase.
    brandname = models.CharField(
        db_column="BrandName", unique=True, verbose_name="Brand"
    )  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = "tblBrands"
        ordering = ["brandid"]

    def __str__(self):
        return f"{self.brandname}"


class Tblcheckslists(models.Model):
    testname = models.CharField(
        db_column="Test", max_length=100, verbose_name="Test"
    )  # Field name made lowercase.
    testid = models.BigAutoField(
        db_column="testID", primary_key=True, verbose_name="ID"
    )  # Field name made lowercase.
    test_description = models.TextField(
        db_column="Test Description", verbose_name="Description"
    )  # Field name made lowercase. Field renamed to remove unsuitable characters.
    modelid = models.ForeignKey(
        "tblModel",
        models.PROTECT,
        db_column="ModelID",
    )  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = "tblChecksLists"
        ordering = ["testid"]

    def __str__(self):
        return f"{self.testname}"


class Tblcustomer(models.Model):
    customer_name = models.CharField(
        db_column="Customer Name", unique=True, max_length=100, verbose_name="Customer"
    )  # Field name made lowercase. Field renamed to remove unsuitable characters.
    customer_address = models.CharField(
        db_column="Customer Address",
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Address",
    )  # Field name made lowercase. Field renamed to remove unsuitable characters.
    customer_phone = models.CharField(
        db_column="Customer Phone",
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Phone",
    )  # Field name made lowercase. Field renamed to remove unsuitable characters.
    customerid = models.BigAutoField(
        db_column="CustomerID", primary_key=True
    )  # Field name made lowercase.
    customer_postcode = models.CharField(
        db_column="Customer Postcode", blank=True, null=True, verbose_name="Postcode"
    )  # Field name made lowercase. Field renamed to remove unsuitable characters.

    class Meta:
        managed = False
        db_table = "tblCustomer"
        ordering = ["customerid"]

    def __str__(self):
        return self.customer_name


class Tbljob(models.Model):
    jobid = models.BigAutoField(
        db_column="JobID", primary_key=True
    )  # Field name made lowercase.
    jobstartdate = models.DateField(
        db_column="JobStartDate", blank=True, null=True
    )  # Field name made lowercase.
    jobenddate = models.DateField(
        db_column="JobEndDate", blank=True, null=True
    )  # Field name made lowercase.
    comments = models.CharField(
        db_column="Comments", blank=True, null=True
    )  # Field name made lowercase.
    workdone = models.TextField(
        db_column="WorkDone", blank=True, null=True
    )  # Field name made lowercase.
    jobstatusid = models.ForeignKey(
        "Tbljobstatus", models.PROTECT, db_column="JobStatusID"
    )  # Field name made lowercase.
    technicianid = models.ForeignKey(
        "Tbltechnicianlist", models.PROTECT, db_column="TechnicianID"
    )  # Field name made lowercase.
    assetid = models.ForeignKey(
        Tblassets, models.PROTECT, db_column="AssetID"
    )  # Field name made lowercase.
    jobtypeid = models.ForeignKey("Tbljobtypes", models.PROTECT, db_column="jobtypeid")
    creationdate = models.DateField(blank=True, null=True, default=now)

    class Meta:
        managed = False
        db_table = "tblJob"
        ordering = ("jobid",)
        permissions = [
            ("bulk_update_tbljob", "Can perform bulk updates"),
            ("genreport_tbljob", "Can download job reports"),
        ]

    def __str__(self):
        return str(self.jobid)

    def get_absolute_url(self):
        return reverse("jobs:job_summary", kwargs={"pk": self.pk})


class Tbljobstatus(models.Model):
    jobstatusname = models.CharField(
        db_column="JobStatus",
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Job `Status",
    )  # Field name made lowercase.
    jobstatusid = models.BigIntegerField(
        db_column="JobStatusID", primary_key=True
    )  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = "tblJobStatus"

    def __str__(self):
        return self.jobstatusname


class Tbljobtypes(models.Model):
    jobtypeid = models.BigIntegerField(
        primary_key=True,
    )
    jobtypename = models.CharField(max_length=50, verbose_name="Job Type")

    class Meta:
        managed = False
        db_table = "tblJobTypes"

    def __str__(self):
        return self.jobtypename


class Tblmodel(models.Model):
    modelname = models.CharField(
        db_column="ModelName", max_length=100, verbose_name="Model"
    )  # Field name made lowercase.
    modelid = models.BigAutoField(
        db_column="ModelID", primary_key=True
    )  # Field name made lowercase.
    brandid = models.ForeignKey(
        "Tblbrands",
        models.PROTECT,
        db_column="BrandID",
    )  # Field name made lowercase.
    categoryid = models.ForeignKey(
        "Tblcategories",
        on_delete=models.PROTECT,
        db_column="categoryid",
    )
    gtin = models.CharField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "tblModel"
        unique_together = (("modelname", "brandid"),)
        ordering = ["modelid"]
        permissions = [
            ("bulk_update_tblmodel", "Can perform bulk updates"),
        ]

    def __str__(self):
        return f"{self.modelname}"


class Tblpartsused(models.Model):
    jobid = models.ForeignKey(
        Tbljob,
        on_delete=models.PROTECT,
        db_column="JobID",
    )  # Field name made lowercase.
    quantity = models.IntegerField(
        db_column="Quantity", default=1
    )  # Field name made lowercase.
    partsusedid = models.BigAutoField(
        db_column="PartsUsedID", primary_key=True
    )  # Field name made lowercase.
    partid = models.ForeignKey(
        "parts.Tblpartslist",
        models.PROTECT,
        db_column="PartID",
    )  # Field name made lowercase.
    unitprice = models.DecimalField(
        max_digits=100, decimal_places=2, blank=True, null=True
    )
    price = models.DecimalField(max_digits=100, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "tblPartsUsed"

    def __str__(self):
        return f"Job: {self.jobid} - Part: {self.partid} - Qty: {self.quantity}"


class Tbltechnicianlist(models.Model):
    name = models.CharField(
        db_column="Name", max_length=100, blank=True, null=True
    )  # Field name made lowercase.
    technicianid = models.BigIntegerField(
        db_column="TechnicianID", primary_key=True
    )  # Field name made lowercase.
    email = models.CharField(unique=True, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "tblTechnicianList"

    def __str__(self):
        return self.name


class Tbltesteq(models.Model):
    testeqid = models.BigAutoField(
        db_column="TestEqID", primary_key=True
    )  # Field name made lowercase.
    last_calibration_date = models.DateField(
        db_column="Last Calibration Date", blank=True, null=True
    )  # Field name made lowercase. Field renamed to remove unsuitable characters.
    status = models.CharField(
        db_column="Status", max_length=100, blank=True, null=True
    )  # Field name made lowercase.
    serialnumber = models.CharField(
        db_column="SerialNumber", max_length=100
    )  # Field name made lowercase.
    comment = models.CharField(
        db_column="Comment", max_length=100, blank=True, null=True
    )  # Field name made lowercase.
    modelid = models.ForeignKey(
        Tblmodel, models.PROTECT, db_column="ModelID", blank=True, null=True
    )  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = "tblTestEq"


class Tbltesteqused(models.Model):
    id = models.BigAutoField(
        db_column="ID", primary_key=True
    )  # Field name made lowercase.
    jobid = models.ForeignKey(
        Tbljob, on_delete=models.PROTECT, db_column="JobID"
    )  # Field name made lowercase.
    test_eq = models.ForeignKey(
        Tblassets, on_delete=models.PROTECT, limit_choices_to={"is_test_eq": True}
    )

    class Meta:
        managed = False
        db_table = "tblTestEqUsed"
        unique_together = (("jobid", "test_eq"),)

    def __str__(self):
        return f"{self.test_eq}"


class Tbltestscarriedout(models.Model):
    jobid = models.ForeignKey(
        "Tbljob", on_delete=models.CASCADE, db_column="JobID"
    )  # Field name made lowercase.
    testid = models.BigAutoField(
        db_column="TestID", primary_key=True
    )  # Field name made lowercase.
    checkid = models.ForeignKey(
        "Tblcheckslists", on_delete=models.PROTECT, db_column="CheckID", blank=True
    )  # Field name made lowercase.
    resultid = models.ForeignKey(
        "Tbltestresult",
        on_delete=models.PROTECT,
        db_column="resultid",
        blank=True,
        null=True,
    )

    class Meta:
        managed = False
        db_table = "tblTestsCarriedOut"
        unique_together = (("jobid", "checkid"),)

    def __str__(self):
        return f"{self.checkid} - {self.resultid}"


class TblAssetStatus(models.Model):
    asset_status_id = models.BigAutoField(primary_key=True, verbose_name="ID")
    status_name = models.CharField(verbose_name="Asset Status")

    class Meta:
        managed = False
        db_table = "tbl_asset_status"

    def __str__(self):
        return self.status_name


class TblMaintenanceSupplier(models.Model):
    supplier_id = models.BigAutoField(primary_key=True)
    maint_supplier_name = models.CharField(unique=True)
    maint_supplier_contact = models.CharField(blank=True, null=True)
    maint_supplier_email = models.CharField(blank=True, null=True)
    maint_supplier_phone = models.CharField(blank=True, null=True)
    main_supplier_notes = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "tbl_maintenance_supplier"


class TblSupportLevel(models.Model):
    support_level_id = models.BigAutoField(primary_key=True)
    support_level_name = models.CharField(unique=True)
    support_level_description = models.CharField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "tbl_support_level"

    def __str__(self):
        return self.support_level_name


class Tblassetscontracts(models.Model):
    assetcontractid = models.BigAutoField(primary_key=True)
    assetid = models.ForeignKey(Tblassets, models.PROTECT, db_column="assetid")
    main_contractid = models.ForeignKey(
        "TblmaintContracts", models.PROTECT, db_column="main_contractid"
    )
    creationdate = models.DateField()

    class Meta:
        managed = False
        db_table = "tblassetscontracts"
        unique_together = (("assetid", "main_contractid"),)


class Tblcategories(models.Model):
    categoryid = models.BigAutoField(primary_key=True, verbose_name="ID")
    categoryname = models.CharField(verbose_name="Category")
    categorydescription = models.TextField(
        blank=True, null=True, verbose_name="Description"
    )
    gmdnname = models.CharField(blank=True, null=True)
    gmdncode = models.CharField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "tblcategories"
        ordering = ["categoryid"]

    def __str__(self):
        return self.categoryname


class Tblcontractstatus(models.Model):
    contractstatusid = models.BigAutoField(primary_key=True)
    statusname = models.CharField()

    class Meta:
        managed = False
        db_table = "tblcontractstatus"


class Tblcontracttype(models.Model):
    contracttypeid = models.BigAutoField(primary_key=True)
    contracttypename = models.CharField()

    class Meta:
        managed = False
        db_table = "tblcontracttype"


class Tblest(models.Model):
    class Meta:
        managed = False
        db_table = "tblest"


class Tbllocations(models.Model):
    locationid = models.BigAutoField(primary_key=True)
    locationname = models.CharField()
    departmentname = models.CharField(blank=True, null=True)
    siteid = models.ForeignKey("Tblsites", models.PROTECT, db_column="siteid")
    customerid = models.ForeignKey(Tblcustomer, models.PROTECT, db_column="customerid")

    class Meta:
        managed = False
        db_table = "tbllocations"

    def __str__(self):
        return self.locationname


class TblmaintContracts(models.Model):
    contractid = models.BigAutoField(primary_key=True)
    contractname = models.CharField()
    contracttypeid = models.ForeignKey(
        Tblcontracttype,
        models.PROTECT,
        db_column="contracttypeid",
        blank=True,
        null=True,
    )
    purchaseorder = models.CharField(blank=True, null=True)
    startdate = models.DateField(blank=True, null=True)
    enddate = models.DateField(blank=True, null=True)
    supplierid = models.ForeignKey(
        TblMaintenanceSupplier, models.PROTECT, db_column="supplierid"
    )
    contractstatusid = models.ForeignKey(
        Tblcontractstatus, models.PROTECT, db_column="contractstatusid"
    )
    contract_value = models.DecimalField(
        max_digits=12, decimal_places=4, blank=True, null=True
    )
    customer = models.ForeignKey(Tblcustomer, models.PROTECT, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "tblmaint_contracts"


class Tblppmschedules(models.Model):
    scheduleid = models.BigAutoField(primary_key=True)
    schedulename = models.CharField(blank=True, verbose_name="PPM Schedule")
    schedulemetric = models.CharField(blank=True, null=True)
    schedulefrequency = models.IntegerField()

    class Meta:
        managed = False
        db_table = "tblppmschedules"

    def __str__(self):
        return self.schedulename


class Tblsites(models.Model):
    siteid = models.BigAutoField(primary_key=True)
    sitename = models.CharField(unique=True)

    class Meta:
        managed = False
        db_table = "tblsites"

    def __str__(self):
        return self.sitename


class Tbltestresult(models.Model):
    resultid = models.BigIntegerField(primary_key=True)
    resultname = models.CharField()

    class Meta:
        managed = False
        db_table = "tbltestresult"

    def __str__(self):
        return str(self.resultname)


class Tbltotaljobcost(models.Model):
    totalcostid = models.BigAutoField(primary_key=True)
    jobid = models.OneToOneField(
        Tbljob, models.CASCADE, db_column="jobid", blank=True, null=True
    )
    totalcost = models.DecimalField(
        max_digits=100, decimal_places=2, blank=True, null=True
    )

    class Meta:
        managed = False
        db_table = "tbltotaljobcost"
