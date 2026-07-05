import hashlib
from io import BytesIO
from django.db import transaction, IntegrityError
from documents.models import TblDocuments, TblDocumentLinks, TempUploadGroup, TemporaryUpload
from django.core.exceptions import ValidationError
from documents.services.process_document import quick_group_processor
from PIL import Image, ImageOps
import uuid
import io
from django.contrib.contenttypes.models import ContentType
from documents.services.document_parser import parse_gs1code

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
    content=None,
    mime_type=None,
    document_type_id,
    temp_file=None,
    document_name=None,
    content_object=None,
    document_description=None,
):
    file_hash = None

    if document is None and uploaded_file is None and temp_file is None and content is None:
        raise ValidationError("No file found!")

    if uploaded_file:
        mime_type = uploaded_file.content_type
        if 'image/' in mime_type:
            content = Image.open(uploaded_file)
        else:
            content = uploaded_file.read()
            file_hash = hashlib.sha256(content).hexdigest()

        document_name = document_name or uploaded_file.name

    if temp_file:
        if "image/" in mime_type:
            content = Image.open(temp_file.file.path).convert("RGB")
        else:
            with open(temp_file.file.path, "rb") as f:
                content = f.read()
        document_name = temp_file.original_name
        mime_type = temp_file.mime_type


    # resize images
    if "image/" in mime_type:
        img = resizeimg(content)
        
        img = ImageOps.exif_transpose(img)
        buffer = BytesIO()
        content.save(buffer, format="JPEG", quality=85, optimize=True)
        # Get the resized image bytes
        content = buffer.getvalue()
        file_hash = hashlib.sha256(content).hexdigest()

    # --------------------------------------
    # check if document already exists in DB
    # --------------------------------------

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

    return document

def resizeimg(img, max_size=(2000, 2000)):
    img.thumbnail(max_size, Image.Resampling.LANCZOS)
    return img


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


def save_temp_files(group, content_object, file_name=None):
    """
    Save all files permanently and link them to the row/table.
    """

    temp_group = TempUploadGroup.objects.filter(pk=group).first()
    temp_files = temp_group.temp_uploads.all()

    image_files = [file for file in temp_files if "image/" in file.mime_type]

    non_image_files = [
        file for file in temp_files if "image/" not in file.mime_type
    ]

    with transaction.atomic():
        if image_files:
            images_pdf = convert_images_to_pdf(image_files)
            # Open all images
            create_document_from_file(
                document_name=f"{uuid.uuid4()}" + ".pdf",
                mime_type='application/pdf',
                content=images_pdf,
                document_type_id=temp_group.document_type_id,
                content_object=content_object,
            )

        if non_image_files:
            for file in non_image_files:
                create_document_from_file(
                    temp_file=file,
                    document_type_id=temp_group.document_type_id,
                    content_object=content_object,
                )


def delete_document_link(link):
    with transaction.atomic():
        documentid = link.documentid.pk
        link.delete()
        orphaned_documents = TblDocuments.objects.filter(
            pk=documentid, links__isnull=True
        )
        orphaned_documents.delete()


def delete_object_document_links(obj):
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


def save_temp_document(user, group_id=None, file=None, scanned_code=None):

    # non staff users can only have 1 scan group
    if not user.is_staff:
        user.temp_upload_group.all().delete()

    if file:
        group = None
        if group_id is not None:
            group = TempUploadGroup.objects.filter(pk=group_id).first()
            if group:
                if group.user != user:
                    raise ValidationError("Group belongs to another user")
        if group is None:
            group = TempUploadGroup.objects.create(
                user=user,
            )
        scanned = TemporaryUpload.from_uploaded_file(
            file=file,
            group=group,
        )
        quick_group_processor(scanned)
        return scanned

    elif scanned_code:
        gs1_data = parse_gs1code(
            scanned_code=scanned_code.replace('(', '').replace(')', '')
        )
        if set(gs1_data.keys()) == {'non_gs1_codes'}:
            # return list of non gs1 codes if no gs1 data found
            search = ' '.join(gs1_data['non_gs1_codes'])
            raise ValidationError({
                '__all__': 'Cannot add non GS1 barcode information to group',
                'search': search
            })
        
        barcode_data = [{
            'text': scanned_code,
            'parsed': gs1_data,
        }]
        if group_id is not None:
            group = TempUploadGroup.objects.filter(pk=group_id).first()
            if group.user != user:
                raise ValidationError("Group belongs to another user")
        else:
            group = TempUploadGroup.objects.create(
                user=user,
            )

        scanned = TemporaryUpload.objects.create(
            group=group,
            barcode_data=barcode_data,
        )

        quick_group_processor(scanned)
        return scanned

