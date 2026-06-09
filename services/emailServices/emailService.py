import base64
from pathlib import Path
from email.message import EmailMessage
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from dotenv import load_dotenv
import os

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
TOKEN_PATH = BASE_DIR / "token.json"
CREDENTIALS_PATH = BASE_DIR / "credentials.json"

EMAIL_TO = os.getenv("EMAIL_TO")
EMAIL_FROM = os.getenv("EMAIL_FROM")

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def _save_token(creds: Credentials) -> None:
    TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")


def get_gmail_credentials(*, allow_interactive: bool = False) -> Credentials:
    creds = None

    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            _save_token(creds)
            return creds
        except Exception:
            TOKEN_PATH.unlink(missing_ok=True)
            raise RuntimeError(
                "Gmail: token expirado ou revogado. Rode na raiz do projeto: "
                "python services/emailServices/emailService.py"
            )

    if not allow_interactive:
        raise RuntimeError(
            "Gmail: autenticacao necessaria. Rode na raiz do projeto: "
            "python services/emailServices/emailService.py"
        )

    if not CREDENTIALS_PATH.exists():
        raise FileNotFoundError(
            f"credentials.json nao encontrado em {CREDENTIALS_PATH}"
        )

    flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
    creds = flow.run_local_server(port=0)
    _save_token(creds)
    return creds


def send_message(
    *,
    subject: str,
    plain_text: str,
    html_content: str,
    to: str | None = None,
    from_email: str | None = None,
    inline_images: list[dict] | None = None,
) -> str:
    creds = get_gmail_credentials(allow_interactive=False)
    service = build("gmail", "v1", credentials=creds)

    message = EmailMessage()
    message.set_content(plain_text)
    message.add_alternative(html_content, subtype="html")

    for image in inline_images or []:
        if not os.path.exists(image["path"]):
            continue
        with open(image["path"], "rb") as image_file:
            message.get_payload()[1].add_related(
                image_file.read(),
                maintype=image.get("maintype", "image"),
                subtype=image.get("subtype", "jpeg"),
                cid=image["cid"],
            )

    message["To"] = to or EMAIL_TO
    message["From"] = from_email or EMAIL_FROM
    message["Subject"] = subject

    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    response = (
        service.users()
        .messages()
        .send(userId="me", body={"raw": encoded_message})
        .execute()
    )
    message_id = response["id"]
    print(f"Enviado! ID: {message_id}")
    return message_id


if __name__ == "__main__":
    get_gmail_credentials(allow_interactive=True)
    print("Gmail autenticado com sucesso.")
