import os

EMAIL_HERO_IMAGE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "assets",
    "emailImage.jpg",
)
EMAIL_HERO_OBJECT_POSITION = "right top"
EMAIL_HERO_CID = "vibora-hero-image"


def wrap_email_page(title: str, subtitle: str, body_html: str) -> str:
    return f"""
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
            .email-metrics-col {{
              width: 50%;
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
                    <p style="margin:8px 0 0; color:#ef6a84; font-size:14px;">{subtitle}</p>
                  </td>
                </tr>
                <tr>
                  <td class="email-hero-wrap" style="padding:0;">
                    <img class="email-hero-img" src="cid:{EMAIL_HERO_CID}" alt="ViboraInk" style="display:block; width:100%; height:auto; border:0;" />
                  </td>
                </tr>
                <tr>
                  <td style="padding:24px;">
                    {body_html}
                    <p style="margin:24px 0 0; font-size:12px; color:#9a9a9a; text-align:center;">
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
