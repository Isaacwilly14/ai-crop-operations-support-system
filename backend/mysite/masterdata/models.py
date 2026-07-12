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

    WATER_REQUIREMENT_CHOICES = [
        ("HIGH", "High"),
        ("MEDIUM", "Medium"),
        ("LOW", "Low"),
    ]

    SENSITIVITY_CHOICES = [
        ("LOW", "Low"),
        ("HIGH", "High"),
        ("VERY_HIGH", "Very High"),
    ]

    PLACEMENT_CHOICES = [
        ("PREFER_EDGE", "Prefer Edge"),
        ("EDGE_ALLOWED", "Edge Allowed"),
        ("AVOID_EDGE", "Avoid Edge"),
    ]

    growing_group_code = models.CharField(
        max_length=2,
        unique=True
    )

    growing_group_name = models.CharField(
        max_length=100
    )

    water_requirement = models.CharField(
        max_length=10,
        choices=WATER_REQUIREMENT_CHOICES,
        null=True,
        blank=True,
    )

    sensitivity_level = models.CharField(
        max_length=15,
        choices=SENSITIVITY_CHOICES,
        null=True,
        blank=True,
    )

    placement_preference = models.CharField(
        max_length=20,
        choices=PLACEMENT_CHOICES,
        null=True,
        blank=True,
    )

    edge_placement_allowed = models.BooleanField(
        default=False
    )

    color_code = models.CharField(
        max_length=7,
        null=True,
        blank=True,
    )

    description = models.TextField(
        blank=True
    )

    def compatibility_with(
        self,
        other_group_code
    ):

        current_code = self.growing_group_code

        if current_code == other_group_code:
            return "EXCELLENT"

        current_letter = current_code[0]
        current_family = current_code[1]

        other_letter = other_group_code[0]
        other_family = other_group_code[1]

        if current_letter == other_letter:

            if current_family == other_family:
                return "EXCELLENT"

            if abs(
                int(current_family) -
                int(other_family)
            ) == 1:
                return "ACCEPTABLE"

            return "CONDITIONAL"

        family_rules = {
            ("A", "B"): "GOOD",
            ("A", "C"): "ACCEPTABLE",
            ("A", "D"): "AVOID",
            ("A", "E"): "HIGHLY_AVOID",

            ("B", "C"): "GOOD",
            ("B", "D"): "ACCEPTABLE",
            ("B", "E"): "AVOID",

            ("C", "D"): "GOOD",
            ("C", "E"): "ACCEPTABLE",

            ("D", "E"): "GOOD",
        }

        key = tuple(sorted(
            [current_letter, other_letter]
        ))

        return family_rules.get(
            key,
            "AVOID"
        )

    def __str__(self):
        return self.growing_group_code
class Greenhouse(models.Model):

    greenhouse_code = models.CharField(
        max_length=5,
        unique=True
    )

    greenhouse_name = models.CharField(
        max_length=100
    )

    edge_zone_beds = models.PositiveIntegerField(
        default=5
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
            (
                self.occupied_capacity /
                self.total_capacity
            ) * 100,
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

    @property
    def available_sides(self):
        return sorted(
            list(
                self.greenhousebed_set.values_list(
                    "side",
                    flat=True
                ).distinct()
            )
        )

    @property
    def layout_summary(self):

        result = {}

        for side in self.available_sides:

            result[side] = self.greenhousebed_set.filter(
                side=side
            ).order_by(
                "bed_no"
            )

        return result

    def recommend_beds(
        self,
        growing_group_code,
        required_quantity
    ):

        recommendations = []

        for bed in self.greenhousebed_set.all():

            if bed.available_capacity <= 0:
                continue

            recommendations.append(
                {
                    "bed": bed,
                    "available": bed.available_capacity,
                    "score": bed.recommendation_for_group(
                        growing_group_code
                    ),
                }
            )

        recommendations.sort(
            key=lambda x: x["score"],
            reverse=True
        )

        selected = []

        accumulated_quantity = 0

        for item in recommendations:

            selected.append(item)

            accumulated_quantity += item["available"]

            if accumulated_quantity >= required_quantity:
                break

        return selected

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
    def is_edge_bed(self):

        total_beds = GreenhouseBed.objects.filter(
            greenhouse=self.greenhouse,
            side=self.side
        ).count()

        edge_size = self.greenhouse.edge_zone_beds

        return (
            self.bed_no <= edge_size
            or
            self.bed_no > (total_beds - edge_size)
        )

    @property
    def valve_growing_groups(self):

        beds = GreenhouseBed.objects.filter(
            greenhouse=self.greenhouse,
            valve=self.valve
        )

        groups = set()

        for bed in beds:
            for allocation in bed.productionallocation_set.filter(
                status="IN_PRODUCTION"
            ):
                groups.add(
                    allocation.variety.growing_group.growing_group_code
                )

        return sorted(groups)

    def valve_compatibility_score(
        self,
        incoming_group_code
    ):

        if not self.valve_growing_groups:
            return 1000

        from masterdata.models import GrowingGroup

        try:
            incoming_group = GrowingGroup.objects.get(
                growing_group_code=incoming_group_code
            )
        except GrowingGroup.DoesNotExist:
            return 0

        score = 0

        for existing_group in self.valve_growing_groups:

            compatibility = incoming_group.compatibility_with(
                existing_group
            )

            if compatibility == "EXCELLENT":
                score += 1000

            elif compatibility == "GOOD":
                score += 750

            elif compatibility == "ACCEPTABLE":
                score += 300

            elif compatibility == "CONDITIONAL":
                score += 100

            elif compatibility == "AVOID":
                score -= 750

            elif compatibility == "HIGHLY_AVOID":
                score -= 1500

        return score

    def recommendation_for_group(
        self,
        growing_group_code
    ):

        score = self.available_capacity

        if growing_group_code.startswith("A"):
            if self.is_edge_bed:
                score += 1000

        elif growing_group_code.startswith("B"):
            if self.is_edge_bed:
                score += 500

        elif growing_group_code.startswith("C"):
            if self.is_edge_bed:
                score += 250

        elif growing_group_code.startswith("D"):
            if self.is_edge_bed:
                score -= 1000

        elif growing_group_code.startswith("E"):
            if self.is_edge_bed:
                score -= 1500

        score += self.valve_compatibility_score(
            growing_group_code
        )

        return score

    def recommendation_explanation(
        self,
        growing_group_code
    ):

        explanation = []

        explanation.append(
            f"Available Capacity: {self.available_capacity}"
        )

        if self.is_edge_bed:

            if growing_group_code.startswith("A"):
                explanation.append(
                    "Edge Bed Preferred For A Groups"
                )

            elif growing_group_code.startswith("B"):
                explanation.append(
                    "Edge Bed Suitable For B Groups"
                )

            elif growing_group_code.startswith("C"):
                explanation.append(
                    "Edge Bed Acceptable For C Groups"
                )

            elif growing_group_code.startswith("D"):
                explanation.append(
                    "Edge Bed Not Recommended For D Groups"
                )

            elif growing_group_code.startswith("E"):
                explanation.append(
                    "Edge Bed Not Recommended For E Groups"
                )

        if self.valve_growing_groups:

            explanation.append(
                f"Valve Groups: {', '.join(self.valve_growing_groups)}"
            )

        explanation.append(
            f"Final Score: "
            f"{self.recommendation_for_group(growing_group_code)}"
        )

        return explanation

    @property
    def recommendation_score(self):

        score = self.available_capacity

        if self.is_edge_bed:
            score += 500

        return score

    @property
    def allocation_priority(self):

        if self.available_capacity == 0:
            return "NOT AVAILABLE"

        if self.available_capacity >= 1500:
            return "HIGH"

        if self.available_capacity >= 750:
            return "MEDIUM"

        return "LOW"

    @property
    def is_empty(self):
        if self.occupied_capacity == 0:
            return "EMPTY"

        return "OCCUPIED"

    @property
    def is_full(self):
        if self.available_capacity == 0:
            return "FULL"

        return "AVAILABLE"

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

    @property
    def compatible_growing_groups(self):

        groups = set()

        for allocation in self.productionallocation_set.filter(
            status="IN_PRODUCTION"
        ):
            groups.add(
                allocation.variety.growing_group.growing_group_code
            )

        return ", ".join(sorted(groups))

    @property
    def bed_summary(self):
        return (
            f"Capacity={self.mother_plants} | "
            f"Occupied={self.occupied_capacity} | "
            f"Available={self.available_capacity}"
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

    @property
    def greenhouse(self):
        return self.greenhouse_bed.greenhouse

    @property
    def side(self):
        return self.greenhouse_bed.side

    @property
    def bed_number(self):
        return self.greenhouse_bed.bed_no

    @property
    def variety_code(self):
        return self.variety.variety_code

    @property
    def variety_name(self):
        return self.variety.variety_name

    @property
    def growing_group_code(self):
        return self.variety.growing_group.growing_group_code

    @property
    def color_code(self):
        return self.variety.growing_group.color_code

    @property
    def layout_row(self):
        return {
            "bed": self.bed_number,
            "variety_code": self.variety_code,
            "variety_name": self.variety_name,
            "quantity": self.quantity,
            "group": self.growing_group_code,
            "color": self.color_code,
            "side": self.side,
        }

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
            f"{self.variety.variety_code} - "
            f"{self.variety.variety_name}"
        )