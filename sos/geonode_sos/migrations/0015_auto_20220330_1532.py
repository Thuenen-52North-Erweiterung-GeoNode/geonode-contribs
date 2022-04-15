# Generated by Django 2.2.24 on 2022-03-30 15:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('geonode_sos', '0014_auto_20220330_1531'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sensorresponsible',
            name='extracted_arcrole',
            field=models.CharField(choices=[('manufacturerName', 'manufacturerName'), ('owner', 'owner'), ('pointOfContact', 'pointOfContact')], max_length=255, null=True),
        ),
    ]