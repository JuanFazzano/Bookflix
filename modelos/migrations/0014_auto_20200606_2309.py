# Generated by Django 3.0.5 on 2020-06-06 23:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('modelos', '0013_trailer_titulo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='trailer',
            name='libro_asociado',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='modelos.Libro'),
        ),
    ]
