from django.db import models


class Crop(models.Model):
    crop_code = models.CharField(
        max_length=2
    )

    crop_name = models.CharField(
        max_length=100
    )

    description = models.TextField(
        blank=True
    )

    def __str__(self):
        return self.crop_name


class CropSubGroup(models.Model):
    subgroup_code = models.CharField(
        max_length=6,
        unique=True
    )

    subgroup_name = models.CharField(
        max_length=100
    )

    crop = models.ForeignKey(
        Crop,
        on_delete=models.PROTECT
    )

    description = models.TextField(
        blank=True
    )

    def __str__(self):
        return self.subgroup_name


class Variety(models.Model):
    variety_code = models.CharField(
        max_length=20,
        unique=True
    )

    subgroup = models.ForeignKey(
        CropSubGroup,
        on_delete=models.PROTECT
    )

    variety_name = models.CharField(
        max_length=100
    )

    description = models.TextField(
        blank=True
    )

    def __str__(self):
        return self.variety_name