# Generated by Django 4.2.17 on 2025-02-05 19:03

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('complaints', '0010_remove_complaint_cluster_complaint_clusters_field_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='complaint',
            old_name='clusters_field',
            new_name='cluster',
        ),
    ]
