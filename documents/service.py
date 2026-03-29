import hashlib
from django.db import transaction
from .models import TblDocuments, TblDocumentLinks
from PIL import Image
import uuid
import io

def resolve_customer(content_object):
    if not content_object:
        return None

    if hasattr(content_object, "customer"):
        return content_object.customer

    if hasattr(content_object, "asset") and hasattr(content_object.asset, "customer"):
        return content_object.asset.customer

    return None


def create_document_from_file(
    *,
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
    customer = resolve_customer(content_object)

    existing_document = TblDocuments.objects.filter(
        document_hash=file_hash
    ).first()

    with transaction.atomic():

        if not existing_document:
            document = TblDocuments.objects.create(
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
                documentid=document,
                content_object=content_object,
                customer=customer,
            )

        if temp_file:
            temp_file.delete()

    return document


def resizeimg(img):
    # Calculate new size (50%)
    new_width = img.width // 2
    new_height = img.height // 2

    # Resize
    resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    return resized_img


class SaveTempFiles:
    def __init__(self, temp_files, content_object, document_type=None, file_name=None):
        self.temp_files_list = temp_files
        self.file_name = file_name
        self.document_type = document_type
        self.content_object = content_object

    def save_single_file(self):
        file = self.temp_files_list[0]
        with open(file.file.path, "rb") as f:
            content = f.read()
        create_document_from_file(
            temp_file=file,
            content=content,
            document_type_id=self.document_type,
            content_object=self.content_object,
        )

    def save_all(self):
        """
        Save all files permanently and link them to the row/table.
        """
        with transaction.atomic():
            if len(self.temp_files_list) == 1:
                self.save_single_file()

            else:
                image_files = [
                    file for file in self.temp_files_list if "image/" in file.mime_type
                ]
                # Open all images
                if image_files:
                    images = [
                        Image.open(img.file.path).convert("RGB") for img in image_files
                    ]
                    downscaled_images = list(map(resizeimg, images))

                    # Create a bytes buffer instead of saving to disk
                    pdf_bytes_io = io.BytesIO()
                    # Save as PDF
                    # The first image is used as the starting point, the rest are appended
                    downscaled_images[0].save(
                        pdf_bytes_io,
                        format="PDF",
                        save_all=True,
                        append_images=downscaled_images[1:],
                    )
                    # Get bytes for storage
                    pdf_bytes = pdf_bytes_io.getvalue()
                    pdf_bytes_io.close()

                    create_document_from_file(
                        document_name=f"{uuid.uuid4()}" + ".pdf",
                        mime_type="application/pdf",
                        content=pdf_bytes,
                        file_size=len(pdf_bytes),
                        document_type_id=self.document_type,
                        content_object=self.content_object,
                    )

                    for image in image_files:
                        image.delete()
