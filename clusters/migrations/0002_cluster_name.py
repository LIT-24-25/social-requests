# Generated by Django 4.2.17 on 2025-02-14 07:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clusters', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='cluster',
            name='name',
            field=models.CharField(default='Unnamed Complaint', max_length=100),
        ),
    ]
