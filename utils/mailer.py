# -*- coding: utf-8 -*-
"""
Passkey Bot — Enterprise-Grade Multi-Language Transactional Mailer.
Built according to RFC 5322, SpamAssassin 10/10 Guidelines, with Bot Avatar branding and Spam Check reminders.
Supports 10 Global Languages: vi, en, ja, ko, zh, es, fr, de, ru, pt.
"""
import smtplib
import ssl
import asyncio
import logging
import email.utils
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from utils.config import Config

log = logging.getLogger("passkey.mailer")

TRANSLATIONS = {
    "vi": {
        "subject": "[Passkey] Mã xác minh của bạn là {otp}",
        "preheader": "Mã bảo mật Passkey của bạn là {otp}. Hiệu lực trong 10 phút.",
        "heading": "Xác Thực Tài Khoản Discord",
        "greeting": "Xin chào <strong>{username}</strong>,",
        "intro": "Bạn vừa yêu cầu mã xác minh để tham gia máy chủ <strong>{guild_name}</strong> trên Discord. Dưới đây là mã bảo mật một lần của bạn:",
        "expiry_notice": " Mã này có hiệu lực trong vòng <strong>10 phút</strong>. Vì sự an toàn, tuyệt đối không chia sẻ mã này cho người khác.",
        "spam_reminder": " <strong>Lưu ý quan trọng:</strong> Nếu không tìm thấy mã trong Hộp thư đến (Inbox), bạn vui lòng kiểm tra thêm mục <strong>Thư rác (Spam / Junk)</strong> nhé.",
        "ignore_notice": "Nếu bạn không thực hiện yêu cầu này, vui lòng bỏ qua email này.",
        "footer_system": "Đây là thông báo bảo mật tự động từ hệ thống Passkey Gatekeeper.",
        "footer_brand": "Hệ thống bảo vệ Discord Passkey Zero-Trust Security Network"
    },
    "en": {
        "subject": "[Passkey] Your verification code is {otp}",
        "preheader": "Your Passkey security code is {otp}. Valid for 10 minutes.",
        "heading": "Confirm Your Discord Account",
        "greeting": "Hello <strong>{username}</strong>,",
        "intro": "We received a request to verify your account to join <strong>{guild_name}</strong> on Discord. Please use your one-time code below:",
        "expiry_notice": " This code will expire in <strong>10 minutes</strong>. For your security, never share this code with anyone.",
        "spam_reminder": " <strong>Important:</strong> If you cannot find this email in your primary Inbox, please check your <strong>Spam / Junk folder</strong>.",
        "ignore_notice": "If you did not request this verification code, please disregard this email.",
        "footer_system": "This is an automated system notification from Passkey Security Gateway.",
        "footer_brand": "Passkey Zero-Trust Discord Security Network"
    },
    "ja": {
        "subject": "【Passkey】認証コード: {otp}",
        "preheader": "Passkey認証コードは {otp} です。有効期限は10分です。",
        "heading": "Discordアカウントの認証",
        "greeting": "こんにちは <strong>{username}</strong> 様",
        "intro": "<strong>{guild_name}</strong> への参加に伴う認証コードをお届けします。以下のワンタイムコードをご利用ください：",
        "expiry_notice": " このコードの有効期限は <strong>10分間</strong> です。セキュリティ保護のため、第三者と共有しないでください。",
        "spam_reminder": " <strong>ご注意:</strong> メールが受信トレイに届いていない場合は、<strong>迷惑メールフォルダ（Spam）</strong>をご確認ください。",
        "ignore_notice": "心当たりのない場合は、このメールを破棄してください。",
        "footer_system": "このメールはPasskey Gatekeeperより自動送信されています。",
        "footer_brand": "Passkey Zero-Trust Discord セキュリティネットワーク"
    },
    "ko": {
        "subject": "[Passkey] 인증 코드: {otp}",
        "preheader": "Passkey 보안 인증 코드는 {otp} 입니다. 10분간 유효합니다.",
        "heading": "Discord 계정 보안 인증",
        "greeting": "안녕하세요 <strong>{username}</strong>님,",
        "intro": "<strong>{guild_name}</strong> 서버 참여를 위한 일회용 인증 코드가 발급되었습니다. 아래 코드를 입력해 주세요:",
        "expiry_notice": " 이 코드는 <strong>10분</strong> 동안 유효합니다. 보안을 위해 타인과 공유하지 마세요.",
        "spam_reminder": " <strong>안내:</strong> 받은편지함에서 메일을 찾을 수 없다면 <strong>스팸 메일함 (Spam)</strong>을 확인해 주세요.",
        "ignore_notice": "본인이 요청하지 않은 경우 이 메일을 무시하셔도 됩니다.",
        "footer_system": "본 메일은 Passkey Gatekeeper 시스템에서 자동 발송되었습니다.",
        "footer_brand": "Passkey Zero-Trust Discord 보안 네트워크"
    },
    "zh": {
        "subject": "【Passkey】您的验证码是 {otp}",
        "preheader": "您的 Passkey 安全验证码是 {otp}，10分钟内有效。",
        "heading": "Discord 账号安全验证",
        "greeting": "您好 <strong>{username}</strong>，",
        "intro": "您正在申请加入 Discord 服务器 <strong>{guild_name}</strong>。请使用以下一次性安全验证码：",
        "expiry_notice": " 此验证码有效期为 <strong>10分钟</strong>。为了您的账号安全，切勿向他人透露此代码。",
        "spam_reminder": " <strong>重要提示：</strong> 如果在收件箱中未找到此邮件，请检查您的 <strong>垃圾邮件箱（Spam）</strong>。",
        "ignore_notice": "如果您未曾发起此请求，请直接忽略此邮件。",
        "footer_system": "此邮件由 Passkey Gatekeeper 自动发送，请勿直接回复。",
        "footer_brand": "Passkey 零信任 Discord 安全防护系统"
    },
    "es": {
        "subject": "[Passkey] Tu código de verificación es {otp}",
        "preheader": "Tu código de seguridad Passkey es {otp}. Válido por 10 minutos.",
        "heading": "Confirmar Cuenta de Discord",
        "greeting": "Hola <strong>{username}</strong>,",
        "intro": "Hemos recibido una solicitud para verificar tu cuenta en <strong>{guild_name}</strong> en Discord. Utiliza el siguiente código único:",
        "expiry_notice": " Este código caducará en <strong>10 minutos</strong>. Por tu seguridad, nunca compartas este código con nadie.",
        "spam_reminder": " <strong>Aviso importante:</strong> Si no encuentras este correo en tu Bandeja de entrada, revisa tu <strong>carpeta de Spam / Correo no deseado</strong>.",
        "ignore_notice": "Si no solicitaste este código, puedes ignorar este mensaje de forma segura.",
        "footer_system": "Esta es una notificación automática del sistema Passkey Gatekeeper.",
        "footer_brand": "Red de Seguridad Zero-Trust para Discord de Passkey"
    },
    "fr": {
        "subject": "[Passkey] Votre code de vérification est {otp}",
        "preheader": "Votre code de sécurité Passkey est {otp}. Valide pendant 10 minutes.",
        "heading": "Confirmez Votre Compte Discord",
        "greeting": "Bonjour <strong>{username}</strong>,",
        "intro": "Nous avons reçu une demande de vérification pour rejoindre <strong>{guild_name}</strong> sur Discord. Veuillez utiliser votre code à usage unique ci-dessous :",
        "expiry_notice": " Ce code expirera dans <strong>10 minutes</strong>. Pour votre sécurité, ne partagez jamais ce code.",
        "spam_reminder": " <strong>Remarque importante :</strong> Si vous ne trouvez pas cet e-mail dans votre boîte de réception, vérifiez votre <strong>dossier Spam / Courrier indésirable</strong>.",
        "ignore_notice": "Si vous n'avez pas demandé ce code, vous pouvez ignorer cet e-mail en toute sécurité.",
        "footer_system": "Ceci est une notification automatique de Passkey Gatekeeper.",
        "footer_brand": "Réseau de Sécurité Zero-Trust Passkey pour Discord"
    },
    "de": {
        "subject": "[Passkey] Dein Bestätigungscode lautet {otp}",
        "preheader": "Dein Passkey-Sicherheitscode lautet {otp}. 10 Minuten gültig.",
        "heading": "Discord-Konto Bestätigen",
        "greeting": "Hallo <strong>{username}</strong>,",
        "intro": "Wir haben eine Anfrage erhalten, dein Konto für <strong>{guild_name}</strong> auf Discord zu verifizieren. Bitte verwende deinen einmaligen Code:",
        "expiry_notice": " Dieser Code läuft in <strong>10 Minuten</strong> ab. Teile diesen Code aus Sicherheitsgründen mit niemandem.",
        "spam_reminder": " <strong>Wichtiger Hinweis:</strong> Wenn du diese E-Mail nicht im Posteingang findest, überprüfe bitte deinen <strong>Spam-Ordner</strong>.",
        "ignore_notice": "Wenn du diesen Code nicht angefordert hast, kannst du diese E-Mail ignorieren.",
        "footer_system": "Dies ist eine automatische Benachrichtigung von Passkey Gatekeeper.",
        "footer_brand": "Passkey Zero-Trust Discord Sicherheitsnetzwerk"
    },
    "ru": {
        "subject": "[Passkey] Ваш код подтверждения: {otp}",
        "preheader": "Ваш код безопасности Passkey: {otp}. Действителен 10 минут.",
        "heading": "Подтверждение Аккаунта Discord",
        "greeting": "Здравствуйте, <strong>{username}</strong>,",
        "intro": "Мы получили запрос на верификацию вашего аккаунта на сервере <strong>{guild_name}</strong> в Discord. Ваш одноразовый код:",
        "expiry_notice": " Этот код действителен в течение <strong>10 минут</strong>. В целях безопасности никогда не передавайте его третьим лицам.",
        "spam_reminder": " <strong>Важное примечание:</strong> Если письмо не пришло во Входящие, пожалуйста, проверьте папку <strong>Спам (Spam)</strong>.",
        "ignore_notice": "Если вы не запрашивали данный код, просто проигнорируйте это письмо.",
        "footer_system": "Это автоматическое системное уведомление Passkey Gatekeeper.",
        "footer_brand": "Система Безопасности Passkey Zero-Trust для Discord"
    },
    "pt": {
        "subject": "[Passkey] Seu código de verificação é {otp}",
        "preheader": "Seu código de segurança Passkey é {otp}. Válido por 10 minutos.",
        "heading": "Confirmar Conta do Discord",
        "greeting": "Olá <strong>{username}</strong>,",
        "intro": "Recebemos uma solicitação para verificar sua conta no servidor <strong>{guild_name}</strong> no Discord. Use o código de uso único abaixo:",
        "expiry_notice": " Este código expira em <strong>10 minutos</strong>. Para sua segurança, nunca compartilhe este código.",
        "spam_reminder": " <strong>Aviso importante:</strong> Se você não encontrar este e-mail na Caixa de entrada, verifique sua <strong>pasta de Spam / Lixo eletrônico</strong>.",
        "ignore_notice": "Se você não solicitou este código, ignore este e-mail com segurança.",
        "footer_system": "Esta é uma notificação automática do sistema Passkey Gatekeeper.",
        "footer_brand": "Rede de Segurança Zero-Trust para Discord do Passkey"
    }
}

def _send_email_sync(recipient_email: str, subject: str, plain_text: str, html_body: str) -> bool:
    if not Config.SMTP_USER or not Config.SMTP_PASSWORD:
        log.warning("SMTP_USER or SMTP_PASSWORD is not configured in .env! Cannot send email.")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"Passkey Security <{Config.SMTP_USER}>"
    msg["To"] = recipient_email
    msg["Reply-To"] = Config.SMTP_USER
    msg["Date"] = email.utils.formatdate(localtime=True)
    msg["Message-ID"] = email.utils.make_msgid(domain="zohomail.com")
    msg["Auto-Submitted"] = "auto-generated"
    msg["X-Auto-Response-Suppress"] = "All"
    msg["MIME-Version"] = "1.0"
    msg["Feedback-ID"] = "passkey-verification:otp:passkeybot"

    part_text = MIMEText(plain_text, "plain", "utf-8")
    part_html = MIMEText(html_body, "html", "utf-8")
    msg.attach(part_text)
    msg.attach(part_html)

    try:
        if Config.SMTP_PORT == 465:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(Config.SMTP_HOST, Config.SMTP_PORT, context=context, timeout=15) as server:
                server.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
                server.sendmail(Config.SMTP_USER, recipient_email, msg.as_string())
        else:
            with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT, timeout=15) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
                server.sendmail(Config.SMTP_USER, recipient_email, msg.as_string())

        log.info(f"Verification OTP email successfully sent to: {recipient_email}")
        return True
    except Exception as e:
        log.error(f"Failed to send email to {recipient_email} via Zoho SMTP: {e}")
        return False

async def send_verification_otp(recipient_email: str, otp_code: str, guild_name: str, username: str, lang: str = "vi", avatar_url: str = "") -> bool:
    """Send enterprise-grade HTML verification email with multi-language and avatar branding."""
    t = TRANSLATIONS.get(lang.lower(), TRANSLATIONS["vi"])
    subject = t["subject"].format(otp=otp_code)
    
    logo_img = avatar_url or "https://raw.githubusercontent.com/IamPrmgVyt/passkey/main/static/passkey.png"

    plain_text = f"""Passkey Security Verification

{t['greeting'].replace('<strong>', '').replace('</strong>', '')}

{t['intro'].replace('<strong>', '').replace('</strong>', '')}

    {otp_code}

{t['expiry_notice'].replace('<strong>', '').replace('</strong>', '')}
{t['spam_reminder'].replace('<strong>', '').replace('</strong>', '')}

{t['ignore_notice']}

--
Passkey Security Gateway
"""

    html_body = f"""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="{lang}" xml:lang="{lang}">
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{t['heading']}</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1e293b;">
  <!-- Preheader Text -->
  <div style="display: none; font-size: 1px; color: #ffffff; line-height: 1px; max-height: 0px; max-width: 0px; opacity: 0; overflow: hidden;">
    {t['preheader'].format(otp=otp_code)}
  </div>

  <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color: #f1f5f9; padding: 36px 12px;">
    <tr>
      <td align="center">
        <!-- Main Card Container -->
        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="max-width: 520px; background-color: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05); overflow: hidden;">
          
          <!-- Header Bar with Bot Logo & Brand -->
          <tr>
            <td style="padding: 24px 32px; background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%); color: #ffffff;">
              <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                <tr>
                  <td width="48" style="vertical-align: middle;">
                    <img src="{logo_img}" alt="Passkey Logo" width="40" height="40" style="border-radius: 10px; display: block; border: 2px solid rgba(255,255,255,0.2);" onerror="this.style.display='none'" />
                  </td>
                  <td style="vertical-align: middle; padding-left: 12px;">
                    <span style="font-size: 18px; font-weight: 800; letter-spacing: -0.3px; color: #ffffff;">
                      Passkey <span style="color: #818cf8;">Gatekeeper</span>
                    </span>
                  </td>
                  <td align="right" style="vertical-align: middle;">
                    <span style="font-size: 11px; font-weight: 700; color: #c7d2fe; background: rgba(255, 255, 255, 0.12); padding: 4px 10px; border-radius: 20px; border: 1px solid rgba(255, 255, 255, 0.2);">
                      OTP Secure
                    </span>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Main Body Content -->
          <tr>
            <td style="padding: 32px 32px 24px 32px;">
              <h1 style="margin: 0 0 16px 0; font-size: 20px; font-weight: 800; color: #0f172a; line-height: 1.3;">
                {t['heading']}
              </h1>
              <p style="margin: 0 0 20px 0; font-size: 14px; line-height: 1.6; color: #334155;">
                {t['greeting'].format(username=username)}<br />
                {t['intro'].format(guild_name=guild_name)}
              </p>

              <!-- OTP Code Display Box -->
              <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin-bottom: 24px;">
                <tr>
                  <td align="center" style="background-color: #f8fafc; border: 2px dashed #6366f1; border-radius: 8px; padding: 18px 24px;">
                    <span style="font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, Courier, monospace; font-size: 34px; font-weight: 800; letter-spacing: 8px; color: #4338ca;">
                      {otp_code}
                    </span>
                  </td>
                </tr>
              </table>

              <p style="margin: 0 0 16px 0; font-size: 13px; line-height: 1.5; color: #64748b;">
                {t['expiry_notice']}
              </p>

              <!-- Highlighted Spam Folder Reminder Box -->
              <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin-bottom: 20px; background-color: #fefce8; border: 1px solid #fef08a; border-radius: 8px;">
                <tr>
                  <td style="padding: 12px 16px; font-size: 12.5px; color: #854d0e; line-height: 1.5;">
                    {t['spam_reminder']}
                  </td>
                </tr>
              </table>

              <p style="margin: 0; font-size: 12px; line-height: 1.5; color: #94a3b8;">
                {t['ignore_notice']}
              </p>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding: 20px 32px; background-color: #f8fafc; border-top: 1px solid #f1f5f9;">
              <p style="margin: 0 0 4px 0; font-size: 11px; color: #94a3b8; line-height: 1.4;">
                {t['footer_system']}
              </p>
              <p style="margin: 0; font-size: 11px; color: #94a3b8; line-height: 1.4;">
                {t['footer_brand']}
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
    return await asyncio.to_thread(_send_email_sync, recipient_email, subject, plain_text, html_body)
