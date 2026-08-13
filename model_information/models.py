from django.db import models
from django.db.models import Q
from django.urls import reverse


class ModelView(models.Model):
    model_id = models.IntegerField(primary_key=True, db_column="ModelID")
    brand_id = models.IntegerField(null=True, blank=True, db_column="BrandID")
    category_id = models.IntegerField(null=True, blank=True, db_column="categoryid")

    model_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_column="modelname",
    )

    brand_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_column="brandname",
    )

    category_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_column="categoryname",
    )

    class Meta:
        managed = False
        db_table = "model_view"

    def get_absolute_url(self):
        return reverse('model_information:model_view', kwargs={'pk':self.pk})

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

    version_number = models.IntegerField(default=1)

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
    
    def get_absolute_url(self):
        return reverse('model_information:software_detail', kwargs={'pk':self.pk})


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

class EquipmentConfigurationStatus(models.Model):
    id = models.BigAutoField(primary_key=True)

    code = models.CharField(max_length=50, unique=True)

    name = models.CharField(max_length=100)

    description = models.TextField(blank=True)

    sort_order = models.IntegerField(default=0)

    is_terminal = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = "equipment_configuration_status"
        ordering = ["sort_order"]

    def __str__(self):
        return self.name

class EquipmentConfigurationQuerySet(models.QuerySet):

    def active(self):
        return self.filter(
            configuration_status__code="active"
        )

    def for_model(self, model):
        return self.filter(
            model_links__model=model
        )

    def resolve(self, asset):
        if asset.locationid is None:
            return None

        qs = (
            self.active()
            .for_model(asset.modelid)
        )

        site = asset.locationid.siteid
        location = asset.locationid

        # 1. Exact location match
        config = qs.filter(
            scopes__site=site,
            scopes__location=location,
        ).first()

        if config:
            return config

        # 2. Site-wide match
        config = qs.filter(
            scopes__site=site,
            scopes__location__isnull=True,
        ).first()

        if config:
            return config

        # 3. Global match
        return qs.filter(
            scopes__isnull=True
        ).first()


class EquipmentConfiguration(models.Model):
    """
    Defines a configuration policy that can apply to equipment.
    """

    id = models.BigAutoField(primary_key=True, editable=False)

    name = models.CharField(max_length=200)
    configuration_status = models.ForeignKey(EquipmentConfigurationStatus, on_delete=models.PROTECT)
    version = models.IntegerField(default=1)

    brand = models.ForeignKey(
        'assets.tblbrands',
        on_delete=models.CASCADE,
    )

    description = models.TextField(blank=True)

    active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    objects = EquipmentConfigurationQuerySet.as_manager()

    class Meta:
        managed = False
        db_table = "equipment_configuration"

    def get_absolute_url(self):
        return reverse('model_information:configuration_detail', kwargs={'pk':self.pk})

    def __str__(self):
        return self.name


class EquipmentConfigurationModel(models.Model):
    """
    Links configurations to compatible equipment models.
    """

    id = models.BigAutoField(primary_key=True, editable=False)

    configuration = models.ForeignKey(
        EquipmentConfiguration,
        on_delete=models.CASCADE,
        related_name="model_links",
    )

    model = models.ForeignKey(
        "assets.Tblmodel",
        on_delete=models.CASCADE,
        related_name="configuration_links",
    )

    mandatory = models.BooleanField(default=False)

    notes = models.TextField(blank=True,)

    class Meta:
        managed = False
        db_table = "equipment_configuration_model"
        unique_together = ("configuration", "model")

    def __str__(self):
        return f"{self.configuration} -> {self.model}"


class EquipmentConfigurationScope(models.Model):
    """
    Defines where a configuration applies.
    """

    id = models.BigAutoField(primary_key=True, editable=False)

    configuration = models.ForeignKey(
        EquipmentConfiguration,
        on_delete=models.CASCADE,
        related_name="scopes",
    )

    site = models.ForeignKey(
        "assets.Tblsites",
        on_delete=models.PROTECT,
    )

    location = models.ForeignKey(
        "assets.Tbllocations",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    class Meta:
        managed = False
        db_table = "equipment_configuration_scope"
        constraints = [
            models.UniqueConstraint(
                fields=["configuration", "site", "location"],
                name="uniq_config_site_location",
            )
        ]


class EquipmentConfigurationLink(models.Model):
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
        related_name="installed_config",
    )

    configuration = models.ForeignKey(
        EquipmentConfiguration,
        on_delete=models.PROTECT,
        related_name="installed",
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
        db_table = 'equipment_configuration_link'
        constraints = [
            models.UniqueConstraint(
                fields=["equipment", "configuration"],
                condition=models.Q(is_current=True),
                name="unique_current_configuration_install",
            )
        ]
