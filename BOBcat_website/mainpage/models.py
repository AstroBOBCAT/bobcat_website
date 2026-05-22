from django.db import models

# Made by Dominic. KEEEP KEEP KEEP

# TODO make candidate table

"""
class Candidates(models.Model):
    redshift = models.FloatField(blank=True, null=True)


"""

#Models each row in the small ingestion list.
class Papers(models.Model):
    paper_id = models.AutoField(primary_key=True)
    paper_link = models.URLField(unique=True)
    candidate_name = models.CharField(max_length=100, blank=True, null=True)
    ned_name = models.CharField(max_length=100, blank=True, null=True)
    model_param_link = models.URLField(unique=True)  # TODO primary key
    notes = models.CharField(max_length=500, blank=True, null=True)

#Models each model_param sheet
class BinaryModel(models.Model):
    model_param_link = models.ForeignKey(
        'Papers',
        on_delete=models.CASCADE,
        to_field='model_param_link',
        db_column='model_param_link',
        primary_key=True,
    )
    sheet_id = models.CharField(max_length=100,
        help_text="Internal identifier linking this entry to its source spreadsheet")
    paper = models.CharField(max_length=200, blank=True, null=True,
        help_text="Citation key or bibcode for the paper this model is drawn from")
    eccentricity = models.FloatField(blank=True, null=True,
        help_text="Orbital eccentricity (0 = circular, 0–1 = bound elliptical orbit)")
    m1 = models.FloatField(blank=True, null=True,
        help_text="Primary black hole mass in solar masses (M☉)")
    m2 = models.FloatField(blank=True, null=True,
        help_text="Secondary black hole mass in solar masses (M☉)")
    mtot = models.FloatField(blank=True, null=True,
        help_text="Total system mass m1 + m2 in solar masses (M☉)")
    mc = models.FloatField(blank=True, null=True,
        help_text="Chirp mass — the mass combination that governs GW inspiral rate (M☉)")
    mu = models.FloatField(blank=True, null=True,
        help_text="Reduced mass μ = m1·m2 / (m1+m2) in solar masses (M☉)")
    q = models.FloatField(blank=True, null=True,
        help_text="Mass ratio q = m2/m1, where q ≤ 1 by convention")
    inclination = models.FloatField(blank=True, null=True,
        help_text="Orbital inclination relative to the line of sight, in degrees")
    semimajor_axis = models.FloatField(blank=True, null=True,
        help_text="Semimajor axis of the binary orbit in parsecs")
    seperation = models.FloatField(blank=True, null=True,
        help_text="Physical separation between the two black holes in parsecs")
    period_epoch = models.FloatField(blank=True, null=True,
        help_text="Reference epoch (MJD) at which the orbital period is defined")
    orb_freq = models.FloatField(blank=True, null=True,
        help_text="Orbital frequency in Hz")
    orb_period = models.FloatField(blank=True, null=True,
        help_text="Orbital period in years")
    summary = models.TextField(blank=True, null=True,
        help_text="Brief description of the model methodology and assumptions")
    caveats = models.TextField(max_length=500, blank=True, null=True,
        help_text="Known limitations, degeneracies, or assumptions to be aware of")
    ext_proj = models.TextField(max_length=100, blank=True, null=True,
        help_text="Associated external project or observing campaign")
    gw_strain = models.FloatField(blank=True, null=True,
        help_text="Gravitational wave strain amplitude h at Earth")
    gw_freq = models.FloatField(blank=True, null=True,
        help_text="Gravitational wave frequency in Hz (typically 2× the orbital frequency)")
    gw_strain_err = models.FloatField(blank=True, null=True,
        help_text="1σ uncertainty on the gravitational wave strain")
    gw_freq_err = models.FloatField(blank=True, null=True,
        help_text="1σ uncertainty on the gravitational wave frequency in Hz")


# Compacted table describing evidence types.
class Evidence(models.Model):
    model_param_link = models.ForeignKey('Papers', on_delete=models.CASCADE, to_field='model_param_link',
                                         db_column='model_param_link')
    type = models.CharField(max_length=100, blank=True, null=True)
    note = models.CharField(max_length=500, blank=True, null=True)
    waveband = models.CharField(max_length=25, blank=True, null=True)
