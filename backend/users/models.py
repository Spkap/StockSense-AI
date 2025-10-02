from django.db import models
from django.contrib.auth.models import AbstractUser


# Create your models here.
class User(AbstractUser):
    firebase_uid  = models.CharField(max_length=255, unique=True, db_index=True) 
    picture = models.URLField(blank=True, null=True)
    email_verified = models.BooleanField(default=False, blank=True, null=True)

    def __str__(self):
        return self.email
    

