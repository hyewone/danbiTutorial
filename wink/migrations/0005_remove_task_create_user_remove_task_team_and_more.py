# Generated by Django 4.2.6 on 2023-10-28 21:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wink', '0004_alter_subtask_task'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='task',
            name='create_user',
        ),
        migrations.RemoveField(
            model_name='task',
            name='team',
        ),
        migrations.DeleteModel(
            name='SubTask',
        ),
        migrations.DeleteModel(
            name='Task',
        ),
    ]
