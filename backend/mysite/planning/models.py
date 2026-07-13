from django.db import models
from masterdata.models import Variety, Greenhouse
import re


class ImportBatch(models.Model):

    STATUS_CHOICES = [
        ("UPLOADED", "Uploaded"),
        ("VALIDATED", "Validated"),
        ("IMPORTED", "Imported"),
        ("FAILED", "Failed"),
    ]

    batch_reference = models.CharField(
        max_length=50,
        unique=True
    )

    file_name = models.CharField(
        max_length=255
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="UPLOADED"
    )

    imported_at = models.DateTimeField(
        auto_now_add=True
    )

    notes = models.TextField(
        blank=True
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
        related_name="rows"
    )

    row_number = models.IntegerField()

    variety_code = models.CharField(
        max_length=20
    )

    variety_name = models.CharField(
        max_length=255,
        blank=True
    )

    greenhouse_code = models.CharField(
        max_length=20
    )

    sticking_week = models.CharField(
        max_length=10
    )

    production_end_week = models.CharField(
        max_length=10
    )

    planned_quantity = models.IntegerField(
        default=0
    )

    urc_per_bag = models.IntegerField(
        default=0
    )

    validation_status = models.CharField(
        max_length=20,
        choices=VALIDATION_CHOICES,
        default="PENDING"
    )

    validation_message = models.TextField(
        blank=True
    )

    raw_data = models.JSONField(
        null=True,
        blank=True
    )

    imported_at = models.DateTimeField(
        auto_now_add=True
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

        if not re.match(
            pattern,
            self.sticking_week
        ):
            return False

        week, year = self.sticking_week.split("-")

        week = int(week)

        return 1 <= week <= 53

    @property
    def valid_end_week(self):

        pattern = r"^\d{1,2}-\d{4}$"

        if not re.match(
            pattern,
            self.production_end_week
        ):
            return False

        week, year = self.production_end_week.split("-")

        week = int(week)

        return 1 <= week <= 53

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
                f"Invalid Sticking Week: "
                f"{self.sticking_week}"
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