from django.db import models

# Create your models here.


class source(models.Model):
    NED_name = models.CharField(primary_key=True, max_length=20)
    ra = models.CharField(max_length=20)
    dec = models.CharField(max_length=20)
    ra_deg = models.DecimalField(max_digits=8, decimal_places=5)
    dec_deg = models.DecimalField(max_digits=8, decimal_places=5)
    redshift = models.DecimalField(max_digits=8, decimal_places=5)
    luminosity_distance = models.DecimalField(blank=True, null=True, max_digits=20, decimal_places=5)



class binary_model(models.Model):
    id = models.BigAutoField(primary_key=True)
    paper_link = models.URLField(blank=True, null=True, max_length=300)
    source_name = models.CharField(blank=True, null=True, max_length=20)
    eccentricity = models.DecimalField(blank=True, null=True, max_digits=8, decimal_places=5)
    m1 = models.BigIntegerField(blank=True, null=True)
    m2 = models.BigIntegerField(blank=True, null=True)
    total_mass = models.BigIntegerField(blank=True, null=True)
    chirp_mass = models.BigIntegerField(blank=True, null=True)
    reduced_mass = models.BigIntegerField(blank=True, null=True)
    q = models.DecimalField(blank=True, null=True, max_digits=8, decimal_places=4)
    evid_type_1 = models.CharField(blank=True, null=True, max_length=50)
    evid_type_1_note = models.CharField(blank=True, null=True, max_length=50)
    evid_type_1_waveband = models.CharField(blank=True, null=True, max_length=50)
    evid_type_2 = models.CharField(blank=True, null=True, max_length=50)
    evid_type_2_note = models.CharField(blank=True, null=True, max_length=50)
    evid_type_2_waveband = models.CharField(blank=True, null=True, max_length=50)
    evid_type_3 = models.CharField(blank=True, null=True, max_length=50)
    evid_type_3_note = models.CharField(blank=True, null=True, max_length=50)
    evid_type_3_waveband = models.CharField(blank=True, null=True, max_length=50)
    evid_type_4 = models.CharField(blank=True, null=True, max_length=50)
    evid_type_4_note = models.CharField(blank=True, null=True, max_length=50)
    evid_type_4_waveband = models.CharField(blank=True, null=True, max_length=50)
    inclination = models.DecimalField(blank=True, null=True, max_digits=8, decimal_places=5)
    semi_major_axis = models.DecimalField(blank=True, null=True, max_digits=8, decimal_places=5)
    separation = models.DecimalField(blank=True, null=True, max_digits=8, decimal_places=5)
    period_epoch = models.IntegerField(blank=True, null=True)
    orb_freq = models.DecimalField(blank=True, null=True, max_digits=10, decimal_places=5)
    orb_period = models.DecimalField(blank=True, null=True, max_digits=10, decimal_places=5)
    gw_freq = models.DecimalField(blank=True, null=True, max_digits=10, decimal_places=5)
    gw_strain = models.DecimalField(blank=True, null=True, max_digits=10, decimal_places=5)
    summary = models.TextField(blank=True, null=True)
    caveats = models.TextField(blank=True, null=True)
    ext_projects = models.TextField(blank=True, null=True)


