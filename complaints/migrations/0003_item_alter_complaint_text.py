# Generated by Django 4.2.17 on 2025-01-15 20:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('complaints', '0002_remove_complaint_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Item',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
            ],
        ),
        migrations.AlterField(
            model_name='complaint',
            name='text',
            field=models.CharField(max_length=140),
        ),
    ]
