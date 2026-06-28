from django.db import models

# Create your models here.
#
class SoftwareType(models.Model):

    id = models.AutoField(
        primary_key=True,
        editable=False
    )
    name = models.CharField(
        max_length=100,
        unique=True,
    )

    description = models.TextField(
        blank=True,
    )

    class Meta:
        managed = False
        db_table = "software_type"
        ordering = ["name"]

    def __str__(self):
        return self.name

class Software(models.Model):
    """
    An installable software package or firmware release.
    """

    id = models.BigAutoField(
        primary_key=True,
        editable=False
    )

    brand = models.ForeignKey(
        'assets.tblbrands',
        on_delete=models.CASCADE,
    )

    name = models.CharField(max_length=200)

    version = models.CharField(max_length=100)

    part_number = models.CharField(
        max_length=100,
        blank=True,
    )

    gtin = models.CharField(
        max_length=100,
        blank=True,
    )

    release_date = models.DateField(
        null=True,
        blank=True,
    )

    notes = models.TextField(blank=True)

    software_type = models.ForeignKey(
        SoftwareType,
        on_delete=models.CASCADE,
        related_name="compatible_models",
    )

    class Meta:
        managed = False
        unique_together = (
            "brand",
            "name",
            "version",
        )
        db_table = 'software'

    def __str__(self):
        return f"{self.name} {self.version}"


class SoftwareModel(models.Model):
    """
    Defines which equipment models a software package
    can be installed on.
    """

    id = models.BigAutoField(
        primary_key=True, editable=False,
    )
    software = models.ForeignKey(
        Software,
        on_delete=models.CASCADE,
        related_name="compatible_models",
    )

    model = models.ForeignKey(
        "assets.Tblmodel",
        on_delete=models.CASCADE,
        related_name="supported_software",
    )

    mandatory = models.BooleanField(default=False)

    notes = models.TextField(blank=True)

    class Meta:
        managed = False
        unique_together = (
            "software",
            "model",
        )
        db_table = 'software_model'

    def __str__(self):
        return f"{self.software} -> {self.model}"


class EquipmentSoftware(models.Model):
    """
    Represents software actually installed on a specific
    equipment asset.
    """
    id = models.BigAutoField(
        primary_key=True, editable=False,
    )
    equipment = models.ForeignKey(
        "assets.tblAssets",
        on_delete=models.CASCADE,
        related_name="installed_software",
    )

    software = models.ForeignKey(
        Software,
        on_delete=models.PROTECT,
        related_name="installations",
    )

    installed_on = models.DateField(
        null=True,
        blank=True,
    )

    removed_on = models.DateField(
        null=True,
        blank=True,
    )

    is_current = models.BooleanField(default=True)

    notes = models.TextField(blank=True)

    class Meta:
        managed = False
        db_table = 'equipment_software'
        constraints = [
            models.UniqueConstraint(
                fields=["equipment", "software"],
                condition=models.Q(is_current=True),
                name="unique_current_software_install",
            )
        ]

    def __str__(self):
        return f"{self.software} -> {self.equipment}"
