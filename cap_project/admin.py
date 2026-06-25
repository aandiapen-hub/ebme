from django.contrib import admin
from .models import(
    CapitalProjectStatus,
    CapitalProjectType,
    CapitalProjectBidStatus,
    CommissionRequestStatus,
    )

admin.site.register([
    CapitalProjectStatus,
    CapitalProjectType,
    CapitalProjectBidStatus,
    CommissionRequestStatus,
])
