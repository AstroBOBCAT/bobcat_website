# Generated by Django 4.0.4 on 2024-05-16 15:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mainpage', '0002_alter_source_dec_alter_source_ra'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='source',
            name='ADS_bibcode',
        ),
    ]
