from django.db import models


WAVEBAND_CHOICES = [
    ('radio', 'Radio'),
    ('infrared', 'Infrared'),
    ('optical', 'Optical'),
    ('UV', 'UV'),
    ('x-ray', 'X-ray'),
    ('gamma-ray', 'Gamma-ray'),
]

ERROR_TYPE_CHOICES = [
    ('Assumed', 'Assumed'),
    ('Upper limit', 'Upper limit'),
    ('Lower limit', 'Lower limit'),
    ('Gaussian', 'Gaussian'),
    ('Two-sided', 'Two-sided'),
    ('Representative', 'Representative'),
]


class EvidenceCategory(models.Model):
    evidence_category_id = models.SmallAutoField(primary_key=True)
    name = models.CharField(max_length=60, unique=True)

    class Meta:
        db_table = 'evidence_category'

    def __str__(self):
        return self.name


class EvidenceSubcategory(models.Model):
    evidence_subcategory_id = models.SmallAutoField(primary_key=True)
    category = models.ForeignKey(EvidenceCategory, on_delete=models.PROTECT)
    name = models.CharField(max_length=50)

    class Meta:
        db_table = 'evidence_subcategory'
        unique_together = [('category', 'name')]

    def __str__(self):
        return f'{self.category.name} / {self.name}'


# ===================
# CORE TABLES
# ===================

class Candidate(models.Model):
    # NED-recognized name used as the natural primary key
    name = models.CharField(max_length=100, primary_key=True)
    # RA/Dec in J2000 decimal degrees — double precision (~1e-10 deg = 1 µas)
    jra = models.FloatField()
    jdec = models.FloatField()
    # Redshift: not a reliable distance indicator below z~0.01
    redshift = models.FloatField(null=True, blank=True)
    # Luminosity distance in Mpc; preferred over redshift for nearby objects
    lum_dist = models.FloatField(null=True, blank=True)
    # Placeholder source ranking; positive/negative integer scale
    rating = models.SmallIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'candidate'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['jra', 'jdec']),
        ]

    def __str__(self):
        return self.name


class Bib(models.Model):
    # 19-character ADS/SciX bibcode used as the natural primary key
    bib_id = models.CharField(max_length=19, primary_key=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    doi = models.CharField(max_length=100, unique=True, null=True, blank=True)
    title = models.TextField(null=True, blank=True)
    year = models.SmallIntegerField(null=True, blank=True)
    # Citation count as of updated_at; max SmallIntegerField is 32,767
    citations = models.SmallIntegerField(null=True, blank=True)

    class Meta:
        db_table = 'bib'

    def __str__(self):
        return self.bib_id


class BinaryModel(models.Model):
    binary_model_id = models.BigAutoField(primary_key=True)
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.PROTECT,
        to_field='name',
    )
    bib = models.ForeignKey(
        Bib,
        on_delete=models.PROTECT,
        to_field='bib_id',
    )
    created_at = models.DateTimeField(null=True, blank=True)
    # Google Sheets parameter key — exclude from public API responses at the serializer/view level
    sheet_id = models.TextField(null=True, blank=True)

    # Orbital parameters — nullable; not all are constrained for every model
    eccentricity = models.FloatField(null=True, blank=True)
    m1 = models.FloatField(null=True, blank=True, help_text="Larger BH mass in M☉")
    m2 = models.FloatField(null=True, blank=True, help_text="Smaller BH mass in M☉")
    mtot = models.FloatField(null=True, blank=True, help_text="Total mass m1+m2 in M☉")
    mc = models.FloatField(null=True, blank=True, help_text="Chirp mass in M☉")
    mu = models.FloatField(null=True, blank=True, help_text="Reduced mass in M☉")
    q = models.FloatField(null=True, blank=True, help_text="Mass ratio m2/m1 ≤ 1")
    inclination = models.FloatField(null=True, blank=True, help_text="Orbital inclination in degrees")
    semimajor_axis = models.FloatField(null=True, blank=True, help_text="Semimajor axis in parsecs")
    separation = models.FloatField(null=True, blank=True, help_text="Projected separation in parsecs")
    rm_orb_period = models.FloatField(
        null=True, blank=True,
        db_column='RM_orb_period',
        help_text="Earth-frame orbital period in years",
    )
    rm_orb_period_epoch = models.FloatField(
        null=True, blank=True,
        db_column='RM_orb_period_epoch',
        help_text="Reference epoch (MJD) for the orbital period",
    )
    # Calculated fields
    gw_strain = models.FloatField(null=True, blank=True, help_text="GW strain amplitude h at Earth (circular orbit)")
    gw_inspiral_timescale = models.FloatField(null=True, blank=True, help_text="Time to coalescence in seconds (GR, circular orbit)")

    summary = models.CharField(max_length=750, null=True, blank=True)
    caveats = models.CharField(max_length=750, null=True, blank=True)
    ext_proj = models.CharField(max_length=750, null=True, blank=True)

    class Meta:
        db_table = 'binary_model'
        indexes = [
            models.Index(fields=['candidate']),
            models.Index(fields=['bib']),
            models.Index(fields=['mtot']),
        ]

    def __str__(self):
        return f'{self.candidate_id} / {self.bib_id} (id={self.binary_model_id})'


# ===================
# PERIOD MEASUREMENTS
# ===================

class ObsPeriod(models.Model):
    obs_period_id = models.BigAutoField(primary_key=True)
    binary_model = models.ForeignKey(BinaryModel, on_delete=models.PROTECT)
    waveband = models.CharField(max_length=10, choices=WAVEBAND_CHOICES, null=True, blank=True)
    value = models.FloatField(help_text="Measured period")
    epoch = models.FloatField(help_text="Reference epoch in MJD")

    class Meta:
        db_table = 'obs_period'
        indexes = [
            models.Index(fields=['binary_model']),
            models.Index(fields=['value']),
        ]


class ObsPeriodError(models.Model):
    obs_period = models.OneToOneField(ObsPeriod, on_delete=models.PROTECT, primary_key=True)
    error_type = models.CharField(max_length=20, choices=ERROR_TYPE_CHOICES, null=True, blank=True)
    error_upper = models.FloatField(null=True, blank=True)
    error_lower = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = 'obs_period_error'


# ===================
# EVIDENCE TRACKING
# ===================

class ModelEvidence(models.Model):
    model_evidence_id = models.BigAutoField(primary_key=True)
    binary_model = models.ForeignKey(BinaryModel, on_delete=models.PROTECT)
    subcategory = models.ForeignKey(EvidenceSubcategory, on_delete=models.PROTECT)

    class Meta:
        db_table = 'model_evidence'
        indexes = [
            models.Index(fields=['binary_model']),
            models.Index(fields=['subcategory']),
        ]


class ModelEvidenceWaveband(models.Model):
    model_evidence_waveband_id = models.BigAutoField(primary_key=True)
    evidence = models.ForeignKey(ModelEvidence, on_delete=models.PROTECT)
    waveband = models.CharField(max_length=10, choices=WAVEBAND_CHOICES)

    class Meta:
        db_table = 'model_evidence_waveband'
        unique_together = [('evidence', 'waveband')]


# ===================
# ERROR TRACKING
# ===================

class BinaryModelError(models.Model):
    binary_model_error_id = models.BigAutoField(primary_key=True)
    binary_model = models.ForeignKey(BinaryModel, on_delete=models.PROTECT)
    property_name = models.CharField(max_length=25, help_text="Parameter name, e.g. 'mtot', 'separation'")
    error_type = models.CharField(max_length=20, choices=ERROR_TYPE_CHOICES, null=True, blank=True)
    error_upper = models.FloatField(null=True, blank=True)
    error_lower = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = 'binary_model_error'
        unique_together = [('binary_model', 'property_name')]
