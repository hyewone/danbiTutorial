from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    team = models.ForeignKey('Team', on_delete=models.CASCADE)

class Task(models.Model):
    id = models.AutoField(primary_key=True)
    create_user = models.ForeignKey(User, on_delete=models.CASCADE)
    team = models.ForeignKey('Team', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    content = models.TextField()
    is_complete = models.BooleanField(default=False)
    completed_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

class SubTask(models.Model):
    id = models.AutoField(primary_key=True)
    team = models.ForeignKey('Team', on_delete=models.CASCADE)
    is_complete = models.BooleanField(default=False)
    completed_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)

class Team(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
