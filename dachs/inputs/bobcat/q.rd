<?xml version="1.0" encoding="utf-8"?>

<!--
  BOBcat Resource Descriptor for DACHS
  =====================================
  Exposes Django-managed tables in the PostgreSQL "public" schema via IVOA TAP.

  All tables are declared with onDisk="True" — DACHS reads them without
  creating or modifying them.  Column types match Django's PostgreSQL types
  (FloatField → double precision, etc.).

  After any schema change, re-run:
      gavo imp /var/gavo/inputs/bobcat/q.rd
      gavo pub /var/gavo/inputs/bobcat/q.rd
-->

<resource schema="bobcat" resdir=".">

  <!-- ── Catalog metadata ───────────────────────────────────────────── -->
  <meta name="title">BOBcat – Binary Object Black Hole Catalog</meta>
  <meta name="description">
    BOBcat is a catalog of supermassive binary black hole (SMBHB) candidates
    with observed orbital parameters, gravitational wave properties, and
    multiwavelength evidence classifications.
  </meta>
  <meta name="subject">Gravitational waves; binary black holes; active galactic nuclei</meta>
  <meta name="creator.name">BOBcat Team</meta>
  <meta name="type">Catalog</meta>
  <meta name="contentLevel">Research</meta>

  <!-- ── candidate ──────────────────────────────────────────────────── -->
  <table id="candidate" onDisk="True" adql="True">
    <meta name="description">
      SMBHB candidate sources.  Each row is a unique sky object identified
      by its NED-recognized name.
    </meta>

    <column name="name"
            type="text"
            ucd="meta.id;meta.main"
            description="NED-recognized source identifier (primary key)"/>

    <column name="jra"
            type="double precision"
            ucd="pos.eq.ra;meta.main"
            unit="deg"
            description="Right ascension J2000 in decimal degrees"/>

    <column name="jdec"
            type="double precision"
            ucd="pos.eq.dec;meta.main"
            unit="deg"
            description="Declination J2000 in decimal degrees"/>

    <column name="redshift"
            type="double precision"
            ucd="src.redshift"
            description="Spectroscopic redshift"
            required="False"/>

    <column name="lum_dist"
            type="double precision"
            ucd="phys.distance"
            unit="Mpc"
            description="Luminosity distance in Mpc"
            required="False"/>

    <column name="rating"
            type="smallint"
            ucd="meta.code.qual"
            description="Source quality ranking (positive = stronger evidence)"
            required="False"/>

    <column name="created_at"
            type="timestamp"
            ucd="time.creation"
            description="Record creation timestamp"
            required="False"/>
  </table>

  <!-- ── bib ────────────────────────────────────────────────────────── -->
  <table id="bib" onDisk="True" adql="True">
    <meta name="description">
      Bibliographic references.  Each row is an ADS/SciX bibcode for a paper
      that provides one or more binary models.
    </meta>

    <column name="bib_id"
            type="text"
            ucd="meta.bib.bibcode;meta.main"
            description="19-character ADS/SciX bibcode (primary key)"/>

    <column name="doi"
            type="text"
            ucd="meta.ref.doi"
            description="Digital Object Identifier"
            required="False"/>

    <column name="title"
            type="text"
            ucd="meta.title"
            description="Paper title"
            required="False"/>

    <column name="year"
            type="smallint"
            ucd="time.epoch;meta.bib"
            description="Publication year"
            required="False"/>

    <column name="citations"
            type="smallint"
            ucd="meta.number"
            description="Citation count as of updated_at"
            required="False"/>

    <column name="created_at"
            type="timestamp"
            ucd="time.creation"
            required="False"/>

    <column name="updated_at"
            type="timestamp"
            ucd="time.update"
            required="False"/>
  </table>

  <!-- ── binary_model ───────────────────────────────────────────────── -->
  <table id="binary_model" onDisk="True" adql="True">
    <meta name="description">
      Binary black hole orbital models.  Each row is one published model for
      one candidate, linking the source (candidate.name) to the paper (bib.bib_id).
      Mass quantities are stored as log10(value / M_sun).
    </meta>

    <column name="binary_model_id"
            type="bigint"
            ucd="meta.id;meta.main"
            description="Auto-generated primary key"/>

    <column name="candidate_id"
            type="text"
            ucd="meta.id.cross"
            description="Source name — foreign key to candidate.name"/>

    <column name="bib_id"
            type="text"
            ucd="meta.bib.bibcode"
            description="ADS bibcode — foreign key to bib.bib_id"/>

    <column name="eccentricity"
            type="double precision"
            ucd="src.orbital.eccentricity"
            description="Orbital eccentricity (0 = circular)"
            required="False"/>

    <column name="m1"
            type="double precision"
            ucd="phys.mass"
            unit="log(Msun)"
            description="log10 of the primary BH mass in solar masses"
            required="False"/>

    <column name="m2"
            type="double precision"
            ucd="phys.mass"
            unit="log(Msun)"
            description="log10 of the secondary BH mass in solar masses"
            required="False"/>

    <column name="mtot"
            type="double precision"
            ucd="phys.mass"
            unit="log(Msun)"
            description="log10 of the total mass (m1+m2) in solar masses"
            required="False"/>

    <column name="mc"
            type="double precision"
            ucd="phys.mass"
            unit="log(Msun)"
            description="log10 of the chirp mass in solar masses"
            required="False"/>

    <column name="mu"
            type="double precision"
            ucd="phys.mass"
            unit="log(Msun)"
            description="log10 of the reduced mass in solar masses"
            required="False"/>

    <column name="q"
            type="double precision"
            ucd="phys.mass.ratio"
            description="Mass ratio m2/m1, constrained to (0, 1]"
            required="False"/>

    <column name="inclination"
            type="double precision"
            ucd="src.orbital.inclination"
            unit="deg"
            description="Orbital inclination in degrees"
            required="False"/>

    <column name="semimajor_axis"
            type="double precision"
            ucd="src.orbital.smAxis"
            unit="pc"
            description="Semimajor axis in parsecs"
            required="False"/>

    <column name="separation"
            type="double precision"
            ucd="pos.distance"
            unit="pc"
            description="Projected separation in parsecs"
            required="False"/>

    <!-- Note: the DB columns were renamed from rm_orb_period /
         rm_orb_period_epoch (the "rm" prefix had no documented meaning)
         to orb_period / orb_period_epoch by the 0002 migration. -->
    <column name="orb_period"
            type="double precision"
            ucd="time.period;src.orbital"
            unit="yr"
            description="Earth-frame orbital period in years"
            required="False"/>

    <column name="orb_period_epoch"
            type="double precision"
            ucd="time.epoch"
            unit="d"
            description="Reference epoch for the orbital period (MJD)"
            required="False"/>

    <column name="gw_strain"
            type="double precision"
            ucd="phys.strain"
            description="Gravitational wave characteristic strain h at Earth (circular orbit)"
            required="False"/>

    <column name="gw_inspiral_timescale"
            type="double precision"
            ucd="time.duration"
            unit="s"
            description="GR inspiral timescale to coalescence in seconds (circular orbit)"
            required="False"/>

    <column name="summary"
            type="text"
            ucd="meta.note"
            description="Brief description of the binary model"
            required="False"/>

    <column name="caveats"
            type="text"
            ucd="meta.note"
            description="Known limitations or assumptions of the model"
            required="False"/>

    <column name="ext_proj"
            type="text"
            ucd="meta.note"
            description="Related external project or survey"
            required="False"/>

    <column name="created_at"
            type="timestamp"
            ucd="time.creation"
            required="False"/>
  </table>

  <!-- ── obs_period ─────────────────────────────────────────────────── -->
  <table id="obs_period" onDisk="True" adql="True">
    <meta name="description">
      Individual period measurements for a binary model, optionally
      tagged with a waveband.
    </meta>

    <column name="obs_period_id"
            type="bigint"
            ucd="meta.id;meta.main"
            description="Auto-generated primary key"/>

    <column name="binary_model_id"
            type="bigint"
            ucd="meta.id.cross"
            description="Foreign key to binary_model.binary_model_id"/>

    <column name="waveband"
            type="text"
            ucd="instr.bandpass"
            description="Observational waveband (radio, infrared, optical, UV, x-ray, gamma-ray)"
            required="False"/>

    <column name="value"
            type="double precision"
            ucd="time.period;src.orbital"
            unit="yr"
            description="Measured period in years"/>

    <column name="epoch"
            type="double precision"
            ucd="time.epoch"
            unit="d"
            description="Reference epoch in MJD"/>
  </table>

  <!-- ── binary_model_error ─────────────────────────────────────────── -->
  <table id="binary_model_error" onDisk="True" adql="True">
    <meta name="description">
      Per-parameter measurement uncertainties for a binary model.
    </meta>

    <column name="binary_model_error_id"
            type="bigint"
            ucd="meta.id;meta.main"
            description="Auto-generated primary key"/>

    <column name="binary_model_id"
            type="bigint"
            ucd="meta.id.cross"
            description="Foreign key to binary_model.binary_model_id"/>

    <column name="property_name"
            type="text"
            ucd="meta.id"
            description="Name of the parameter this error applies to (e.g. mtot, separation)"/>

    <column name="error_type"
            type="text"
            ucd="meta.code.error"
            description="Error characterisation: Assumed, Upper limit, Lower limit, Gaussian, Two-sided, Representative"
            required="False"/>

    <column name="error_upper"
            type="double precision"
            ucd="stat.error;stat.max"
            description="Upper uncertainty (same units as the parameter)"
            required="False"/>

    <column name="error_lower"
            type="double precision"
            ucd="stat.error;stat.min"
            description="Lower uncertainty (same units as the parameter)"
            required="False"/>
  </table>

  <!-- ── evidence_subcategory ───────────────────────────────────────── -->
  <table id="evidence_subcategory" onDisk="True" adql="True">
    <meta name="description">
      Controlled vocabulary of evidence types used to classify binary models.
    </meta>

    <column name="evidence_subcategory_id"
            type="smallint"
            ucd="meta.id;meta.main"
            description="Auto-generated primary key"/>

    <column name="category"
            type="text"
            ucd="meta.code.class"
            description="Top-level evidence category (e.g. continuum_variability, gravitational_wave)"/>

    <column name="name"
            type="text"
            ucd="meta.note"
            description="Specific subcategory name within the category"/>
  </table>

  <!-- ── model_evidence ─────────────────────────────────────────────── -->
  <table id="model_evidence" onDisk="True" adql="True">
    <meta name="description">
      Links a binary model to one evidence subcategory.
    </meta>

    <column name="model_evidence_id"
            type="bigint"
            ucd="meta.id;meta.main"
            description="Auto-generated primary key"/>

    <column name="binary_model_id"
            type="bigint"
            ucd="meta.id.cross"
            description="Foreign key to binary_model.binary_model_id"/>

    <column name="subcategory_id"
            type="smallint"
            ucd="meta.id.cross"
            description="Foreign key to evidence_subcategory.evidence_subcategory_id"/>
  </table>

  <!-- Without <data><make>, gavo imp validates the RD but doesn't
       register tables in dc.tablemeta, so ADQL queries fail to locate them. -->
  <data id="d">
    <make table="candidate"/>
    <make table="bib"/>
    <make table="binary_model"/>
    <make table="obs_period"/>
    <make table="binary_model_error"/>
    <make table="evidence_subcategory"/>
    <make table="model_evidence"/>
  </data>

</resource>
