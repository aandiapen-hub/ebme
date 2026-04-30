from django.db import models
import datetime

# Create your models here.
class Tblpartslist(models.Model):
    partid = models.BigAutoField(db_column='partID', primary_key=True)  # Field name made lowercase.
    description = models.CharField(max_length=100, blank=True, null=True)
    part_number = models.CharField(db_column='part number', max_length=100,)  # Field renamed to remove unsuitable characters.
    short_name = models.CharField(db_column='Short Name', max_length=100,)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    supplier_id = models.ForeignKey('procurement.TblSuppliers', models.PROTECT, blank=True, null=True,db_column='supplier_id')
    inactive = models.BooleanField(default=False)
    gtin = models.CharField(db_column='gtin', max_length=100,null=True,blank=True) 
    order_unit = models.ForeignKey('procurement.TblOrderUnit',models.PROTECT,blank=True, default=0)
    order_unit_quantity = models.IntegerField(blank=True, default=1)

    class Meta:
        managed = False  
        db_table = 'tblPartsList'
        ordering = ['partid']
    def __str__(self):
        return f"{self.short_name} - {self.part_number}"


class SparepartView(models.Model):
    partid = models.BigIntegerField(db_column='partID', primary_key=True)  # Field name made lowercase.
    description = models.CharField(max_length=100, blank=True, null=True)
    part_number = models.CharField(max_length=100, blank=True, null=True)
    short_name = models.CharField(max_length=100, blank=True, null=True)
    supplier_id = models.BigIntegerField(blank=True, null=True)
    inactive = models.BooleanField(blank=True, null=True)
    supplier_name = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sparepart_view'
        ordering = ['partid']

    def __str__(self):
        return f"{self.short_name} - {self.part_number}"
    
    
class Tblpartsprice(models.Model):
    priceid = models.BigAutoField(db_column='priceID', primary_key=True)  # Field name made lowercase.
    partid = models.ForeignKey(Tblpartslist, models.PROTECT, db_column='partID')  # Field name made lowercase.
    price = models.DecimalField(max_digits=100, decimal_places=2, blank=True, null=True)
    effectivedate = models.DateField(db_column='EffectiveDate', default=datetime.date.today)  # Field name made lowercase.

    class Meta:
        managed = False  
        db_table = 'tblPartsPrice'
        



class TblPartModel(models.Model):
    part_model_id = models.BigAutoField(primary_key=True)
    model = models.ForeignKey('assets.Tblmodel', models.PROTECT,db_column='model_id')
    part = models.ForeignKey(Tblpartslist, models.DO_NOTHING, db_column='part_id')

    class Meta:
        managed = False  
        db_table = 'tbl_part_model'
    
    def __str__(self):
        return "{self.part} - {self.model}"