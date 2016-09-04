# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-09-04 00:31
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('modified_on', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(help_text='Task name', max_length=300, verbose_name='Name')),
                ('description', models.TextField(blank=True, help_text='Task description', max_length=2000, verbose_name='Description')),
                ('priority', models.PositiveIntegerField(choices=[(1, b'Lowest'), (2, b'Low'), (3, b'Medium'), (4, b'High'), (5, b'Highest')], default=3, help_text='Task priority', verbose_name='Priority')),
                ('status', models.PositiveIntegerField(choices=[(1, b'Todo'), (2, b'In Progress'), (3, b'Done')], default=1, help_text='Task status', verbose_name='Status')),
                ('assignee', models.ForeignKey(blank=True, help_text='User that is assigned to the task', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='assigned_tasks', to=settings.AUTH_USER_MODEL, verbose_name='Assignee')),
            ],
            options={
                'ordering': ['created_on'],
            },
        ),
        migrations.CreateModel(
            name='TaskCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True, max_length=300)),
            ],
            options={
                'ordering': ['created_on'],
            },
        ),
        migrations.CreateModel(
            name='TaskEventLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('event', models.PositiveIntegerField(choices=[(1, b'Created'), (2, b'Edited'), (3, b'Status Changed'), (4, b'Assigned')], default=1, help_text='The event logged for this task', verbose_name='Event')),
                ('description', models.TextField(blank=True, help_text='Event description', max_length=2000, verbose_name='Description')),
                ('task', models.ForeignKey(help_text='The task for this event', on_delete=django.db.models.deletion.CASCADE, related_name='events', to='tasks.Task', verbose_name='Task')),
                ('user', models.ForeignKey(help_text='The user that triggered the event', on_delete=django.db.models.deletion.CASCADE, related_name='task_events', to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
            options={
                'ordering': ['created_on'],
            },
        ),
        migrations.AddField(
            model_name='task',
            name='category',
            field=models.ForeignKey(help_text='Task category', on_delete=django.db.models.deletion.PROTECT, related_name='tasks', to='tasks.TaskCategory', verbose_name='category'),
        ),
        migrations.AddField(
            model_name='task',
            name='reporter',
            field=models.ForeignKey(help_text='User that created the task', on_delete=django.db.models.deletion.PROTECT, related_name='created_tasks', to=settings.AUTH_USER_MODEL, verbose_name='Reporter'),
        ),
    ]
