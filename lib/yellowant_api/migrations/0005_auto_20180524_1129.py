# Generated by Django 2.0.5 on 2018-05-24 11:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('yellowant_api', '0004_auto_20180524_1122'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Awsec2',
            new_name='ec2credentials',
        ),
    ]
