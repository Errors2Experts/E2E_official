from datetime import date, datetime, time
from decimal import Decimal

from django.contrib import admin
from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

MAX_COLUMN_WIDTH = 60
MIN_COLUMN_WIDTH = 12
FORMULA_PREFIXES = ("=", "+", "-", "@")


def prepare_excel_value(value):
    if value is None:
        return ""

    if isinstance(value, bool):
        return "Yes" if value else "No"

    if isinstance(value, datetime):
        return value.strftime("%d-%m-%Y %I:%M %p")

    if isinstance(value, date):
        return value.strftime("%d-%m-%Y")

    if isinstance(value, time):
        return value.strftime("%I:%M %p")

    if isinstance(value, (int, float, Decimal)):
        return value

    text = str(value)

    # Prevent user-provided text from being interpreted as an Excel formula.
    if text.startswith(FORMULA_PREFIXES):
        return f"'{text}"

    return text


@admin.action(description="📥 Export selected records to Excel")
def export_as_excel(modeladmin, request, queryset):
    workbook = Workbook()
    worksheet = workbook.active

    model = modeladmin.model
    worksheet.title = model._meta.verbose_name_plural.title()[:31]

    fields = [field for field in model._meta.fields if field.name != "id"]

    header_fill = PatternFill(
        start_color="1F4E78",
        end_color="1F4E78",
        fill_type="solid",
    )
    header_font = Font(
        bold=True,
        color="FFFFFF",
    )
    header_alignment = Alignment(
        horizontal="center",
        vertical="center",
    )

    for column_number, field in enumerate(fields, start=1):
        cell = worksheet.cell(
            row=1,
            column=column_number,
            value=field.verbose_name.title(),
        )
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_alignment

    for row_number, obj in enumerate(queryset, start=2):
        for column_number, field in enumerate(fields, start=1):
            value = getattr(obj, field.name)
            safe_value = prepare_excel_value(value)

            cell = worksheet.cell(
                row=row_number,
                column=column_number,
                value=safe_value,
            )
            cell.alignment = Alignment(
                vertical="top",
                wrap_text=True,
            )

    for column_cells in worksheet.columns:
        content_length = max(
            len(str(cell.value)) if cell.value is not None else 0
            for cell in column_cells
        )

        width = min(
            max(content_length + 2, MIN_COLUMN_WIDTH),
            MAX_COLUMN_WIDTH,
        )

        column_letter = get_column_letter(column_cells[0].column)
        worksheet.column_dimensions[column_letter].width = width

    worksheet.freeze_panes = "A2"
    worksheet.auto_filter.ref = worksheet.dimensions

    filename = f"{model._meta.model_name}_export.xlsx"

    response = HttpResponse(
        content_type=(
            "application/vnd.openxmlformats-officedocument." "spreadsheetml.sheet"
        )
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    workbook.save(response)
    return response
