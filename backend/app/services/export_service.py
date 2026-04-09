from io import BytesIO

from openpyxl import Workbook


class ExportService:
    def build_gradebook_xlsx(self, rows: list[dict]) -> bytes:
        workbook = Workbook()
        sheet = workbook.active
        headers = ["Student Name", "Quizzes", "Assignments", "Projects", "Midsem", "Endsem", "Final Score"]
        sheet.append(headers)
        for row in rows:
            sheet.append([row.get(header, "") for header in headers])
        buffer = BytesIO()
        workbook.save(buffer)
        return buffer.getvalue()

