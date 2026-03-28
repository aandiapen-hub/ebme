import os
from django.db import models
import hashlib
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

# Create your models here.
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.db import transaction

from io import BytesIO
from django.core.files.base import ContentFile
from PIL import Image

from documents.utils import clear_extraction_results


class TblDocumentTypes(models.Model):
    document_type_id = models.BigAutoField(primary_key=True)
    document_type_name = models.CharField()

    class Meta:
        managed = False
        db_table = "tbl_document_types"

    def __str__(self):
        return f"{self.document_type_name}"


class TblDocuments(models.Model):
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
    document_type_id = models.ForeignKey(
        TblDocumentTypes,
        models.PROTECT,
        db_column="document_type_id",
        null=True,
        blank=True,
    )
    document_hash = models.CharField(
        max_length=64, unique=True, db_index=True, null=True, blank=True
    )

    def __str__(self):
        return self.document_name

    @classmethod
    def from_file(
        cls,
        content,
        document_type_id,
        temp_file=None,
        document_name=None,
        mime_type=None,
        file_size=None,
        content_object=None,
        document_description=None,
    ):
        if temp_file:
            document_name = temp_file.original_name
            mime_type = temp_file.mime_type
            file_size = temp_file.file_size

        file_hash = hashlib.sha256(content).hexdigest()
        with transaction.atomic():
            # Check if a document with this hash already exists
            existing_object = cls.objects.filter(document_hash=file_hash).first()

            if existing_object:
                created_object = existing_object

            else:
                created_object = cls.objects.create(
                    document_name=document_name,
                    mime_type=mime_type,
                    document_bytea=content,
                    document_description=document_description,
                    file_size=file_size,
                    document_type_id=document_type_id,
                    document_hash=file_hash,
                )

            if content_object:
                TblDocumentLinks.objects.create(
                    documentid=created_object,
                    content_object=content_object,
                )

            if temp_file:
                temp_file.delete()

    class Meta:
        managed = False
        db_table = "tbl_aws_documents"


# temp media files folder
temp_storage = FileSystemStorage(
    location=os.path.join(settings.MEDIA_ROOT, "temp_uploads")
)


class TemporaryUpload(models.Model):
    file = models.FileField(upload_to="", storage=temp_storage)
    mime_type = models.CharField(max_length=100)
    original_name = models.CharField(max_length=100)
    file_size = models.BigIntegerField()
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,  # delete files if user is deleted
    )
    upload_at = models.DateTimeField(auto_now_add=True)
    group = models.IntegerField(default=1)

    @classmethod
    def from_uploaded_file(cls, user, file, group=None):
        return cls.objects.create(
            user=user,
            file=file,
            mime_type=file.content_type,
            file_size=file.size,
            original_name=file.name,
            group=group,
        )

    def save(self, *args, **kwargs):
        # Only compress if new file is being uploaded
        if self.file:
            ext = os.path.splitext(self.file.name)[1].lower()

            if ext in [".jpg", ".jpeg", ".png"]:
                img = Image.open(self.file)

                # Convert PNG with transparency to RGB (avoid errors)
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")

                # Create a BytesIO buffer
                buffer = BytesIO()
                if ext in [".jpg", ".jpeg"]:
                    img.save(buffer, format="JPEG", quality=70, optimize=True)
                elif ext == ".png":
                    img.save(buffer, format="PNG", optimize=True)

                # Replace file with compressed version
                buffer.seek(0)
                self.file.save(self.file.name, ContentFile(buffer.read()), save=False)

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Ensure the file is also deleted from disk when model is deleted
        if self.file:
            self.file.delete(save=False)
            clear_extraction_results(user_id=self.user, group=self.group)
        super().delete(*args, **kwargs)

    class Meta:
        managed = False
        db_table = "tbl_temporaryupload"


class TblDocTableRef(models.Model):
    table_id = models.BigIntegerField(primary_key=True)
    table_name = models.CharField(unique=True)

    class Meta:
        managed = False
        db_table = "tbl_doc_table_ref"

    def __str__(self):
        return f"{self.table_name}"


class TblDocumentLinks(models.Model):
    document_link_id = models.BigAutoField(primary_key=True)
    documentid = models.ForeignKey(
        TblDocuments,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        db_column="document_id",
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
    )
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    class Meta:
        managed = False
        db_table = "tbl_document_links"
        ordering = ["document_link_id"]

    @staticmethod
    def delete_link_documents(obj):
        table_name = obj._meta.db_table
        links = TblDocumentLinks.objects.filter(
            link_table__table_name__iexact=table_name.lower(), link_row=obj.pk
        )
        for link in links:
            with transaction.atomic():
                documentid = link.documentid.document_id
                link.delete()
                other_document_links = TblDocumentLinks.objects.filter(
                    documentid=documentid
                )
                print(other_document_links)
                if not other_document_links.exists():
                    TblDocuments.objects.get(document_id=documentid).delete()


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
    document_type_id = models.ForeignKey(
        TblDocumentTypes,
        models.PROTECT,
        db_column="document_type_id",
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

