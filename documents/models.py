import os
from django.db import models
import hashlib
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
import uuid
from django.db.models.signals import post_delete
from django.dispatch import receiver


# Create your models here.
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.db import transaction

from io import BytesIO
from django.core.files.base import ContentFile
from PIL import Image


class DocumentTypes(models.IntegerChoices):
    UNKNOWN = 0, "UNKNOWN"
    USER_MANUAL = 10, "User Manual"
    SERVICE_MANUAL = 20, "Service Manual"
    INVOICE = 30, "Invoice"
    DELIVERY_NOTE = 40, "Delivery Note"
    SERVICE_REPORT = 50, "Service Report"


class TblDocuments(models.Model):
    """
    Use create document from file service
    to create object for this model
    """

    document_id = models.BigAutoField(primary_key=True)
    document_name = models.CharField()
    document_description = models.TextField(blank=True, null=True)
    document_bytea = models.BinaryField(blank=True, null=True)
    file_size = models.BigIntegerField(blank=True, null=True)
    checksum = models.CharField(
        max_length=64, blank=True, null=True
    )  # e.g. SHA256 hex digest
    mime_type = models.CharField(max_length=100, blank=True, null=True)
    creation_date = models.DateTimeField(auto_now_add=True)
    document_type_id = models.IntegerField(
        choices=DocumentTypes.choices,
        default=DocumentTypes.UNKNOWN,
        null=True,
        blank=True,
    )
    document_hash = models.CharField(
        max_length=64, unique=True, db_index=True, null=True, blank=True
    )

    def __str__(self):
        return self.document_name

    def set_content(self, content, file_hash=None):
        self.document_bytea = content
        self.document_hash = file_hash or hashlib.sha256(content).hexdigest()
        self.file_size = len(content)

    class Meta:
        managed = False
        db_table = "tbl_aws_documents"


# temp media files folder
temp_storage = FileSystemStorage(
    location=os.path.join(settings.MEDIA_ROOT, "temp_uploads")
)


class TempUploadGroup(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,  # delete files if user is deleted
        related_name='temp_upload_group')
    document_type_id = models.IntegerField(
        choices=DocumentTypes.choices,
        default=DocumentTypes.UNKNOWN,
    )

    combined_ocr_text = models.TextField(blank=True)
    extracted_json = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'temp_upload_group'


class TemporaryUpload(models.Model):
    file = models.FileField(upload_to="", storage=temp_storage)
    group = models.ForeignKey(
        TempUploadGroup,
        on_delete=models.CASCADE,
        related_name='temp_uploads',
        db_column='group'
    )
    mime_type = models.CharField(max_length=100)
    original_name = models.CharField(max_length=100)
    page_number = models.IntegerField(null=True, blank=True)
    file_size = models.BigIntegerField()
    ocr_text = models.TextField(blank=True)
    ocr_boxes = models.JSONField(default=dict, blank=True)
    barcode_data = models.JSONField(default=dict, blank=True)
    upload_at = models.DateTimeField(auto_now_add=True)

    @classmethod
    def from_uploaded_file(cls, file, group):
        return cls.objects.create(
            file=file,
            mime_type=file.content_type,
            file_size=file.size,
            original_name=file.name,
            group=group,
        )

    def save(self, *args, **kwargs):
        update_fields = kwargs.get("update_fields")

        should_process_file = (
            not update_fields
            or "file" in update_fields
        )

        if should_process_file and self.file:
            ext = os.path.splitext(self.file.name)[1].lower()

            if ext in [".jpg", ".jpeg", ".png"]:
                self.file.open("rb")
                img = Image.open(self.file).copy()

                # Convert PNG with transparency to RGB
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")

                buffer = BytesIO()

                if ext in [".jpg", ".jpeg"]:
                    img.save(
                        buffer,
                        format="JPEG",
                        quality=70,
                        optimize=True
                    )
                elif ext == ".png":
                    img.save(
                        buffer,
                        format="PNG",
                        optimize=True
                    )

                buffer.seek(0)

                self.file.save(
                    self.file.name,
                    ContentFile(buffer.read()),
                    save=False
                )

        super().save(*args, **kwargs)

    class Meta:
        managed = False
        db_table = "tbl_temporaryupload"


@receiver(post_delete, sender=TemporaryUpload)
def delete_uploaded_file(sender, instance, **kwargs):
    if instance.file:
        instance.file.delete(save=False)
    if TemporaryUpload.objects.filter(group=instance.group.pk).count() == 0:
        TempUploadGroup.objects.get(pk=instance.group.pk).delete()

class TblDocTableRef(models.Model):
    table_id = models.BigIntegerField(primary_key=True)
    table_name = models.CharField(unique=True)

    class Meta:
        managed = False
        db_table = "tbl_doc_table_ref"

    def __str__(self):
        return f"{self.table_name}"


class TblDocumentLinks(models.Model):
    document_link_id = models.BigAutoField(primary_key=True, editable=False)
    documentid = models.ForeignKey(
        TblDocuments,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        db_column="document_id",
        related_name="links",
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
    )
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    customer = models.ForeignKey(
        "assets.Tblcustomer", on_delete=models.PROTECT, null=True, blank=True
    )

    class Meta:
        managed = False
        db_table = "tbl_document_links"
        ordering = ["document_link_id"]
        permissions = [
            ("bulk_create_links", "Can bulk create links"),
            ("bulk_delete_links", "Can bulk delete links"),
        ]

    def __str__(self):
        return repr(self.document_link_id)


class DocumentsView(models.Model):
    document_link_id = models.BigIntegerField(primary_key=True, verbose_name="Link ID")
    document_id = models.BigIntegerField(
        blank=True, null=True, verbose_name="Document ID"
    )
    document_name = models.CharField(
        blank=True, null=True, verbose_name="Document Name"
    )
    document_description = models.TextField(blank=True, null=True)
    link_table = models.ForeignKey(
        TblDocTableRef, models.DO_NOTHING, db_column="link_table"
    )
    link_row = models.BigIntegerField(blank=True, null=True)
    table_name = models.CharField(blank=True, null=True)
    customerid = models.ForeignKey(
        "assets.Tblcustomer", models.DO_NOTHING, db_column="CustomerID"
    )
    document_type_id = models.IntegerField(
        DocumentTypes,
        null=True,
        blank=True,
    )

    class Meta:
        managed = False
        db_table = "documents_view2"
        ordering = ["document_link_id"]


def calculate_document_checksum(file_path):
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


