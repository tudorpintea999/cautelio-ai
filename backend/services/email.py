import os
import httpx


def send_welcome_email(to_email: str, api_key: str) -> bool:
    resend_key = os.environ.get("RESEND_API_KEY", "")
    if not resend_key:
        return False

    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Your Cautelio API key</title>
</head>
<body style="margin:0;padding:0;background:#0b1320;font-family:Georgia,serif;color:#e8e4d9;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0b1320;padding:48px 0;">
    <tr>
      <td align="center">
        <table width="560" cellpadding="0" cellspacing="0"
               style="background:#101a2a;border:1px solid #1e2d42;border-radius:4px;overflow:hidden;">

          <!-- Header -->
          <tr>
            <td style="padding:32px 40px 24px;border-bottom:1px solid #1e2d42;">
              <p style="margin:0;font-size:11px;letter-spacing:0.2em;color:#c4a35a;font-family:Georgia,serif;">
                &sect; CAUTELIO AI
              </p>
              <h1 style="margin:10px 0 0;font-size:26px;font-weight:normal;color:#e8e4d9;letter-spacing:0.05em;">
                Your subscription is active.
              </h1>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:32px 40px;">
              <p style="margin:0 0 24px;font-size:15px;line-height:1.7;color:#8a96aa;">
                Below is your personal API key. Keep it private — it's your access credential to the extension.
              </p>

              <!-- Key block -->
              <div style="background:#0b1320;border:1px solid #1e2d42;border-left:3px solid #c4a35a;
                          border-radius:3px;padding:20px 24px;margin:0 0 32px;">
                <p style="margin:0 0 8px;font-size:9px;letter-spacing:0.2em;color:#4a5a72;font-family:sans-serif;">
                  API KEY
                </p>
                <p style="margin:0;font-size:14px;letter-spacing:0.06em;color:#c4a35a;
                           word-break:break-all;font-family:monospace;">
                  {api_key}
                </p>
              </div>

              <!-- Steps -->
              <p style="margin:0 0 16px;font-size:9px;letter-spacing:0.2em;color:#4a5a72;font-family:sans-serif;">
                HOW TO ACTIVATE
              </p>
              <table cellpadding="0" cellspacing="0" width="100%">
                <tr>
                  <td style="padding:10px 0;border-bottom:1px solid #1e2d42;">
                    <span style="font-size:11px;letter-spacing:0.12em;color:#4a5a72;font-family:sans-serif;">01 &nbsp;</span>
                    <span style="font-size:14px;color:#8a96aa;">Install the Cautelio Chrome extension</span>
                  </td>
                </tr>
                <tr>
                  <td style="padding:10px 0;border-bottom:1px solid #1e2d42;">
                    <span style="font-size:11px;letter-spacing:0.12em;color:#4a5a72;font-family:sans-serif;">02 &nbsp;</span>
                    <span style="font-size:14px;color:#8a96aa;">Click the Cautelio icon and paste your key</span>
                  </td>
                </tr>
                <tr>
                  <td style="padding:10px 0;">
                    <span style="font-size:11px;letter-spacing:0.12em;color:#4a5a72;font-family:sans-serif;">03 &nbsp;</span>
                    <span style="font-size:14px;color:#8a96aa;">Open any contract and click Analyze Contract</span>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding:20px 40px;border-top:1px solid #1e2d42;">
              <p style="margin:0;font-size:11px;letter-spacing:0.05em;color:#4a5a72;font-family:sans-serif;">
                Cautelio AI &middot; cautelioai.xyz &middot;
                Reply to this email if you need help.
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

    try:
        response = httpx.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {resend_key}",
                "Content-Type": "application/json",
            },
            json={
                "from": "Cautelio AI <noreply@cautelioai.xyz>",
                "to": [to_email],
                "subject": "Your Cautelio API key is ready",
                "html": html,
            },
            timeout=10,
        )
        return response.status_code == 200
    except Exception:
        return False
