import os
import base64
import html
from pathlib import Path
from email.message import EmailMessage
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
TOKEN_PATH = BASE_DIR / "token.json"
CREDENTIALS_PATH = BASE_DIR / "credentials.json"

EMAIL_TO = os.getenv("EMAIL_TO")
EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_HERO_IMAGE = os.path.join(
    os.path.dirname(__file__),
    "assets",
    "emailImage.jpg",
)
# Desktop: JPG quadrado; cabeça/olho no canto superior direito — "right top" alinha o recorte a essa área.
# Ajuste fino só se precisar: ex. "82% 12%" (direita + pouco abaixo do topo do arquivo).
EMAIL_HERO_OBJECT_POSITION = "right top"

SCOPES = ['https://www.googleapis.com/auth/gmail.send']


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


def _format_currency(cents: int | None) -> str:
    if cents is None:
        return "Nao informado"
    reais = cents / 100
    formatted = f"{reais:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"


def send_email(
    tattoo_description: str = "",
    form_link: str = "",
    client_name: str = "",
    subject: str = "Novo aviso de orçamento - ViboraInk",
    dificuldade_ia: str = "",
    estimativa_valor: int | None = None,
    justificativa_ia: str = "",
):
    creds = get_gmail_credentials(allow_interactive=False)
    service = build('gmail', 'v1', credentials=creds)
    
    message = EmailMessage()
    safe_client_name = client_name.strip() if client_name else "Cliente"
    safe_description = tattoo_description.strip() if tattoo_description else "Sem descrição enviada."
    safe_form_link = form_link.strip() if form_link else "Link do formulário ainda não informado."
    safe_dificuldade = dificuldade_ia.strip() if dificuldade_ia else "Nao informado"
    safe_estimativa = _format_currency(estimativa_valor)
    safe_justificativa = justificativa_ia.strip() if justificativa_ia else "Nao informado"

    html_client_name = html.escape(safe_client_name)
    html_description = html.escape(safe_description)
    html_form_link = html.escape(safe_form_link)
    html_dificuldade = html.escape(safe_dificuldade)
    html_estimativa = html.escape(safe_estimativa)
    html_justificativa = html.escape(safe_justificativa)

    plain_text = (
        "ViboraInk - Novo aviso de orçamento\n\n"
        f"Cliente: {safe_client_name}\n"
        f"Descrição da tatuagem: {safe_description}\n"
        f"Dificuldade (IA): {safe_dificuldade}\n"
        f"Estimativa (IA): {safe_estimativa}\n"
        f"Justificativa (IA): {safe_justificativa}\n"
        f"Link do formulário: {safe_form_link}\n"
    )

    html_content = f"""
    <html>
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <style type="text/css">
          .email-hero-wrap {{
            padding: 0;
          }}
          .email-hero-img {{
            display: block;
            width: 100%;
            height: auto;
            border: 0;
          }}
          @media (min-width: 601px) {{
            .email-hero-wrap {{
              max-height: 260px;
              overflow: hidden;
              line-height: 0;
            }}
            .email-hero-img {{
              width: 100% !important;
              height: 260px !important;
              object-fit: cover !important;
              object-position: {EMAIL_HERO_OBJECT_POSITION} !important;
            }}
          }}
        </style>
      </head>
      <body style="margin:0; padding:0; background-color:#0b0b0b; font-family:Arial, sans-serif; color:#f4f4f4;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="padding:24px 12px;">
          <tr>
            <td align="center">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:620px; background-color:#141414; border:1px solid #45101b; border-radius:12px; overflow:hidden;">
                <tr>
                  <td style="padding:20px 24px; background:#171717; border-bottom:2px solid #b10f2e;">
                    <h1 style="margin:0; font-size:24px; color:#ffffff;">ViboraInk</h1>
                    <p style="margin:8px 0 0; color:#ef6a84; font-size:14px;">Novo aviso de orçamento</p>
                  </td>
                </tr>
                <tr>
                  <td class="email-hero-wrap" style="padding:0;">
                    <img class="email-hero-img" src="cid:vibora-hero-image" alt="ViboraInk" style="display:block; width:100%; height:auto; border:0;" />
                  </td>
                </tr>
                <tr>
                  <td style="padding:24px;">
                    <p style="margin:0 0 16px; font-size:16px; color:#f4f4f4;">
                      Um novo pedido de orçamento foi recebido.
                    </p>
                    <p style="margin:0 0 8px; font-size:14px; color:#ef6a84;">Cliente</p>
                    <p style="margin:0 0 20px; font-size:16px; color:#ffffff;">{html_client_name}</p>

                    <p style="margin:0 0 8px; font-size:14px; color:#ef6a84;">Descrição da tatuagem</p>
                    <p style="margin:0 0 20px; font-size:15px; color:#e8e8e8; line-height:1.5;">{html_description}</p>

                    <p style="margin:0 0 8px; font-size:14px; color:#ef6a84;">Dificuldade (IA)</p>
                    <p style="margin:0 0 20px; font-size:15px; color:#e8e8e8; line-height:1.5;">{html_dificuldade}</p>

                    <p style="margin:0 0 8px; font-size:14px; color:#ef6a84;">Estimativa (IA)</p>
                    <p style="margin:0 0 20px; font-size:15px; color:#e8e8e8; line-height:1.5;">{html_estimativa}</p>

                    <p style="margin:0 0 8px; font-size:14px; color:#ef6a84;">Justificativa (IA)</p>
                    <p style="margin:0 0 20px; font-size:15px; color:#e8e8e8; line-height:1.5;">{html_justificativa}</p>

                    <p style="margin:0 0 8px; font-size:14px; color:#ef6a84;">Formulário para tatuadora</p>
                    <p style="margin:0 0 24px; font-size:15px; color:#e8e8e8; line-height:1.5;">
                      <a href="{html_form_link}" style="color:#ff3b5c; text-decoration:none;">{html_form_link}</a>
                    </p>

                    <p style="margin:0; font-size:12px; color:#9a9a9a;">
                      Este e-mail foi gerado automaticamente pelo sistema da ViboraInk.
                    </p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
        </table>
      </body>
    </html>
    """

    message.set_content(plain_text)
    message.add_alternative(html_content, subtype='html')

    if os.path.exists(EMAIL_HERO_IMAGE):
        with open(EMAIL_HERO_IMAGE, "rb") as image_file:
            image_data = image_file.read()
            message.get_payload()[1].add_related(
                image_data,
                maintype="image",
                subtype="jpeg",
                cid="vibora-hero-image",
            )

    message['To'] = EMAIL_TO
    message['From'] = EMAIL_FROM
    message['Subject'] = subject

    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    create_message = {'raw': encoded_message}
    
    send_message = service.users().messages().send(userId="me", body=create_message).execute()
    print(f'Enviado! ID: {send_message["id"]}')

if __name__ == '__main__':
    get_gmail_credentials(allow_interactive=True)
    send_email()
    print("E-mail de teste enviado com sucesso.")