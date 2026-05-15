import os
import resend

resend.api_key = os.environ["RESEND_API_KEY"]


def send_api_key_email(to_email: str, api_key: str):
    resend.Emails.send({
        "from": "Cautelio AI <noreply@cautelioai.xyz>",
        "to": to_email,
        "subject": "Your Cautelio API Key — You're all set",
        "html": f"""
        <div style="font-family: Georgia, serif; max-width: 600px; margin: 0 auto;
                    background: #0b1320; color: #e8e4d9; padding: 48px 40px;">
            <p style="font-size: 22px; letter-spacing: 0.1em; color: #e8e4d9; margin-bottom: 32px;">
                <span style="color: #c4a35a;">&sect;</span> CAUTELIO
            </p>

            <h1 style="font-size: 24px; font-weight: normal; margin-bottom: 12px;">
                Your subscription is active.
            </h1>
            <p style="color: #7a8899; font-size: 15px; line-height: 1.7; margin-bottom: 32px;">
                Here is your API key. Keep it private — it's tied to your subscription.
            </p>

            <div style="background: #101a2a; border: 1px solid #1e2d42;
                        border-left: 3px solid #c4a35a; padding: 20px 24px;
                        margin-bottom: 36px; border-radius: 3px;">
                <p style="font-family: monospace; font-size: 15px; letter-spacing: 0.05em;
                           color: #c4a35a; margin: 0; word-break: break-all;">
                    {api_key}
                </p>
            </div>

            <h2 style="font-size: 16px; font-weight: normal; color: #c4a35a;
                        margin-bottom: 16px; letter-spacing: 0.08em;">
                How to activate
            </h2>
            <ol style="color: #7a8899; font-size: 14px; line-height: 2.2;
                       padding-left: 20px; margin-bottom: 36px;">
                <li>Open Chrome and click the Cautelio extension icon</li>
                <li>Paste your API key in the setup screen</li>
                <li>Click <strong style="color: #e8e4d9;">Save Key</strong></li>
                <li>Open any contract and click <strong style="color: #e8e4d9;">Analyze Contract</strong></li>
            </ol>

            <p style="color: #4a5a72; font-size: 12px; border-top: 1px solid #1e2d42;
                       padding-top: 24px; line-height: 1.7;">
                If you lose this key or need help, reply to this email or contact
                <a href="mailto:contact@cautelioai.xyz" style="color: #c4a35a;">
                    contact@cautelioai.xyz
                </a>.<br />
                To cancel your subscription, visit your Stripe billing portal.
            </p>
        </div>
        """,
    })
