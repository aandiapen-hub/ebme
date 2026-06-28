from django.contrib import admin
from .models import SoftwareType

# Register your models here.

admin.site.register([
    SoftwareType,
])
