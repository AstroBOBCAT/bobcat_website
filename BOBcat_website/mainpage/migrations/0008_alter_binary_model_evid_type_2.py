# Generated by Django 4.0.4 on 2024-06-28 18:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mainpage', '0007_alter_binary_model_chirp_mass_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='binary_model',
            name='evid_type_2',
            field=models.CharField(blank=True, max_length=50),
        ),
    ]
