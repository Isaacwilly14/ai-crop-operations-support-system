from datetime import date, timedelta
import re

from django.db import models

from masterdata.models import Variety, Greenhouse


class ImportBatch(models.Model):

    STATUS_CHOICES = [
        ("UPLOADED", "Uploaded"),
        ("VALIDATED", "Validated"),
        ("IMPORTED", "Imported"),
        ("FAILED", "Failed"),
    ]

    batch_reference = models.CharField(
        max_length=50,
        unique=True,
    )

    file_name = models.CharField(
    max_length=255
)

    uploaded_file = models.FileField(
    upload_to="imports/",
    null=True,
    blank=True
)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="UPLOADED",
    )

    imported_at = models.DateTimeField(
        auto_now_add=True,
    )

    notes = models.TextField(
        blank=True,
    )

    def __str__(self):
        return self.batch_reference


class ImportedStickingPlanRow(models.Model):

    VALIDATION_CHOICES = [
        ("PENDING", "Pending"),
        ("VALID", "Valid"),
        ("INVALID", "Invalid"),
    ]

    import_batch = models.ForeignKey(
        ImportBatch,
        on_delete=models.CASCADE,
        related_name="rows",
    )

    row_number = models.IntegerField()

    variety_code = models.CharField(
        max_length=20,
    )

    variety_name = models.CharField(
        max_length=255,
        blank=True,
    )

    greenhouse_code = models.CharField(
        max_length=20,
    )

    sticking_week = models.CharField(
        max_length=10,
    )

    production_end_week = models.CharField(
        max_length=10,
    )

    planned_quantity = models.IntegerField(
        default=0,
    )

    urc_per_bag = models.IntegerField(
        default=0,
    )

    validation_status = models.CharField(
        max_length=20,
        choices=VALIDATION_CHOICES,
        default="PENDING",
    )

    validation_message = models.TextField(
        blank=True,
    )

    raw_data = models.JSONField(
        null=True,
        blank=True,
    )

    imported_at = models.DateTimeField(
        auto_now_add=True,
    )

    @property
    def variety_exists(self):
        return Variety.objects.filter(
            variety_code=self.variety_code
        ).exists()

    @property
    def greenhouse_exists(self):
        return Greenhouse.objects.filter(
            greenhouse_code=self.greenhouse_code
        ).exists()

    @property
    def valid_sticking_week(self):
        pattern = r"^\d{1,2}-\d{4}$"

        if not re.match(pattern, self.sticking_week):
            return False

        week, year = self.sticking_week.split("-")

        return 1 <= int(week) <= 53

    @property
    def valid_end_week(self):
        pattern = r"^\d{1,2}-\d{4}$"

        if not re.match(
            pattern,
            self.production_end_week,
        ):
            return False

        week, year = self.production_end_week.split("-")

        return 1 <= int(week) <= 53

    @property
    def quantity_valid(self):
        return self.planned_quantity > 0

    @property
    def urc_valid(self):
        return self.urc_per_bag > 0

    @property
    def validation_errors(self):
        errors = []

        if not self.variety_exists:
            errors.append(
                f"Unknown Variety: {self.variety_code}"
            )

        if not self.greenhouse_exists:
            errors.append(
                f"Unknown Greenhouse: {self.greenhouse_code}"
            )

        if not self.valid_sticking_week:
            errors.append(
                f"Invalid Sticking Week: {self.sticking_week}"
            )

        if not self.valid_end_week:
            errors.append(
                f"Invalid Production End Week: {self.production_end_week}"
            )

        if not self.quantity_valid:
            errors.append(
                "Quantity must be greater than zero"
            )

        if not self.urc_valid:
            errors.append(
                "URC Per Bag must be greater than zero"
            )

        return errors

    def validate_row(self):
        errors = self.validation_errors

        if errors:
            self.validation_status = "INVALID"
            self.validation_message = "\n".join(errors)
        else:
            self.validation_status = "VALID"
            self.validation_message = "Validation Passed"

        self.save()

    def __str__(self):
        return (
            f"{self.import_batch.batch_reference} "
            f"- Row {self.row_number}"
        )


class StickingPlanHeader(models.Model):

    STATUS_CHOICES = [
        ("DRAFT", "Draft"),
        ("APPROVED", "Approved"),
        ("ALLOCATED", "Allocated"),
        ("COMPLETED", "Completed"),
    ]

    reference = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
    )

    season = models.CharField(
        max_length=100,
    )

    import_batch = models.ForeignKey(
        ImportBatch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="DRAFT",
    )

    notes = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def generate_reference(self):

        year = date.today().year

        sequence = (
            StickingPlanHeader.objects.count()
            + 1
        )

        return (
            f"SP-"
            f"{year}-"
            f"{sequence:03d}"
        )

    def save(self, *args, **kwargs):

        if not self.reference:
            self.reference = (
                self.generate_reference()
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return self.reference

class StickingPlanLine(models.Model):

    STATUS_CHOICES = [
        ("PLANNED", "Planned"),
        ("ALLOCATED", "Allocated"),
        ("PRODUCED", "Produced"),
    ]

    header = models.ForeignKey(
        StickingPlanHeader,
        on_delete=models.CASCADE,
        related_name="lines",
    )

    reference = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
    )

    variety = models.ForeignKey(
        Variety,
        on_delete=models.PROTECT,
    )

    greenhouse = models.ForeignKey(
        Greenhouse,
        on_delete=models.PROTECT,
    )

    sticking_week = models.CharField(
        max_length=10,
    )

    planting_week = models.CharField(
        max_length=10,
        blank=True,
    )

    planting_week_override = models.BooleanField(
        default=False,
    )

    production_end_week = models.CharField(
        max_length=10,
    )

    planned_quantity = models.IntegerField()

    buffer_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=5.00,
    )

    urc_per_bag = models.IntegerField(
        default=0,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PLANNED",
    )

    notes = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    @property
    def crop(self):
        return self.variety.subgroup.crop

    @property
    def growing_group(self):
        return self.variety.growing_group

    @property
    def urc_needed(self):
        buffer_qty = (
            self.planned_quantity *
            float(self.buffer_percentage) / 100
        )

        return round(
            self.planned_quantity +
            buffer_qty
        )

    @property
    def greenhouse_capacity(self):
        return self.greenhouse.total_capacity

    @property
    def available_capacity(self):
        return self.greenhouse.available_capacity

    @property
    def exceeds_capacity(self):
        return (
            self.planned_quantity >
            self.greenhouse.available_capacity
        )

    @property
    def greenhouse_planned_quantity(self):
        return (
            StickingPlanLine.objects.filter(
                greenhouse=self.greenhouse,
                status="PLANNED",
            )
            .exclude(pk=self.pk)
            .aggregate(
                total=models.Sum(
                    "planned_quantity"
                )
            )["total"]
            or 0
        ) + self.planned_quantity

    @property
    def remaining_capacity(self):
        return (
            self.greenhouse_capacity
            - self.greenhouse_planned_quantity
        )

    @property
    def overbooked_quantity(self):
        if self.remaining_capacity >= 0:
            return 0

        return abs(
            self.remaining_capacity
        )

    @property
    def greenhouse_overbooked(self):
        return (
            self.greenhouse_planned_quantity >
            self.greenhouse_capacity
        )

    @property
    def sticking_monday(self):
        try:
            week, year = self.sticking_week.split("-")

            return date.fromisocalendar(
                int(year),
                int(week),
                1,
            )
        except (ValueError, TypeError):
            return None

    @property
    def planting_monday(self):
        try:
            week, year = self.planting_week.split("-")

            return date.fromisocalendar(
                int(year),
                int(week),
                1,
            )
        except (ValueError, TypeError):
            return None

    @property
    def production_end_monday(self):
        try:
            week, year = self.production_end_week.split("-")

            return date.fromisocalendar(
                int(year),
                int(week),
                1,
            )
        except (ValueError, TypeError):
            return None

    def calculate_planting_week(self):
        week, year = self.sticking_week.split("-")

        sticking_date = date.fromisocalendar(
            int(year),
            int(week),
            1,
        )

        planting_date = (
            sticking_date +
            timedelta(weeks=4)
        )

        iso_year, iso_week, _ = (
            planting_date.isocalendar()
        )

        return f"{iso_week}-{iso_year}"

    def generate_reference(self):
        crop_code = (
            self.variety.subgroup.crop.crop_code
        )

        week, year = self.sticking_week.split("-")

        sequence = (
            StickingPlanLine.objects.filter(
                greenhouse=self.greenhouse,
                sticking_week=self.sticking_week,
            ).count()
            + 1
        )

        return (
            f"SP-"
            f"{crop_code}-"
            f"{self.greenhouse.greenhouse_code}-"
            f"{week}-"
            f"{year}-"
            f"{sequence:03d}"
        )

    def save(self, *args, **kwargs):
        if (
            not self.planting_week
            or not self.planting_week_override
        ):
            self.planting_week = (
                self.calculate_planting_week()
            )

        if not self.reference:
            self.reference = (
                self.generate_reference()
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return self.reference
class AllocationProposal(models.Model):

    STATUS_CHOICES = [
        ("PROPOSED", "Proposed"),
        ("ACCEPTED", "Accepted"),
        ("REJECTED", "Rejected"),
    ]

    sticking_plan_line = models.ForeignKey(
        StickingPlanLine,
        on_delete=models.CASCADE,
        related_name="allocation_proposals"
    )

    greenhouse = models.ForeignKey(
        Greenhouse,
        on_delete=models.PROTECT
    )

    proposed_capacity = models.IntegerField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PROPOSED"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return (
            f"{self.sticking_plan_line.reference}"
            f" -> "
            f"{self.greenhouse.greenhouse_code}"
        )
class BedAllocation(models.Model):

    allocation = models.ForeignKey(
        AllocationProposal,
        on_delete=models.CASCADE,
        related_name="bed_allocations"
    )

    bed = models.ForeignKey(
        "masterdata.GreenhouseBed",
        on_delete=models.PROTECT
    )

    allocated_quantity = models.IntegerField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return (
            f"{self.bed}"
            f" - "
            f"{self.allocated_quantity}"
        )