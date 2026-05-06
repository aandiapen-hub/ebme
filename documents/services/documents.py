import hashlib
from django.db import transaction, IntegrityError
from documents.models import TblDocuments, TblDocumentLinks, TemporaryUpload
from django.core.exceptions import ValidationError
from PIL import Image
import uuid
import io
from django.contrib.contenttypes.models import ContentType


def resolve_customer(content_object):
    if not content_object:
        return None

    if hasattr(content_object, "customerid"):
        return content_object.customerid

    if hasattr(content_object, "assetid"):
        return content_object.assetid.customerid

    return None


def link_document_to_object(document, content_object, customer):
    content_type = ContentType.objects.get_for_model(content_object)
    link, created = TblDocumentLinks.objects.get_or_create(
        documentid=document,
        content_type=content_type,
        object_id=content_object.pk,
        customer=customer,
    )
    return link


def create_document_from_file(
    *,
    document=None,
    uploaded_file=None,
    document_type_id,
    temp_file=None,
    document_name=None,
    content_object=None,
    document_description=None,
):
    if document is None and uploaded_file is None and temp_file is None:
        raise ValidationError("No file found!")

    content = None

    if uploaded_file:
        content = uploaded_file.read()
        mime_type = uploaded_file.content_type
        document_name = document_name or uploaded_file.name

    if temp_file:
        if "image/" in mime_type:
            Image.open(temp_file.file.path).convert("RGB")
            content = resizeimg(content)
        else:
            with open(temp_file.file.path, "rb") as f:
                content = f.read()
        document_name = temp_file.original_name
        mime_type = temp_file.mime_type

    # --------------------------------------
    # check if document already exists in DB
    # --------------------------------------
    if content:
        file_hash = hashlib.sha256(content).hexdigest()
    else:
        file_hash = None

    customer = resolve_customer(content_object)

    with transaction.atomic():
        # ------------------------------------------------
        # Updating an existing document
        # ------------------------------------------------

        # First check if content already exists
        if document is not None and file_hash:
            duplicate = TblDocuments.objects.filter(document_hash=file_hash).exclude(
                pk=document.pk
            )
            if duplicate.exists():
                raise ValidationError("This uploaded file already exists.")

        # update with content if the content is valid
        if document is not None and content:
            document.document_name = document_name
            document.mime_type = mime_type
            document.description = document_description
            document.set_content(content, file_hash=file_hash)

        # update without new content
        if document is not None:
            document.document_name = document_name
            document.description = document_description

        else:
            # ------------------------------------------------
            # creating new document and links
            # ------------------------------------------------

            # first check if document exists by hash
            document = TblDocuments.objects.filter(document_hash=file_hash).first()
            if document is None:
                document = TblDocuments(
                    document_name=document_name,
                    mime_type=mime_type,
                    document_description=document_description,
                )
            document.set_content(content, file_hash=file_hash)

        try:
            document.save()
        except IntegrityError:
            raise ValidationError("This file already exists.")

        if content_object:
            link_document_to_object(
                document=document, content_object=content_object, customer=customer
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


def delete_link_document(link):
    with transaction.atomic():
        documentid = link.documentid.pk
        link.delete()
        other_document_links = TblDocumentLinks.objects.filter(documentid=documentid)
        if not other_document_links.exists():
            TblDocuments.objects.get(document_id=documentid).delete()


def delete_linked_documents(obj):
    if not hasattr(obj, 'document_links'):
        return
    linked_documents = obj.document_links.all()
    document_ids = list(
        linked_documents.values_list('pk', flat=True)
    )
    linked_documents.delete()

    orphaned_documents = TblDocuments.objects.filter(
        pk__in=document_ids, links__isnull=True
    )
    orphaned_documents.delete()


