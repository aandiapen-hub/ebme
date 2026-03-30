import hashlib
from django.db import transaction
from .models import TblDocuments, TblDocumentLinks, TemporaryUpload
from django.core.exceptions import ValidationError
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


def link_document_to_object(document, content_object, customer):
    link = TblDocumentLinks.objects.create(
        documentid=document,
        content_object=content_object,
        customer=customer,
    )
    return link


def create_document_from_file(
    *,
    uploaded_file=None,
    document_type_id,
    temp_file=None,
    document_name=None,
    content_object=None,
    document_description=None,
):
    if uploaded_file is None and temp_file is None:
        raise ValidationError("No file found!")

    if uploaded_file:
        content = (uploaded_file.read(),)
        mime_type = (uploaded_file.content_type,)
        file_size = (uploaded_file.size,)

    if temp_file:
        if "image/" in mime_type:
            Image.open(temp_file.file.path).convert("RGB")
            content = resizeimg(content)
        else:
            with open(temp_file.file.path, "rb") as f:
                content = f.read()
        document_name = temp_file.original_name
        mime_type = temp_file.mime_type
        file_size = temp_file.file_size

    file_hash = hashlib.sha256(content).hexdigest()
    customer = resolve_customer(content_object)

    with transaction.atomic():
        document, created = TblDocuments.objects.get_or_create(
            document_hash=file_hash,
            defaults={
                "document_name": document_name,
                "mime_type": mime_type,
                "document_bytea": content,
                "document_description": document_description,
                "file_size": file_size,
                "document_type_id": document_type_id,
            },
        )

        if content_object:
            link_document_to_object(document, content_object, customer)

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


def convert_images_to_pdf(image_files):
    images = [Image.open(img.file.path).convert("RGB") for img in image_files]
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
    return pdf_bytes


def save_temp_files(group, user, content_object, document_type=None, file_name=None):
    """
    Save all files permanently and link them to the row/table.
    """

    temp_files_list = TemporaryUpload.objects.filter(user=user, group=group)
    image_files = [file for file in temp_files_list if "image/" in file.mime_type]

    non_image_files = [
        file for file in temp_files_list if "image/" not in file.mime_type
    ]

    with transaction.atomic():
        if image_files:
            images_pdf = convert_images_to_pdf(image_files)
            # Open all images
            create_document_from_file(
                document_name=f"{uuid.uuid4()}" + ".pdf",
                mime_type="application/pdf",
                content=images_pdf,
                file_size=len(images_pdf),
                document_type_id=document_type,
                content_object=content_object,
            )
            for image in image_files:
                image.delete()

        if non_image_files:
            for file in non_image_files:
                create_document_from_file(
                    temp_file=file,
                    document_type_id=document_type,
                    content_object=content_object,
                )

            for file in non_image_files:
                file.delete()
