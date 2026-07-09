from django.db import models


class Crop(models.Model):
    crop_code = models.CharField(max_length=10, unique=True)
    crop_name = models.CharField(max_length=100)

    def __str__(self):
        return self.crop_name