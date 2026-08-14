def build_welcome_email(*, email: str, full_name: str, role: str) -> dict[str, str]:
    return {
        "to": email.strip().lower(),
        "subject": "Welcome to Whitfield WMS",
        "body": (
            f"Hi {full_name.strip()}, your Whitfield WMS account is ready. "
            f"Your role is {role}. Please sign in with the temporary password shared by the admin."
        ),
    }

