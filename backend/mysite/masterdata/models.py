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


class GrowingGroup(models.Model):
    growing_group_code = models.CharField(
        max_length=2
    )

    growing_group_name = models.CharField(
        max_length=100
    )

    description = models.TextField(
        blank=True
    )

    def __str__(self):
        return self.growing_group_name

class Greenhouse(models.Model):
    greenhouse_code = models.CharField(
        max_length=5,
        unique=True
    )

    greenhouse_name = models.CharField(
        max_length=100
    )

    description = models.TextField(
        blank=True
    )

    def __str__(self):
        return self.greenhouse_code
class GreenhouseBed(models.Model):

    SIDE_CHOICES = [
        ("LEFT", "Left"),
        ("RIGHT", "Right"),
        ("A", "A"),
        ("B", "B"),
        ("C", "C"),
        ("D", "D"),
        ("E", "E"),
        ("F", "F"),
        ("G", "G"),
        ("H", "H"),
   
    ]

    greenhouse = models.ForeignKey(
        Greenhouse,
        on_delete=models.PROTECT
    )

    side = models.CharField(
        max_length=5,
        choices=SIDE_CHOICES
    )

    bed_no = models.IntegerField()

    valve = models.IntegerField()

    bay_no = models.IntegerField()

    mother_plants = models.IntegerField()

    control_valve = models.BooleanField(
        default=False
    )

    notes = models.TextField(
        blank=True
    )

    class Meta:
        unique_together = (
            "greenhouse",
            "bed_no",
        )

    def __str__(self):
        return f"{self.greenhouse.greenhouse_code} - Bed {self.bed_no}"
    
class Variety(models.Model):
    variety_code = models.CharField(
        max_length=5,
        unique=True
    )

    subgroup = models.ForeignKey(
        CropSubGroup,
        on_delete=models.PROTECT
    )

    growing_group = models.ForeignKey(
        GrowingGroup,
        on_delete=models.PROTECT,
    )

    variety_name = models.CharField(
        max_length=100
    )

    description = models.TextField(
        blank=True
    )

    def __str__(self):
        return self.variety_name