from django.contrib import admin
from assets.models import (
    Tbljobtypes,
    Tbljobstatus,    
)
# Register your models here.
#

admin.site.register([
    Tbljobstatus,
    Tbljobtypes,
])
