from datetime import date, timedelta
import re

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum

from masterdata.models import (
    Variety,
    Greenhouse,
)


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
        db_index=True,
    )

    file_name = models.CharField(
        max_length=255,
    )

    uploaded_file = models.FileField(
        upload_to="imports/",
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="UPLOADED",
        db_index=True,
    )

    imported_at = models.DateTimeField(
        auto_now_add=True,
    )

    notes = models.TextField(
        blank=True,
    )

    class Meta:
        ordering = ["-imported_at"]
        verbose_name = "Import Batch"
        verbose_name_plural = "Import Batches"

    def __str__(self):
        return self.batch_reference
class ImportedStickingPlanRow(models.Model):

    VALIDATION_CHOICES = [
        ("PENDING", "Pending"),
        ("VALID", "Valid"),
        ("INVALID", "Invalid"),
    ]

    BUFFER_SOURCE_CHOICES = [
        ("DEFAULT", "Default"),
        ("OVERRIDE", "Override"),
    ]

    import_batch = models.ForeignKey(
        ImportBatch,
        on_delete=models.CASCADE,
        related_name="rows",
    )

    row_number = models.IntegerField()

    variety_code = models.CharField(
        max_length=20,
        db_index=True,
    )

    variety_name = models.CharField(
        max_length=255,
        blank=True,
    )

    greenhouse_code = models.CharField(
        max_length=20,
        db_index=True,
    )

    sticking_week = models.CharField(
        max_length=10,
        db_index=True,
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

    # ==========================
    # BUFFER MANAGEMENT
    # ==========================

    buffer_override_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )

    override_reason = models.CharField(
        max_length=100,
        blank=True,
    )

    override_notes = models.TextField(
        blank=True,
    )

    applied_buffer_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    buffer_source = models.CharField(
        max_length=20,
        choices=BUFFER_SOURCE_CHOICES,
        default="DEFAULT",
    )

    target_quantity = models.IntegerField(
        default=0,
    )

    validation_status = models.CharField(
        max_length=20,
        choices=VALIDATION_CHOICES,
        default="PENDING",
        db_index=True,
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

    class Meta:
        ordering = ["row_number"]
        indexes = [
            models.Index(fields=["variety_code"]),
            models.Index(fields=["greenhouse_code"]),
            models.Index(fields=["sticking_week"]),
            models.Index(fields=["validation_status"]),
        ]

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
        try:
            week, year = self.sticking_week.split("-")

            date.fromisocalendar(
                int(year),
                int(week),
                1,
            )

            return True

        except (ValueError, TypeError):
            return False

    @property
    def valid_end_week(self):
        try:
            week, year = self.production_end_week.split("-")

            date.fromisocalendar(
                int(year),
                int(week),
                1,
            )

            return True

        except (ValueError, TypeError):
            return False

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
                f"Invalid Production End Week: "
                f"{self.production_end_week}"
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

    def calculate_urc(self):

        try:
            variety = Variety.objects.get(
                variety_code=self.variety_code
            )

            if self.urc_per_bag <= 0:
                self.urc_per_bag = (
                    variety.default_urc_per_bag
                )

        except Variety.DoesNotExist:

            if self.urc_per_bag <= 0:
                self.urc_per_bag = 2

    def calculate_buffer(self):

        try:
            variety = Variety.objects.get(
                variety_code=self.variety_code
            )

            default_buffer = (
                variety.default_buffer_percent
            )

        except Variety.DoesNotExist:
            default_buffer = 0

        if self.buffer_override_percent is not None:

            self.applied_buffer_percent = (
                self.buffer_override_percent
            )

            self.buffer_source = "OVERRIDE"

        else:

            self.applied_buffer_percent = (
                default_buffer
            )

            self.buffer_source = "DEFAULT"

    def calculate_target_quantity(self):

        self.target_quantity = round(
            self.planned_quantity
            * (
                1
                + (
                    float(self.applied_buffer_percent)
                    / 100
                )
            )
        )

    def clean(self):

        errors = {}

        if self.planned_quantity <= 0:
            errors["planned_quantity"] = (
                "Quantity must be greater than zero."
            )

        if self.urc_per_bag < 0:
            errors["urc_per_bag"] = (
                "URC Per Bag cannot be negative."
            )

        if not self.valid_sticking_week:
            errors["sticking_week"] = (
                "Invalid ISO week format."
            )

        if not self.valid_end_week:
            errors["production_end_week"] = (
                "Invalid ISO week format."
            )

        if errors:
            raise ValidationError(errors)

    def validate_row(self):

        self.calculate_urc()
        self.calculate_buffer()
        self.calculate_target_quantity()

        errors = self.validation_errors

        if errors:

            self.validation_status = "INVALID"

            self.validation_message = (
                "\n".join(errors)
            )

        else:

            self.validation_status = "VALID"

            self.validation_message = (
                "Validation Passed"
            )

        self.save()

    def save(self, *args, **kwargs):

        self.calculate_urc()
        self.calculate_buffer()
        self.calculate_target_quantity()

        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.import_batch.batch_reference}"
            f" - Row {self.row_number}"
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
        db_index=True,
    )

    season = models.CharField(
        max_length=100,
    )

    import_batch = models.ForeignKey(
        ImportBatch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sticking_plans",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="DRAFT",
        db_index=True,
    )

    notes = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Sticking Plan Header"
        verbose_name_plural = "Sticking Plan Headers"

    def generate_reference(self):

        year = date.today().year

        last_record = (
            StickingPlanHeader.objects
            .order_by("-id")
            .first()
        )

        sequence = (
            last_record.id + 1
            if last_record
            else 1
        )

        return (
            f"SP-"
            f"{year}-"
            f"{sequence:03d}"
        )

    def clean(self):

        if not self.season:
            raise ValidationError(
                {"season": "Season is required."}
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
        db_index=True,
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
        db_index=True,
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
        db_index=True,
    )

    notes = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = [
            "sticking_week",
            "greenhouse",
            "variety",
        ]
        indexes = [
            models.Index(fields=["greenhouse"]),
            models.Index(fields=["sticking_week"]),
            models.Index(fields=["status"]),
        ]

    @property
    def crop(self):
        return self.variety.subgroup.crop

    @property
    def growing_group(self):
        return self.variety.growing_group

    @property
    def target_quantity(self):
        return round(
            self.planned_quantity
            * (
                1
                + (
                    float(self.buffer_percentage)
                    / 100
                )
            )
        )

    @property
    def urc_needed(self):

        if self.urc_per_bag <= 0:
            return 0

        return (
            self.target_quantity
            + self.urc_per_bag
            - 1
        ) // self.urc_per_bag

    @property
    def greenhouse_capacity(self):
        return self.greenhouse.total_capacity

    @property
    def available_capacity(self):
        return self.greenhouse.available_capacity

    @property
    def exceeds_capacity(self):
        return (
            self.planned_quantity
            > self.available_capacity
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
                total=Sum(
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
            self.greenhouse_planned_quantity
            > self.greenhouse_capacity
        )

    @property
    def sticking_monday(self):

        try:

            week, year = (
                self.sticking_week.split("-")
            )

            return date.fromisocalendar(
                int(year),
                int(week),
                1,
            )

        except (
            ValueError,
            TypeError,
        ):
            return None

    @property
    def planting_monday(self):

        try:

            week, year = (
                self.planting_week.split("-")
            )

            return date.fromisocalendar(
                int(year),
                int(week),
                1,
            )

        except (
            ValueError,
            TypeError,
            AttributeError,
        ):
            return None

    @property
    def production_end_monday(self):

        try:

            week, year = (
                self.production_end_week.split("-")
            )

            return date.fromisocalendar(
                int(year),
                int(week),
                1,
            )

        except (
            ValueError,
            TypeError,
        ):
            return None

    def calculate_planting_week(self):

        week, year = (
            self.sticking_week.split("-")
        )

        sticking_date = (
            date.fromisocalendar(
                int(year),
                int(week),
                1,
            )
        )

        planting_date = (
            sticking_date
            + timedelta(weeks=4)
        )

        iso_year, iso_week, _ = (
            planting_date.isocalendar()
        )

        return (
            f"{iso_week:02d}"
            f"-{iso_year}"
        )

    def generate_reference(self):

        crop_code = (
            self.variety
            .subgroup
            .crop
            .crop_code
        )

        week, year = (
            self.sticking_week.split("-")
        )

        sequence = (
            StickingPlanLine.objects.filter(
                greenhouse=self.greenhouse,
                sticking_week=self.sticking_week,
            )
            .exclude(pk=self.pk)
            .count()
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

    def clean(self):

        errors = {}

        if self.planned_quantity <= 0:
            errors["planned_quantity"] = (
                "Quantity must be greater than zero."
            )

        if self.urc_per_bag <= 0:
            errors["urc_per_bag"] = (
                "URC Per Bag must be greater than zero."
            )

        if self.exceeds_capacity:
            errors["planned_quantity"] = (
                "Quantity exceeds available greenhouse capacity."
            )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):

        self.full_clean()

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
        related_name="allocation_proposals",
    )

    greenhouse = models.ForeignKey(
        Greenhouse,
        on_delete=models.PROTECT,
    )

    proposed_capacity = models.IntegerField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PROPOSED",
        db_index=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["greenhouse"]),
        ]

    def clean(self):

        if self.proposed_capacity <= 0:
            raise ValidationError(
                {
                    "proposed_capacity":
                    "Proposed capacity must be greater than zero."
                }
            )

    @property
    def available_greenhouse_capacity(self):
        return self.greenhouse.available_capacity

    @property
    def exceeds_greenhouse_capacity(self):
        return (
            self.proposed_capacity
            > self.greenhouse.available_capacity
        )

    def save(self, *args, **kwargs):

        self.full_clean()

        super().save(
            *args,
            **kwargs,
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
        related_name="bed_allocations",
    )

    bed = models.ForeignKey(
        "masterdata.GreenhouseBed",
        on_delete=models.PROTECT,
    )

    allocated_quantity = models.IntegerField()

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["bed"]

    def clean(self):

        if self.allocated_quantity <= 0:
            raise ValidationError(
                {
                    "allocated_quantity":
                    "Allocated quantity must be greater than zero."
                }
            )

    def save(self, *args, **kwargs):

        self.full_clean()

        super().save(
            *args,
            **kwargs,
        )

    def __str__(self):
        return (
            f"{self.bed}"
            f" - "
            f"{self.allocated_quantity}"
        )
class BufferHistory(models.Model):

    variety = models.ForeignKey(
        Variety,
        on_delete=models.CASCADE,
    )

    greenhouse = models.ForeignKey(
        Greenhouse,
        on_delete=models.CASCADE,
    )

    sticking_week = models.CharField(
        max_length=10,
        db_index=True,
    )

    demand_quantity = models.IntegerField()

    target_quantity = models.IntegerField()

    rooted_quantity = models.IntegerField(
        default=0,
    )

    loss_quantity = models.IntegerField(
        default=0,
    )

    loss_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    buffer_used = models.DecimalField(
        max_digits=5,
        decimal_places=2,
    )

    buffer_source = models.CharField(
        max_length=20,
        default="DEFAULT",
    )

    override_reason = models.CharField(
        max_length=100,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["sticking_week"]),
            models.Index(fields=["variety"]),
            models.Index(fields=["greenhouse"]),
        ]

    def clean(self):

        errors = {}

        if self.demand_quantity < 0:
            errors["demand_quantity"] = (
                "Demand quantity cannot be negative."
            )

        if self.target_quantity < 0:
            errors["target_quantity"] = (
                "Target quantity cannot be negative."
            )

        if self.rooted_quantity < 0:
            errors["rooted_quantity"] = (
                "Rooted quantity cannot be negative."
            )

        if self.buffer_used < 0:
            errors["buffer_used"] = (
                "Buffer used cannot be negative."
            )

        if errors:
            raise ValidationError(errors)

    def calculate_loss(self):

        self.loss_quantity = max(
            self.target_quantity
            - self.rooted_quantity,
            0,
        )

        if self.target_quantity > 0:

            self.loss_percent = round(
                (
                    self.loss_quantity
                    * 100
                )
                / self.target_quantity,
                2,
            )

        else:
            self.loss_percent = 0

    def save(self, *args, **kwargs):

        self.full_clean()

        self.calculate_loss()

        super().save(
            *args,
            **kwargs,
        )

    def __str__(self):

        return (
            f"{self.variety.variety_code}"
            f" - "
            f"{self.loss_percent}%"
        )