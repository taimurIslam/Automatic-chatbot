from django.db import models

#Create your models here.

class Questions(models.Model):
    class_name = models.CharField(max_length=50, unique=False)
    sentence   = models.CharField(max_length=1000, unique=False)

class Answer(models.Model):
    class_name = models.CharField(max_length=50, unique=False)
    answer     = models.CharField(max_length=1000, unique=False)