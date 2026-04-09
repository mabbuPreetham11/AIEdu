class EmailService:
    async def send_email(self, to_email: str, subject: str, html_content: str) -> None:
        del to_email, subject, html_content
        return None

