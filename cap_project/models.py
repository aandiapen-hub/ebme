from django.db import models

class CapitalProjectStatus(models.Model):
    id = models.IntegerField(primary_key=True, max_length=50)  # Field name made lowercase.
    name = models.CharField(max_length=255, blank=True, null=True)  # Field name made lowercase.
    description = models.TextField(blank=True, null=True)  # Field name made lowercase.
    inactive = models.BooleanField(blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'capital_project_status'

class CapitalProjectType(models.Model):
    id = models.IntegerField(primary_key=True, max_length=50)  # Field name made lowercase.
    name = models.CharField(max_length=255, blank=True, null=True)  # Field name made lowercase.
    description = models.TextField(blank=True, null=True)  # Field name made lowercase.
    inactive = models.BooleanField(blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'capital_project_type'

class CapitalProject(models.Model):
    id = models.BigIntegerField(primary_key=True, max_length=50)  # Field name made lowercase.
    code = models.CharField(max_length=50, blank=True, null=True)  # Field name made lowercase.
    name = models.CharField(max_length=255, blank=True, null=True)  # Field name made lowercase.
    description = models.TextField(blank=True, null=True)  # Field name made lowercase.
    notes = models.TextField(blank=True, null=True)  # Field name made lowercase.
    typeid = models.ForeignKey('CapitalProjectType', models.DO_NOTHING, blank=True, null=True)  # Field name made lowercase.
    statusid = models.ForeignKey('CapitalProjectStatus', models.DO_NOTHING, blank=True, null=True)  # Field name made lowercase.
    responsibleid = models.ForeignKey('CustomUser', models.DO_NOTHING, blank=True, null=True)  # Field name made lowercase.
    creationdate = models.DateTimeField(blank=True, null=True)  # Field name made lowercase.
    modificationdate = models.DateTimeField(blank=True, null=True)  # Field name made lowercase.
    inactive = models.BooleanField(blank=True, null=True)  # Field name made lowercase.
    startdate = models.DateTimeField(blank=True, null=True)  # Field name made lowercase.
    enddate = models.DateTimeField(blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'capital_project'

class CapitalProjectBidStatus(models.Model):
    id = models.CharField(primary_key=True, max_length=50)  # Field name made lowercase.
    code = models.CharField(max_length=50, blank=True, null=True)  # Field name made lowercase.
    name = models.CharField(max_length=255, blank=True, null=True)  # Field name made lowercase.
    description = models.TextField(blank=True, null=True)  # Field name made lowercase.
    inactive = models.BooleanField(blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'capital_project_bid_status'

class CapitalProjectBid(models.Model):
    id = models.IntegerField(primary_key=True, max_length=50)  # Field name made lowercase.
    capitalproject = models.ForeignKey(CapitalProject, models.DO_NOTHING)  # Field name made lowercase.
    code = models.CharField(max_length=50, blank=True, null=True)  # Field name made lowercase.
    name = models.CharField(max_length=255, blank=True, null=True)  # Field name made lowercase.
    description = models.TextField(blank=True, null=True)  # Field name made lowercase.
    notes = models.TextField(blank=True, null=True)  # Field name made lowercase.
    statusid = models.ForeignKey('CapitalProjectBidStatus', models.PROTECT, blank=True, null=True)  # Field name made lowercase.
    statusdate = models.DateTimeField(db_column='StatusDate', blank=True, null=True)  # Field name made lowercase.
    locationid = models.ForeignKey('Tbllocations', models.DO_NOTHING, blank=True, null=True)  # Field name made lowercase.
    responsibleid = models.ForeignKey('Personnel', models.PROTECT, blank=True, null=True)  # Field name made lowercase.
    usercontactid = models.ForeignKey('Personnel', models.PROTECT, related_name='usercontactid', blank=True, null=True)  # Field name made lowercase.
    techcontactid = models.ForeignKey('Personnel', models.PROTECT, related_name='techcontactid', blank=True, null=True)  # Field name made lowercase.
    targetdate = models.DateTimeField(blank=True, null=True)  # Field name made lowercase.

    quantity = models.IntegerField(blank=True, null=True)  # Field name made lowercase.
    approvedquantity = models.IntegerField(blank=True, null=True)  # Field name made lowercase.

    orderno = models.CharField(db_column='OrderNo', max_length=50, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'CapitalProjectBid'

class CommissionRequestStatus(models.Model):
    id = models.IntegerField(primary_key=True, max_length=50)  # Field name made lowercase.
    name = models.CharField(max_length=255, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'commission_request_status'

class Commissionrequest(models.Model):
    id = models.IntegerField(primary_key=True, max_length=50)  # Field name made lowercase.
    code = models.CharField(max_length=50, blank=True, null=True)  # Field name made lowercase.
    capital_project_bit = models.ForeignKey(CapitalProjectBid, models.DO_NOTHING)  # Field name made lowercase.
    notes = models.TextField(db_column='CommissionRequestNotes', blank=True, null=True)  # Field name made lowercase.
    creationdate = models.DateTimeField(db_column='CreationDate', blank=True, null=True)  # Field name made lowercase.

    status = models.ForeignKey('CommissionRequestStatus', models.DO_NOTHING, blank=True, null=True)  # Field name made lowercase.
    configuration = models.TextField(db_column='SoftwareVersion', blank=True, null=True)  # Field name made lowercase.
    isnew = models.BooleanField(db_column='IsNew', blank=True, null=True)  # Field name made lowercase.
    orderno = models.CharField(max_length=50, blank=True, null=True)  # Field name made lowercase.
    quantity = models.IntegerField(blank=True, null=True)  # Field name made lowercase.
    unitprice = models.DecimalField(max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    unitpricevat = models.FloatField(blank=True, null=True)  # Field name made lowercase.
    warrantymonths = models.IntegerField(blank=True, null=True)  # Field name made lowercase.
    inactive = models.BooleanField(blank=True, null=True)  # Field name made lowercase.
    purchasedate = models.DateTimeField(blank=True, null=True)  # Field name made lowercase.
    installationdate = models.DateTimeField(blank=True, null=True)  # Field name made lowercase.
    equipmentstatus = models.ForeignKey('TblAssetStatus', models.PROTECT, blank=True, null=True)  # Field name made lowercase.
    customerid = models.ForeignKey('TblCustomer', models.PROTECT, blank=True, null=True)  # Field name made lowercase.
    orderdate = models.DateTimeField(blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'commission_request'

class CapitalProjectEquipment(models.Model):
    """
        Model linking assets to capital projects
    """
    id = models.CharField(db_column='CapitalProjectEquipmentId', max_length=50)  # Field name made lowercase.
    capital_project_bid = models.ForeignKey(CapitalProjectBid, models.DO_NOTHING, blank=True, null=True)  # Field name made lowercase.
    equipment = models.ForeignKey('TblAssets', models.PROTECT)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'CapitalProjectEquipment'

