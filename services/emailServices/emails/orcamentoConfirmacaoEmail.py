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
    valor_orcamento: int | None = None,
    dificuldade: str = "",
    to: str = "",
    subject: str = "Seu orcamento foi confirmado - ViboraInk",
) -> dict:
    safe_client_name = client_name.strip() if client_name else "Cliente"
    safe_valor = _format_currency(valor_orcamento)
    safe_dificuldade = dificuldade.strip() if dificuldade else "Nao informado"

    html_client_name = html.escape(safe_client_name)
    html_valor = html.escape(safe_valor)
    html_dificuldade = html.escape(safe_dificuldade)

    plain_text = (
        "ViboraInk - Orcamento confirmado\n\n"
        f"Ola, {safe_client_name}!\n\n"
        "Seu orcamento foi analisado e confirmado pela nossa equipe.\n\n"
        f"Valor do orcamento: {safe_valor}\n"
        f"Dificuldade estimada: {safe_dificuldade}\n\n"
        "Em breve entraremos em contato para alinhar os proximos passos "
        "e agendar sua tatuagem.\n\n"
        "Obrigado por escolher a ViboraInk!"
    )

    body_html = f"""
      <p style="margin:0 0 20px; font-size:16px; color:#f4f4f4; line-height:1.6;">
        Ola, <strong style="color:#ffffff;">{html_client_name}</strong>!
      </p>

      <p style="margin:0 0 20px; font-size:16px; color:#f4f4f4; line-height:1.6;">
        Seu orcamento foi analisado e confirmado pela nossa equipe. Confira os detalhes abaixo.
      </p>

      <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-bottom:12px;">
        <tr>
          <td class="email-metrics-col" style="padding:0 6px 12px 0; vertical-align:top;">
            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#171717; border:1px solid #45101b; border-radius:10px;">
              <tr>
                <td align="center" style="padding:22px 20px;">
                  <p style="margin:0 0 6px; font-size:12px; color:#ef6a84;">Valor do orcamento</p>
                  <p style="margin:0; font-size:28px; color:#ffffff; font-weight:bold;">{html_valor}</p>
                </td>
              </tr>
            </table>
          </td>
          <td class="email-metrics-col" style="padding:0 0 12px 6px; vertical-align:top;">
            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#171717; border:1px solid #45101b; border-radius:10px;">
              <tr>
                <td style="padding:22px 20px;">
                  <p style="margin:0 0 6px; font-size:12px; color:#ef6a84;">Dificuldade</p>
                  <p style="margin:0; font-size:20px; color:#ffffff; font-weight:bold;">{html_dificuldade}</p>
                </td>
              </tr>
            </table>
          </td>
        </tr>
      </table>

      <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-bottom:0; background:#171717; border:1px solid #45101b; border-radius:10px;">
        <tr>
          <td style="padding:18px 20px;">
            <p style="margin:0 0 8px; font-size:12px; letter-spacing:0.6px; text-transform:uppercase; color:#ef6a84;">
              Proximo passo
            </p>
            <p style="margin:0; font-size:15px; color:#e8e8e8; line-height:1.6;">
              Em breve entraremos em contato para alinhar os detalhes finais e agendar sua tatuagem.
            </p>
          </td>
        </tr>
      </table>
    """

    html_content = wrap_email_page(
        title="ViboraInk",
        subtitle="Orcamento confirmado",
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
        "to": to,
    }


def send(
    *,
    to: str,
    client_name: str = "",
    valor_orcamento: int | None = None,
    dificuldade: str = "",
    subject: str = "Seu orcamento foi confirmado - ViboraInk",
) -> str:
    payload = build(
        client_name=client_name,
        valor_orcamento=valor_orcamento,
        dificuldade=dificuldade,
        to=to,
        subject=subject,
    )
    return emailService.send_message(**payload)
