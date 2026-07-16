from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mainpage', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='binarymodel',
            old_name='rm_orb_period',
            new_name='orb_period',
        ),
        migrations.RenameField(
            model_name='binarymodel',
            old_name='rm_orb_period_epoch',
            new_name='orb_period_epoch',
        ),
    ]
