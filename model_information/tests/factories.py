import factory
from assets.tests.factories import ModelFactory
from assets.models import Tblcheckslists
from factory.django import DjangoModelFactory
from assets.tests.factories import (
    BrandFactory,
    AssetFactory,
    SiteFactory,
    LocationFactory,
)
from model_information.models import (
    SoftwareType,
    Software,
    SoftwareModel,
    EquipmentSoftware,
    EquipmentConfigurationStatus,
    EquipmentConfiguration,
    EquipmentConfigurationModel,
    EquipmentConfigurationScope,
    EquipmentConfigurationLink,
)

class TblcheckslistsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tblcheckslists

    testname = factory.Sequence(lambda n: f"Test {n}")

    test_description = factory.Faker(
        "paragraph",
        nb_sentences=3,
    )
    modelid = factory.SubFactory(ModelFactory)




class SoftwareTypeFactory(DjangoModelFactory):
    class Meta:
        model = SoftwareType
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"Software Type {n}")
    description = factory.Faker("sentence")


class SoftwareFactory(DjangoModelFactory):
    class Meta:
        model = Software

    brand = factory.SubFactory(BrandFactory)

    name = factory.Sequence(lambda n: f"Software Package {n}")

    version = factory.Sequence(lambda n: f"v1.{n}")
    version_number = factory.Sequence(lambda n: n + 1)

    part_number = factory.Faker("bothify", text="PN-#####")
    gtin = factory.Faker("ean13")

    release_date = factory.Faker("date_object")

    notes = factory.Faker("paragraph")

    software_type = factory.SubFactory(SoftwareTypeFactory)


class SoftwareModelFactory(DjangoModelFactory):
    class Meta:
        model = SoftwareModel

    software = factory.SubFactory(SoftwareFactory)
    model = factory.SubFactory(ModelFactory)

    mandatory = False
    notes = factory.Faker("sentence")


class EquipmentSoftwareFactory(DjangoModelFactory):
    class Meta:
        model = EquipmentSoftware

    equipment = factory.SubFactory(AssetFactory)
    software = factory.SubFactory(SoftwareFactory)

    installed_on = factory.Faker("date_object")

    removed_on = None

    is_current = True

    notes = factory.Faker("sentence")




class EquipmentConfigurationStatusFactory(DjangoModelFactory):
    class Meta:
        model = EquipmentConfigurationStatus
        django_get_or_create = ("code",)

    code = factory.Sequence(lambda n: f"status-{n}")
    name = factory.LazyAttribute(
        lambda obj: obj.code.replace("-", " ").title()
    )
    description = factory.Faker("sentence")
    sort_order = factory.Sequence(int)
    is_terminal = False


class ActiveConfigurationStatusFactory(
    EquipmentConfigurationStatusFactory
):
    code = "active"
    name = "Active"


class DraftConfigurationStatusFactory(
    EquipmentConfigurationStatusFactory
):
    code = "draft"
    name = "Draft"


class RetiredConfigurationStatusFactory(
    EquipmentConfigurationStatusFactory
):
    code = "retired"
    name = "Retired"
    is_terminal = True


class EquipmentConfigurationFactory(DjangoModelFactory):
    class Meta:
        model = EquipmentConfiguration

    name = factory.Sequence(
        lambda n: f"Configuration {n}"
    )

    configuration_status = factory.SubFactory(
        ActiveConfigurationStatusFactory
    )

    version = factory.Sequence(
        lambda n: n + 1
    )

    brand = factory.SubFactory(
        BrandFactory
    )

    description = factory.Faker(
        "paragraph"
    )

    active = True


class EquipmentConfigurationModelFactory(
    DjangoModelFactory
):
    class Meta:
        model = EquipmentConfigurationModel

    configuration = factory.SubFactory(
        EquipmentConfigurationFactory
    )

    model = factory.SubFactory(
        ModelFactory
    )

    mandatory = False

    notes = factory.Faker(
        "sentence"
    )


class EquipmentConfigurationScopeFactory(
    DjangoModelFactory
):
    class Meta:
        model = EquipmentConfigurationScope

    configuration = factory.SubFactory(
        EquipmentConfigurationFactory
    )

    location = factory.SubFactory(
        LocationFactory
    )

    site = factory.SelfAttribute( "location.siteid" )


class SiteConfigurationScopeFactory(
    EquipmentConfigurationScopeFactory
):
    """
    Applies to all locations within a site.
    """

    location = None


class LocationConfigurationScopeFactory(
    EquipmentConfigurationScopeFactory
):
    """
    Applies only to a specific location.
    """

    location = factory.SubFactory(
        LocationFactory
    )


class EquipmentConfigurationLinkFactory(
    DjangoModelFactory
):
    class Meta:
        model = EquipmentConfigurationLink

    equipment = factory.SubFactory(
        AssetFactory
    )

    configuration = factory.SubFactory(
        EquipmentConfigurationFactory
    )

    installed_on = factory.Faker(
        "date_object"
    )

    removed_on = None

    is_current = True

    notes = factory.Faker(
        "sentence"
    )
