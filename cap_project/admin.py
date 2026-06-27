from django.contrib import admin
from .models import(
    CapitalAcquisition,
    CapitalProjectStatus,
    CapitalProjectType,
    CapitalAcquisitionStatus,
    CommissionRequestStatus,
    )

admin.site.register([
    CapitalProjectStatus,
    CapitalProjectType,
    CapitalAcquisitionStatus,
    CommissionRequestStatus,
])
