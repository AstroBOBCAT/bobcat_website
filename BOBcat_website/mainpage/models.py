# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class BinaryModel(models.Model):
    binary_model_id = models.IntegerField(primary_key=True)
    paper = models.CharField(max_length=200, blank=True, null=True)
    candidate_name = models.ForeignKey('Candidate', models.DO_NOTHING, db_column='candidate_name', blank=True, null=True)
    eccentricity = models.FloatField(blank=True, null=True)
    m1 = models.FloatField(blank=True, null=True)
    m2 = models.FloatField(blank=True, null=True)
    mtot = models.FloatField(blank=True, null=True)
    mc = models.FloatField(blank=True, null=True)
    mu = models.FloatField(blank=True, null=True)
    q = models.FloatField(blank=True, null=True)
    evid1_type = models.CharField(max_length=100, blank=True, null=True)
    evid1_note = models.CharField(max_length=500, blank=True, null=True)
    evid1_wavelength = models.CharField(max_length=25, blank=True, null=True)
    evid2_type = models.CharField(max_length=100, blank=True, null=True)
    evid2_note = models.CharField(max_length=500, blank=True, null=True)
    evid2_wavelength = models.CharField(max_length=25, blank=True, null=True)
    evid3_type = models.CharField(max_length=100, blank=True, null=True)
    evid3_note = models.CharField(max_length=500, blank=True, null=True)
    evid3_wavelength = models.CharField(max_length=25, blank=True, null=True)
    evid4_type = models.CharField(max_length=100, blank=True, null=True)
    evid4_note = models.CharField(max_length=500, blank=True, null=True)
    evid4_wavelength = models.CharField(max_length=25, blank=True, null=True)
    inclination = models.FloatField(blank=True, null=True)
    semimajor_axis = models.FloatField(blank=True, null=True)
    seperation = models.FloatField(blank=True, null=True)
    period_epoch = models.FloatField(blank=True, null=True)
    orb_freq = models.FloatField(blank=True, null=True)
    orb_period = models.FloatField(blank=True, null=True)
    summary = models.CharField(max_length=500, blank=True, null=True)
    caveats = models.CharField(max_length=100, blank=True, null=True)
    ext_proj = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'binary_model'


class Candidate(models.Model):
    name = models.CharField(primary_key=True, max_length=50)
    ra_deg = models.FloatField(blank=True, null=True)
    dec_deg = models.FloatField(blank=True, null=True)
    redshift = models.FloatField(blank=True, null=True)
    obs_type_done = models.TextField(blank=True, null=True)  # This field type is a guess.

    class Meta:
        managed = False
        db_table = 'candidate'


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.SmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class MainpageBinaryModel(models.Model):
    binary_model_id = models.BigAutoField(primary_key=True)
    paper = models.CharField(max_length=300, blank=True, null=True)
    eccentricity = models.DecimalField(max_digits=8, decimal_places=5, blank=True, null=True)
    m1 = models.BigIntegerField(blank=True, null=True)
    m2 = models.BigIntegerField(blank=True, null=True)
    mu = models.BigIntegerField(blank=True, null=True)
    mc = models.BigIntegerField(blank=True, null=True)
    mtot = models.BigIntegerField(blank=True, null=True)
    q = models.DecimalField(max_digits=8, decimal_places=4, blank=True, null=True)
    evid1_note = models.CharField(max_length=50, blank=True, null=True)
    evid1_type = models.CharField(max_length=50, blank=True, null=True)
    evid1_wavelength = models.CharField(max_length=50, blank=True, null=True)
    evid2_note = models.CharField(max_length=50, blank=True, null=True)
    evid2_type = models.CharField(max_length=50, blank=True, null=True)
    evid2_wavelength = models.CharField(max_length=50, blank=True, null=True)
    evid3_note = models.CharField(max_length=50, blank=True, null=True)
    evid3_type = models.CharField(max_length=50, blank=True, null=True)
    evid3_wavelength = models.CharField(max_length=50, blank=True, null=True)
    evid4_note = models.CharField(max_length=50, blank=True, null=True)
    evid4_type = models.CharField(max_length=50, blank=True, null=True)
    evid4_wavelength = models.CharField(max_length=50, blank=True, null=True)
    inclination = models.DecimalField(max_digits=8, decimal_places=5, blank=True, null=True)
    semimajor_axis = models.DecimalField(max_digits=8, decimal_places=5, blank=True, null=True)
    separation = models.DecimalField(max_digits=8, decimal_places=5, blank=True, null=True)
    period_epoch = models.IntegerField(blank=True, null=True)
    orb_freq = models.DecimalField(max_digits=10, decimal_places=5, blank=True, null=True)
    orb_period = models.DecimalField(max_digits=10, decimal_places=5, blank=True, null=True)
    summary = models.TextField(blank=True, null=True)
    caveats = models.TextField(blank=True, null=True)
    ext_proj = models.TextField(blank=True, null=True)
    candidate_name = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'mainpage_binary_model'


class MainpageCandidate(models.Model):
    name = models.CharField(primary_key=True, max_length=20)
    obs_type_done = models.CharField(max_length=20)
    ra_deg = models.DecimalField(max_digits=8, decimal_places=5)
    dec_deg = models.DecimalField(max_digits=8, decimal_places=5)
    redshift = models.DecimalField(max_digits=8, decimal_places=5)

    class Meta:
        managed = False
        db_table = 'mainpage_candidate'
