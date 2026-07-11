from django.db import models
from django.core.exceptions import ValidationError

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

    @property
    def total_capacity(self):
        return sum(
            bed.mother_plants
            for bed in self.greenhousebed_set.all()
        )

    @property
    def occupied_capacity(self):
        return sum(
            bed.occupied_capacity
            for bed in self.greenhousebed_set.all()
        )

    @property
    def available_capacity(self):
        return (
            self.total_capacity -
            self.occupied_capacity
        )

    @property
    def utilization_percentage(self):
        if self.total_capacity == 0:
            return 0

        return round(
            (self.occupied_capacity / self.total_capacity) * 100,
            2
        )

    @property
    def occupied_beds(self):
        return sum(
            1
            for bed in self.greenhousebed_set.all()
            if bed.occupied_capacity > 0
        )

    @property
    def available_beds(self):
        return sum(
            1
            for bed in self.greenhousebed_set.all()
            if bed.available_capacity > 0
        )

    @property
    def active_varieties(self):
        varieties = set()

        for bed in self.greenhousebed_set.all():
            for allocation in bed.productionallocation_set.filter(
                status="IN_PRODUCTION"
            ):
                varieties.add(
                    allocation.variety_id
                )

        return len(varieties)

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

    @property
    def occupied_capacity(self):
        return sum(
            allocation.quantity
            for allocation in self.productionallocation_set.filter(
                status="IN_PRODUCTION"
            )
        )

    @property
    def available_capacity(self):
        return self.mother_plants - self.occupied_capacity

    @property
    def utilization_percentage(self):
        if self.mother_plants == 0:
            return 0

        return round(
            (self.occupied_capacity / self.mother_plants) * 100,
            2
        )

    @property
    def is_empty(self):
        return self.occupied_capacity == 0

    @property
    def is_full(self):
        return self.available_capacity == 0

    @property
    def active_allocations(self):
        return self.productionallocation_set.filter(
            status="IN_PRODUCTION"
        )

    @property
    def occupancy_details(self):
        allocations = self.productionallocation_set.filter(
            status="IN_PRODUCTION"
        )

        if not allocations.exists():
            return "EMPTY"

        return ", ".join(
            [
                f"{allocation.variety.variety_name} ({allocation.quantity})"
                for allocation in allocations
            ]
        )

    class Meta:
        unique_together = (
            "greenhouse",
            "side",
            "bed_no",
        )

    def __str__(self):
        return (
            f"{self.greenhouse.greenhouse_code} - "
            f"{self.side} - Bed {self.bed_no}"
        )

    class Meta:
        unique_together = (
            "greenhouse",
            "side",
            "bed_no",
        )

    def __str__(self):
        return (
            f"{self.greenhouse.greenhouse_code} - "
            f"{self.side} - Bed {self.bed_no}"
        )


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


class ProductionAllocation(models.Model):

    allocation_reference = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
    )

    STATUS_CHOICES = [
        ("IN_PRODUCTION", "In Production"),
        ("OUT_OF_PRODUCTION", "Out Of Production"),
    ]

    greenhouse_bed = models.ForeignKey(
        GreenhouseBed,
        on_delete=models.PROTECT
    )

    variety = models.ForeignKey(
        Variety,
        on_delete=models.PROTECT
    )

    quantity = models.IntegerField()

    start_date = models.DateField()

    end_date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="IN_PRODUCTION"
    )

    manual_override = models.BooleanField(
        default=False
    )

    notes = models.TextField(
        blank=True
    )

    @property
    def start_week(self):
        week = self.start_date.isocalendar().week
        year = self.start_date.isocalendar().year
        return f"{week}-{year}"

    @property
    def end_week(self):
        week = self.end_date.isocalendar().week
        year = self.end_date.isocalendar().year
        return f"{week}-{year}"

    def clean(self):

        occupied = self.greenhouse_bed.occupied_capacity

        if self.pk:
            try:
                old_record = ProductionAllocation.objects.get(
                    pk=self.pk
                )

                if old_record.status == "IN_PRODUCTION":
                    occupied -= old_record.quantity

            except ProductionAllocation.DoesNotExist:
                pass

        available = (
            self.greenhouse_bed.mother_plants -
            occupied
        )

        if self.quantity > available:
            raise ValidationError(
                {
                    "quantity": (
                        f"Allocation exceeds available capacity. "
                        f"Available Capacity: {available}. "
                        f"Requested Quantity: {self.quantity}."
                    )
                }
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.variety} - "
            f"{self.greenhouse_bed}"
        )