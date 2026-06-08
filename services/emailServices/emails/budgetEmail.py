import html
import os

from services.emailServices import emailService
from services.emailServices.templates.layout import (
    EMAIL_HERO_CID,
    EMAIL_HERO_IMAGE,
    wrap_email_page,
)


def _format_currency(cents: int | None) -> str:
    if cents is None:
        return "Nao informado"
    reais = cents / 100
    formatted = f"{reais:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"


def build(
    client_name: str = "",
    tattoo_description: str = "",
    form_link: str = "",
    dificuldade_ia: str = "",
    estimativa_valor: int | None = None,
    justificativa_ia: str = "",
    subject: str = "Novo aviso de orçamento - ViboraInk",
) -> dict:
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

    body_html = f"""
      <p style="margin:0 0 20px; font-size:16px; color:#f4f4f4; line-height:1.5;">
        Um novo pedido de orçamento foi recebido e já passou pela análise da IA.
      </p>

      <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-bottom:20px; background:#171717; border:1px solid #45101b; border-radius:10px;">
        <tr>
          <td style="padding:16px 18px;">
            <p style="margin:0 0 6px; font-size:12px; letter-spacing:0.6px; text-transform:uppercase; color:#ef6a84;">Cliente</p>
            <p style="margin:0; font-size:18px; color:#ffffff; font-weight:bold;">{html_client_name}</p>
          </td>
        </tr>
      </table>

      <p style="margin:0 0 10px; font-size:12px; letter-spacing:0.6px; text-transform:uppercase; color:#ef6a84;">Descrição da tatuagem</p>
      <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-bottom:20px; border-left:3px solid #b10f2e; background:#171717; border-radius:0 10px 10px 0;">
        <tr>
          <td style="padding:14px 16px;">
            <p style="margin:0; font-size:15px; color:#e8e8e8; line-height:1.6;">{html_description}</p>
          </td>
        </tr>
      </table>

      <p style="margin:0 0 10px; font-size:12px; letter-spacing:0.6px; text-transform:uppercase; color:#ef6a84;">Análise da IA</p>
      <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-bottom:12px;">
        <tr>
          <td class="email-metrics-col" style="padding:0 6px 12px 0; vertical-align:top;">
            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#171717; border:1px solid #45101b; border-radius:10px;">
              <tr>
                <td style="padding:14px 16px;">
                  <p style="margin:0 0 6px; font-size:12px; color:#ef6a84;">Dificuldade</p>
                  <p style="margin:0; font-size:17px; color:#ffffff; font-weight:bold;">{html_dificuldade}</p>
                </td>
              </tr>
            </table>
          </td>
          <td class="email-metrics-col" style="padding:0 0 12px 6px; vertical-align:top;">
            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#171717; border:1px solid #45101b; border-radius:10px;">
              <tr>
                <td style="padding:14px 16px;">
                  <p style="margin:0 0 6px; font-size:12px; color:#ef6a84;">Estimativa</p>
                  <p style="margin:0; font-size:17px; color:#ffffff; font-weight:bold;">{html_estimativa}</p>
                </td>
              </tr>
            </table>
          </td>
        </tr>
      </table>

      <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-bottom:24px; background:#171717; border:1px solid #45101b; border-radius:10px;">
        <tr>
          <td style="padding:14px 16px;">
            <p style="margin:0 0 6px; font-size:12px; color:#ef6a84;">Justificativa</p>
            <p style="margin:0; font-size:15px; color:#e8e8e8; line-height:1.6;">{html_justificativa}</p>
          </td>
        </tr>
      </table>

      <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-bottom:0; background:#171717; border:1px solid #45101b; border-radius:10px;">
        <tr>
          <td align="center" style="padding:20px 18px;">
            <p style="margin:0 0 12px; font-size:14px; color:#ef6a84;">Revisar orçamento na plataforma</p>
            <a href="{html_form_link}" style="display:inline-block; padding:12px 22px; background:#b10f2e; color:#ffffff; text-decoration:none; font-size:15px; font-weight:bold; border-radius:8px;">
              Abrir formulário
            </a>
            <p style="margin:14px 0 0; font-size:12px; color:#9a9a9a; line-height:1.5; word-break:break-all;">
              {html_form_link}
            </p>
          </td>
        </tr>
      </table>
    """

    html_content = wrap_email_page(
        title="ViboraInk",
        subtitle="Novo aviso de orçamento",
        body_html=body_html,
    )

    inline_images = []
    if os.path.exists(EMAIL_HERO_IMAGE):
        inline_images.append(
            {
                "path": EMAIL_HERO_IMAGE,
                "cid": EMAIL_HERO_CID,
                "maintype": "image",
                "subtype": "jpeg",
            }
        )

    return {
        "subject": subject,
        "plain_text": plain_text,
        "html_content": html_content,
        "inline_images": inline_images,
    }


def send(**kwargs) -> str:
    payload = build(**kwargs)
    return emailService.send_message(**payload)


if __name__ == "__main__":
    emailService.get_gmail_credentials(allow_interactive=True)
    send(
        client_name="Cliente Teste",
        tattoo_description="Leao geometrico com blackwork",
        form_link="http://localhost:8080/admin/calculate/1",
        dificuldade_ia="Alta",
        estimativa_valor=250000,
        justificativa_ia="Estilo complexo e area dificil.",
    )
    print("E-mail de orçamento enviado com sucesso.")
