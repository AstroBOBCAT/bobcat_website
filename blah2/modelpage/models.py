from django.db import models

# Create your models here.

class model(models.Model):
    model_id = models.FloatField(primary_key = True)
    source_name = models.CharField(max_length=200)
    paper_link = models.CharField(max_length = 300)
    evidence = models.CharField(max_length = 200)
    m1 = models.FloatField()
    m2 = models.FloatField()
    m_tot = models.FloatField()
    q = models.FloatField()
    m_chirp = models.FloatField()
    mu = models.FloatField()
    inclination = models.FloatField()
    eccentricity = models.FloatField()
    semimajor_axis = models.FloatField()
    gw_strain = models.FloatField()
    gw_frequency = models.FloatField()
    orb_frequency = models.FloatField()
    orb_period = models.FloatField()
    summary = models.CharField(max_length=600)


    class Meta:
        db_table = 'model'