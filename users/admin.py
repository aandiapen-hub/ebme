from django.contrib import admin
from .models import CustomUser
from .models import Roles
from django.contrib.auth.admin import UserAdmin
# Register your models here.

class UserAdminConfig(UserAdmin):
    search_fields = ('email','user_name','first_name',)
    ordering = ('-date_joined',)
    list_display =  ('email','user_name','is_active','is_staff',"customerid","roleid")
    
    fieldsets = (
        (None,{'fields':('email','user_name','first_name','last_name','password')}),
        ('Permissions',{'fields':('is_staff','is_active')}),
        ('Roles',{'fields':('customerid','roleid')}),
        ('Groups',{'fields':('user_permissions','groups')})
        
    )
    add_fieldsets = (
        (None,{'fields':('email','user_name','first_name','last_name')}),
        ('Password',{'fields':('password1','password2')}),
        ('Permissions',{'fields':('is_staff','is_active')}),
        ('Roles',{'fields':('customerid','roleid')}),
        
    )


admin.site.register(CustomUser,UserAdminConfig)


class RoleAdminConfig(admin.ModelAdmin):
    model = Roles
    search_fields = ('role_name',)
    fields = ('role_name',)
admin.site.register(Roles,RoleAdminConfig)
    
                      
