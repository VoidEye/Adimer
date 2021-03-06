# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-12-17 09:42
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Connection',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('time', models.DateTimeField()),
                ('status', models.SmallIntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Device',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip', models.GenericIPAddressField()),
                ('name', models.CharField(max_length=50, unique=True)),
                ('is_active', models.BooleanField(default=False)),
                ('last_connection', models.DateTimeField(null=True)),
                ('device_id', models.CharField(max_length=255, null=True, unique=True)),
                ('fireBase_token', models.CharField(max_length=255, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='File',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to=b'slides')),
                ('isMP4', models.BooleanField()),
                ('duration', models.FloatField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Group',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Localization',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('shop_name', models.CharField(max_length=100)),
                ('city', models.CharField(max_length=30)),
            ],
        ),
        migrations.CreateModel(
            name='Presentation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('duration', models.DurationField(default=datetime.timedelta(0))),
                ('start', models.DateTimeField()),
                ('end', models.DateTimeField()),
                ('group', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.Group')),
            ],
        ),
        migrations.CreateModel(
            name='Slide',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('duration', models.DurationField(null=True)),
                ('order', models.IntegerField()),
                ('playlist', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.Presentation')),
                ('slide', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.File')),
            ],
        ),
        migrations.AddField(
            model_name='presentation',
            name='slides',
            field=models.ManyToManyField(null=True, through='core.Slide', to='core.File'),
        ),
        migrations.AddField(
            model_name='group',
            name='playlist',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='core.Presentation'),
        ),
        migrations.AddField(
            model_name='device',
            name='group',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.Group'),
        ),
        migrations.AddField(
            model_name='device',
            name='localization',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.Localization'),
        ),
        migrations.AddField(
            model_name='connection',
            name='device',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.Device'),
        ),
    ]
