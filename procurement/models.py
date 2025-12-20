from django.db import models
from parts.models import Tblpartsprice
from django.utils.timezone import now


# Create your models here.
class TblExpenseStatus(models.Model):
    status_id = models.BigIntegerField(primary_key=True)
    status_name = models.CharField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_expense_status'

    def __str__(self):
        return f"{self.status_name}"

class TblExpenses(models.Model):
    expense_id = models.BigAutoField(primary_key=True)
    date = models.DateField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    amount = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    status = models.ForeignKey(TblExpenseStatus, models.PROTECT, db_column='status', blank=True, null=True)
    payment_to = models.BigIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_expenses'
    
    def __str__(self):
        return f"{self.expense_id} - {self.payment_to}"


class TblInvoiceStatus(models.Model):
    invoice_status_id = models.BigIntegerField(primary_key=True)
    invoice_status_name = models.CharField()
    invoice_status_description = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_invoice_status'
    def __str__(self):
        return f"{self.invoice_status_name}"

class TblInvoices(models.Model):
    invoice_id = models.BigAutoField(primary_key=True)
    invoice_no = models.CharField()
    invoice_date = models.DateField()
    po = models.ForeignKey('TblPurchaseOrder', models.PROTECT, blank=True, null=True)
    invoice_due_date = models.DateField(blank=True, null=True)
    invoice_status = models.ForeignKey(TblInvoiceStatus, models.PROTECT)
    fully_paid_date = models.DateField(blank=True, null=True)
    invoice_amount = models.DecimalField(max_digits=12, decimal_places=4)
    creation_date = models.DateField(blank=True, null=True,default=now)

    class Meta:
        managed = False
        db_table = 'tbl_invoices'
        unique_together = (('invoice_no', 'po'),)
        permissions = [
            ("bulk_update_tblinvoices", "Can perform bulk updates"),
        ]
        ordering = ('-invoice_date',)
    def __str__(self):
        return f"{self.invoice_no}-{self.invoice_date}"


class TblOrderStatus(models.Model):
    order_status_id = models.BigIntegerField(primary_key=True)
    order_status_name = models.TextField()

    class Meta:
        managed = False
        db_table = 'tbl_order_status'
    def __str__(self):
        return f"{self.order_status_name}"


class TblOrderUnit(models.Model):
    order_unit_id = models.BigIntegerField(primary_key=True)
    order_unit_name = models.CharField()

    class Meta:
        managed = False
        db_table = 'tbl_order_unit'
    
    def __str__(self):
        return f"{self.order_unit_name}"

class TblPoLines(models.Model):
    line_id = models.BigAutoField(primary_key=True)
    po = models.ForeignKey('TblPurchaseOrder', models.PROTECT,db_column='po_id')
    item = models.ForeignKey('parts.Tblpartslist', models.PROTECT,db_column='item_id', blank=True, null=True)
    unit_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    qty_ordered = models.BigIntegerField(default=1)
    line_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    qty_delivered = models.BigIntegerField(blank=True, null=True)
    line_status_id = models.BigIntegerField(blank=True, null=True)
    vat = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    line_price_incl_vat = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    vat_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    line_description = models.TextField(blank=True, null=True)
    order_unit_id = models.ForeignKey(TblOrderUnit,models.PROTECT,db_column='order_unit_id', blank=True, default=0)
    order_unit_quantity = models.IntegerField(blank=True, default=1)


    class Meta:
        managed = False
        db_table = 'tbl_po_lines'
    def __str__(self):
        return f"PO: {self.po} - Item:{self.item}"


class TblPurchaseOrder(models.Model):
    po_id = models.BigAutoField(primary_key=True)
    supplier = models.ForeignKey('TblSuppliers', models.PROTECT,)
    date_raised = models.DateField()
    ship_to_add = models.ForeignKey('TblDeliveryAddresses', models.PROTECT, blank=True, null=True)
    sub_total = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    po_total = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    order_status = models.ForeignKey(TblOrderStatus, models.PROTECT, blank=True, null=True)
    vat_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_purchase_order'
        ordering = ['-po_id']
    def __str__(self):
        return f"{self.po_id}"

class PoView(models.Model):
    po_id = models.BigIntegerField(primary_key=True)
    supplier_id = models.ForeignKey('TblSuppliers', models.PROTECT, blank=True, null=True,db_column='supplier_id')
    date_raised = models.DateField(blank=True, null=True)
    ship_to_add_id = models.ForeignKey('TblDeliveryAddresses', models.PROTECT, blank=True, null=True,db_column='ship_to_add_id')
    sub_total = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    po_total = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    order_status_id = models.BigIntegerField(blank=True, null=True)
    vat_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    line_id = models.BigIntegerField(blank=True, null=True)
    item_id = models.BigIntegerField(blank=True, null=True)
    unit_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    qty_ordered = models.BigIntegerField(default=1)
    line_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    line_status_id = models.BigIntegerField(blank=True, null=True)
    line_description = models.TextField(blank=True, null=True)
    contact = models.CharField(max_length=100, blank=True, null=True)
    first_line = models.TextField(blank=True, null=True)
    postcode = models.CharField(blank=True, null=True)
    supplier_name = models.TextField(blank=True, null=True)
    addr_first_line = models.TextField(blank=True, null=True)
    addr_postcode = models.TextField(blank=True, null=True)
    partnumber = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'po_view'
    def __str__(self):
        return f"{self.po_id}"
    
class TblSuppliers(models.Model):
    supplier_id = models.BigAutoField(primary_key=True)
    supplier_name = models.TextField(unique=True)
    addr_first_line = models.TextField()
    addr_second_line = models.TextField(blank=True, null=True)
    addr_postcode = models.TextField()
    email_address = models.TextField()
    vat_registration_number = models.CharField(blank=True, null=True)
    company_registration_number = models.CharField(blank=True, null=True)
    phone_number = models.CharField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_suppliers'

    def __str__(self):
        return f"{self.supplier_name}"
    
class TblDeliveries(models.Model):
    delivery_id = models.BigAutoField(primary_key=True)
    po = models.ForeignKey('TblPurchaseOrder', models.PROTECT, db_column='po_id')
    delivery_date = models.DateField()
    delivery_note_number = models.CharField(unique=True, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_deliveries'
    def __str__(self):
        return f"{self.delivery_id}-{self.delivery_note_number} ({self.delivery_date})"

class TblDeliveryAddresses(models.Model):
    addr_id = models.BigIntegerField(primary_key=True)
    first_line = models.TextField(blank=True, null=True)
    postcode = models.CharField(blank=True, null=True)
    address_alias = models.CharField(blank=True, null=True)
    contact = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_delivery_addresses'
    def __str__(self):
        return f"{self.address_alias}"

class TblDeliveryLines(models.Model):
    line_id = models.BigAutoField(primary_key=True)
    delivery = models.ForeignKey('TblDeliveries', models.PROTECT,db_column='delivery_id')
    item = models.ForeignKey('parts.Tblpartslist', models.PROTECT,db_column='item_id',)
    qty = models.PositiveIntegerField(blank=True, null=True,)
    line_description = models.CharField(blank=True, null=True, default=None)

    class Meta:
        managed = False
        db_table = 'tbl_delivery_lines'
    def __str__(self):
        return f"{self.delivery}"


class Deliverylineview(models.Model):
    delivery_id = models.BigIntegerField(blank=True, null=True)
    po_id = models.BigIntegerField(blank=True, null=True)
    delivery_date = models.DateField(blank=True, null=True)
    delivery_note_number = models.CharField(blank=True, null=True)
    item = models.ForeignKey('parts.Tblpartslist', models.PROTECT,db_column='item_id', blank=True, null=True)
    qty = models.BigIntegerField(blank=True, null=True)
    part_number = models.CharField(db_column='part number', max_length=100, blank=True, null=True)  # Field renamed to remove unsuitable characters.
    short_name = models.CharField(db_column='Short Name', max_length=100, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    line_id = models.BigIntegerField(primary_key=True)


    class Meta:
        managed = False
        db_table = 'deliverylineview'




class Outstandngdeliveriesview(models.Model):
    outstanding_id = models.BigIntegerField(primary_key=True)  
    po_id = models.BigIntegerField(blank=True, null=True)
    item = models.ForeignKey('parts.Tblpartslist', models.PROTECT,db_column='item_id', blank=True, null=True)
    qty_ordered = models.IntegerField(blank=True, null=True)
    qty_delivered = models.DecimalField(max_digits=10, decimal_places=5, blank=True, null=True)  # max_digits and decimal_places have been guessed, as this database handles decimal fields as float
    line_description = models.TextField(blank=True, null=True)
    part_number = models.CharField(max_length=100, blank=True, null=True)
    outstanding = models.IntegerField(blank=True, null=True)
    unit_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    line_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'outstandngDeliveriesView'



