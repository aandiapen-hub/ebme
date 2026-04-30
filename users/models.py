
from django.db import models
from django.conf import settings

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from django.contrib.auth.base_user import BaseUserManager


class Roles(models.Model):
    role_name = models.CharField(unique=True, max_length=50)
    # role_description = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'roles'

    def __str__(self):
        return f"{self.role_name}"


class CustomUserManager(BaseUserManager):
    def create_user(self, email, user_name, first_name, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, user_name=user_name,
                          first_name=first_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, user_name, first_name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, user_name, first_name, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    user_name = models.CharField(unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    customerid = models.ForeignKey(
        'assets.Tblcustomer',
        models.DO_NOTHING,
        db_column='customerid',
        null=True)
    roleid = models.ForeignKey(
        Roles, models.DO_NOTHING, db_column='roleid', null=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ["user_name", "first_name"]

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user',
        blank=True,
        db_table='custom_user_groups'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_users',
        blank=True,
        db_table='custom_user_user_permissions'
    )

    class Meta:
        managed = False
        db_table = 'custom_user'


class AuthGroup(models.Model):
    name = models.CharField(max_length=150, unique=True)

    class Meta:
        db_table = 'auth_group'
        managed = False


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type_id = models.ForeignKey(
        ContentType, on_delete=models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        db_table = 'auth_permission'
        managed = False


class AuthGroupPermissions(models.Model):
    group = models.ForeignKey(
        AuthGroup, on_delete=models.DO_NOTHING, db_column='group_id')
    permission = models.ForeignKey(
        AuthPermission, on_delete=models.DO_NOTHING, db_column='permission_id')

    class Meta:
        db_table = 'auth_group_permissions'
        managed = False
        unique_together = (('group', 'permission'),)


class UserProfiles(models.Model):
    user_id = models.OneToOneField(
        'CustomUser', models.CASCADE, db_column='user_id')
    # This field type is a guess.
    table_settings = models.JSONField(blank=True)
    profile_id = models.AutoField(primary_key=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'user_profiles'

    def __str__(self):
        return f"{self.user_id.user_name}  preferences"

    def set_preference(self, table_name, key, value):
        """
        Update a single preference for a specific table.
        Example: set_table_preference("orders", "visible_columns",["id", "status"])
        table_settings will look like {"orders":{"visible_columns":['id','status']}}
        """
        settings = self.table_settings.get(table_name, {})
        settings[key] = value
        self.table_settings[table_name] = settings
        self.save(update_fields=['table_settings', 'updated_at'])

    def get_preference(self, table_name, key, default=None):
        return self.table_settings.get(table_name, {}).get(key, default)
