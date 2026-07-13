from django.core.management.base import BaseCommand
import pandas as pd

from masterdata.models import (
    Variety,
    CropSubGroup,
    GrowingGroup,
)


class Command(BaseCommand):

    help = "Import varieties from Excel file"

    def handle(self, *args, **kwargs):

        file_path = "tblVarieties.xlsx"

        df = pd.read_excel(file_path)

        created = 0
        skipped = 0
        failed = 0

        for _, row in df.iterrows():

            try:

                variety_code = str(
                    row["VarietyCode"]
                ).strip()

                variety_name = str(
                    row["VarietyName"]
                ).strip()

                subgroup_name = str(
                    row["CropName"]
                ).strip()

                grouping = str(
                    row["Grouping"]
                ).strip()

                if (
                    grouping == "Group Not Found"
                    or grouping == ""
                    or grouping.lower() == "nan"
                ):
                    grouping = "TD"

                subgroup = CropSubGroup.objects.get(
                    subgroup_name=subgroup_name
                )

                growing_group = GrowingGroup.objects.get(
                    growing_group_code=grouping
                )

                if Variety.objects.filter(
                    variety_code=variety_code
                ).exists():

                    skipped += 1
                    continue

                Variety.objects.create(
                    variety_code=variety_code,
                    variety_name=variety_name,
                    subgroup=subgroup,
                    growing_group=growing_group,
                )

                created += 1

            except Exception as e:

                failed += 1

                self.stdout.write(
                    self.style.ERROR(
                        f"{variety_code}: {e}"
                    )
                )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Created: {created}"
            )
        )

        self.stdout.write(
            self.style.WARNING(
                f"Skipped: {skipped}"
            )
        )

        self.stdout.write(
            self.style.ERROR(
                f"Failed: {failed}"
            )
        )