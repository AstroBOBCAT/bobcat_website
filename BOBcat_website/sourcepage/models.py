from django.db import models
#Made by Dominic. KEEEP KEEP KEEP

class Papers(models.Model):
    paper_id = models.AutoField(primary_key=True)
    paper_link = models.URLField()
    candidate_name = models.CharField(max_length=100, blank=True, null=True)
    ned_name = models.CharField(max_length=100, blank=True, null=True)
    model_param_link = models.URLField()
    notes = models.CharField(max_length=500, blank=True, null=True)

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
    inclination = models.FloatField(blank=True, null=True)
    semimajor_axis = models.FloatField(blank=True, null=True)
    seperation = models.FloatField(blank=True, null=True)
    period_epoch = models.FloatField(blank=True, null=True)
    orb_freq = models.FloatField(blank=True, null=True)
    orb_period = models.FloatField(blank=True, null=True)
    summary = models.CharField(max_length=500, blank=True, null=True)
    caveats = models.CharField(max_length=100, blank=True, null=True)
    ext_proj = models.CharField(max_length=100, blank=True, null=True)
    gw_strain = models.FloatField(blank=True, null=True)
    gw_freq = models.FloatField(blank=True, null=True)
    gw_strain_err = models.FloatField(blank=True, null=True)
    gw_freq_err = models.FloatField(blank=True, null=True)

#Compacted table describing evidence types.
class Evidence(models.Model):
    binary_model_id = models.ForeignKey(to='BinaryModel', db_column='binary_model_id', on_delete=models.CASCADE, unique=False)
    type = models.CharField(max_length=100, blank=True, null=True)
    note = models.CharField(max_length=500, blank=True, null=True)
    wavelength = models.CharField(max_length=25, blank=True, null=True)
