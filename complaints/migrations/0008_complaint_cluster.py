# Generated by Django 4.2.17 on 2025-01-28 20:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('complaints', '0007_delete_point_complaint_email_complaint_x_complaint_y'),
    ]

    operations = [
        migrations.AddField(
            model_name='complaint',
            name='cluster',
            field=models.CharField(default='Unnamed Complaint', max_length=100),
        ),
    ]
