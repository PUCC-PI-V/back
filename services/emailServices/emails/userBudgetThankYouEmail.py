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
    estimativa_valor: int | None = None,
    to: str = "",
    subject: str = "Recebemos seu orçamento - ViboraInk",
) -> dict:
    safe_client_name = client_name.strip() if client_name else "Cliente"
    safe_estimativa = _format_currency(estimativa_valor)

    html_client_name = html.escape(safe_client_name)
    html_estimativa = html.escape(safe_estimativa)

    plain_text = (
        "ViboraInk - Obrigado pelo seu orçamento!\n\n"
        f"Olá, {safe_client_name}!\n\n"
        "Recebemos seu pedido de orçamento com sucesso. "
        "Em breve a tatuadora entrará em contato com você para dar continuidade ao atendimento.\n\n"
        f"Estimativa de valor (IA): {safe_estimativa}\n\n"
        "Aviso importante: o valor acima é apenas uma estimativa gerada automaticamente "
        "e não representa o valor final da tatuagem. O orçamento definitivo será "
        "informado pela tatuadora após a análise do seu projeto.\n\n"
        "Obrigado por escolher a ViboraInk!"
    )

    body_html = f"""
      <p style="margin:0 0 20px; font-size:16px; color:#f4f4f4; line-height:1.6;">
        Olá, <strong style="color:#ffffff;">{html_client_name}</strong>!
      </p>

      <p style="margin:0 0 20px; font-size:16px; color:#f4f4f4; line-height:1.6;">
        Obrigado por enviar seu pedido de orçamento na ViboraInk. Recebemos tudo certinho
        e já estamos analisando os detalhes da sua tatuagem.
      </p>

      <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-bottom:20px; background:#171717; border:1px solid #45101b; border-radius:10px;">
        <tr>
          <td style="padding:18px 20px;">
            <p style="margin:0 0 8px; font-size:12px; letter-spacing:0.6px; text-transform:uppercase; color:#ef6a84;">
              Próximo passo
            </p>
            <p style="margin:0; font-size:15px; color:#e8e8e8; line-height:1.6;">
              Em breve a tatuadora entrará em contato com você para alinhar os detalhes
              e dar continuidade ao seu atendimento.
            </p>
          </td>
        </tr>
      </table>

      <p style="margin:0 0 10px; font-size:12px; letter-spacing:0.6px; text-transform:uppercase; color:#ef6a84;">
        Estimativa de valor
      </p>
      <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-bottom:20px; background:#171717; border:1px solid #45101b; border-radius:10px;">
        <tr>
          <td align="center" style="padding:22px 20px;">
            <p style="margin:0 0 6px; font-size:12px; color:#ef6a84;">Valor estimado</p>
            <p style="margin:0; font-size:28px; color:#ffffff; font-weight:bold;">{html_estimativa}</p>
          </td>
        </tr>
      </table>

      <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-bottom:0; background:#1a1214; border:1px solid #6b1a2a; border-radius:10px;">
        <tr>
          <td style="padding:16px 18px;">
            <p style="margin:0 0 8px; font-size:12px; letter-spacing:0.6px; text-transform:uppercase; color:#ef6a84;">
              Aviso importante
            </p>
            <p style="margin:0; font-size:14px; color:#d4d4d4; line-height:1.6;">
              Este valor é <strong style="color:#ffffff;">apenas uma estimativa</strong> gerada
              automaticamente pelo sistema e <strong style="color:#ffffff;">não representa o valor
              real ou final</strong> da tatuagem. O orçamento definitivo será informado pela
              tatuadora após a análise completa do seu projeto.
            </p>
          </td>
        </tr>
      </table>
    """

    html_content = wrap_email_page(
        title="ViboraInk",
        subtitle="Obrigado pelo seu orçamento",
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
    estimativa_valor: int | None = None,
    subject: str = "Recebemos seu orçamento - ViboraInk",
) -> str:
    payload = build(
        client_name=client_name,
        estimativa_valor=estimativa_valor,
        to=to,
        subject=subject,
    )
    return emailService.send_message(**payload)


if __name__ == "__main__":
    import os as _os

    emailService.get_gmail_credentials(allow_interactive=True)
    send(
        to=_os.getenv("EMAIL_TO", ""),
        client_name="Maria Silva",
        estimativa_valor=180000,
    )
    print("E-mail de agradecimento enviado com sucesso.")
