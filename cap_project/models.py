from django.db import transaction, IntegrityError, models
import random


class CapitalProjectStatus(models.Model):
    id = models.AutoField(primary_key=True, editable=False)
    name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    inactive = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'capital_project_status'

    def __str__(self):
        return self.name

class CapitalProjectType(models.Model):
    id = models.AutoField(primary_key=True, editable=False)
    name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    inactive = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'capital_project_type'

    def __str__(self):
        return self.name

def generate_internal_code(length=6):
    return "".join(str(random.randint(0,9)) for _ in range(length))

class CapitalProject(models.Model):
    id = models.BigIntegerField(primary_key=True, editable=False)
    code = models.CharField(max_length=50, unique=True, blank=True, null=True, editable=False)
    name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    typeid = models.ForeignKey('CapitalProjectType', models.DO_NOTHING, blank=True, null=True)
    statusid = models.ForeignKey('CapitalProjectStatus', models.DO_NOTHING, blank=True, null=True)
    responsibleid = models.ForeignKey('users.CustomUser', models.DO_NOTHING, blank=True, null=True)
    creationdate = models.DateTimeField(blank=True, null=True, auto_now_add=True, editable=False)
    modificationdate = models.DateTimeField(blank=True, null=True, auto_now=True, editable=False)
    inactive = models.BooleanField(blank=True, null=True)
    startdate = models.DateTimeField(blank=True, null=True)
    enddate = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'capital_project'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        creating = self.pk in None

        if creating and not self.code:
            while True:
                self.code = generate_internal_code()
                try:
                    with transaction.atomic():
                        return super().save(*args, **kwargs)
                except IntegrityError:
                    self.internal_code = None

class CapitalAcquisitionStatus(models.Model):
    id = models.AutoField(primary_key=True, editable=False)
    name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    inactive = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'capital_acquisition_status'

    def __str__(self):
        return self.name

class CapitalAcquisition(models.Model):
    id = models.AutoField(primary_key=True, editable=False)
    capitalproject = models.ForeignKey(CapitalProject, models.DO_NOTHING, related_name='actuisition')
    code = models.CharField(max_length=50, blank=True, null=True, editable=False)
    name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    status = models.ForeignKey('CapitalAcquisitionStatus', models.PROTECT, blank=True, null=True)
    statusdate = models.DateTimeField(db_column='StatusDate', blank=True, null=True, editable=False)
    locationid = models.ForeignKey('assets.Tbllocations', models.DO_NOTHING, blank=True, null=True)
    responsible = models.ForeignKey('users.CustomUser', models.PROTECT, blank=True, null=True)
    usercontact = models.ForeignKey('users.CustomUser', models.PROTECT, related_name='usercontactid', blank=True, null=True)
    techcontact = models.ForeignKey('users.CustomUser', models.PROTECT, related_name='techcontactid', blank=True, null=True)  # Field name made lowercase.
    targetdate = models.DateTimeField(blank=True, null=True)

    quantity = models.IntegerField(blank=True, null=True)
    approvedquantity = models.IntegerField(blank=True, null=True)

    orderno = models.CharField(db_column='OrderNo', max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'capital_acquisition'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        creating = self.pk in None

        if creating and not self.code:
            while True:
                self.code = generate_internal_code()
                try:
                    with transaction.atomic():
                        return super().save(*args, **kwargs)
                except IntegrityError:
                    self.internal_code = None

class CommissionRequestStatus(models.Model):
    id = models.AutoField(primary_key=True, editable=False)
    name = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'commission_request_status'

    def __str__(self):
        return self.name

class Commissionrequest(models.Model):
    id = models.AutoField(primary_key=True, editable=False)
    code = models.CharField(max_length=50, blank=True, null=True, editable=False)
    capital_acquisition = models.ForeignKey(CapitalAcquisition, models.DO_NOTHING, related_name='commission_request')
    notes = models.TextField(db_column='CommissionRequestNotes', blank=True, null=True)
    creationdate = models.DateTimeField(db_column='CreationDate', blank=True, null=True)

    status = models.ForeignKey('CommissionRequestStatus', models.DO_NOTHING, blank=True, null=True)
    configuration = models.TextField(db_column='SoftwareVersion', blank=True, null=True)
    isnew = models.BooleanField(db_column='IsNew', blank=True, null=True)
    orderno = models.CharField(max_length=50, blank=True, null=True)
    quantity = models.IntegerField(blank=True, null=True)
    unitprice = models.DecimalField(max_digits=19, decimal_places=4, blank=True, null=True)
    unitpricevat = models.FloatField(blank=True, null=True)
    warrantymonths = models.IntegerField(blank=True, null=True)
    inactive = models.BooleanField(blank=True, null=True)
    purchasedate = models.DateTimeField(blank=True, null=True)
    installationdate = models.DateTimeField(blank=True, null=True)
    customerid = models.ForeignKey('assets.TblCustomer', models.PROTECT, blank=True, null=True)
    orderdate = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'commission_request'

    def save(self, *args, **kwargs):
        creating = self.pk in None

        if creating and not self.code:
            while True:
                self.code = generate_internal_code()
                try:
                    with transaction.atomic():
                        return super().save(*args, **kwargs)
                except IntegrityError:
                    self.internal_code = None


    def __str__(self):
        return self.name

class CapitalProjectEquipment(models.Model):
    """
        Model linking assets to capital projects
    """
    id = models.AutoField(primary_key=True, editable=False)
    capital_acquisition = models.ForeignKey(CapitalAcquisition, models.DO_NOTHING, blank=True, null=True)
    equipment = models.ForeignKey('assets.TblAssets', models.PROTECT)

    class Meta:
        managed = False
        db_table = 'capital_project_equipment'

    def __str__(self):
        return f"{self.capital_acquisition} - {self.equipment}"
