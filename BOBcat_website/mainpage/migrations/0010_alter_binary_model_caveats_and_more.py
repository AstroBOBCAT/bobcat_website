# Generated by Django 4.0.4 on 2024-06-28 18:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mainpage', '0009_alter_binary_model_evid_type_2'),
    ]

    operations = [
        migrations.AlterField(
            model_name='binary_model',
            name='caveats',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='binary_model',
            name='evid_type_1',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='binary_model',
            name='evid_type_1_note',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='binary_model',
            name='evid_type_1_waveband',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='binary_model',
            name='evid_type_2_note',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='binary_model',
            name='evid_type_2_waveband',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='binary_model',
            name='evid_type_3',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='binary_model',
            name='evid_type_3_note',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='binary_model',
            name='evid_type_3_waveband',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='binary_model',
            name='evid_type_4',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='binary_model',
            name='evid_type_4_note',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='binary_model',
            name='evid_type_4_waveband',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='binary_model',
            name='ext_projects',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='binary_model',
            name='paper_link',
            field=models.URLField(blank=True, max_length=300, null=True),
        ),
        migrations.AlterField(
            model_name='binary_model',
            name='source_name',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='binary_model',
            name='summary',
            field=models.TextField(blank=True, null=True),
        ),
    ]
