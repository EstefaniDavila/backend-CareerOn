import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from core.config import settings

def send_verification_code(to_email: str, code: str):
    """
    Envía un código de verificación al correo usando Gmail SMTP.
    """
    if not settings.SMTP_EMAIL or not settings.SMTP_PASSWORD:
        print(f"[MOCK EMAIL] Enviando código {code} a {to_email}")
        return {"status": "mocked", "code": code}

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #DCE5EC;">
        <div style="max-w-md; margin: 40px auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); border: 1px solid #F3F3F3;">
            <!-- Header con color Morado -->
            <div style="background-color: #1C6B72; padding: 30px; text-align: center;">
                <img src="https://res.cloudinary.com/dpuu7ddmk/image/upload/f_auto,q_auto/v1/WhatsApp_Image_2026-05-15_at_07.33.47_f5iq9x" alt="CarrerOn Logo" style="height: 60px; margin-bottom: 10px;" />
                <p style="color: #ffffff; margin-top: 5px; font-size: 16px; opacity: 0.9;">Tu Copiloto de Empleabilidad</p>
            </div>
            
            <!-- Body del correo -->
            <div style="padding: 40px 30px; text-align: center; color: #1C1C1C;">
                <h2 style="margin-top: 0; color: #1C1C1C; font-size: 22px;">¡Bienvenido Reclutador!</h2>
                <p style="font-size: 16px; line-height: 1.5; margin-bottom: 30px; color: #5F6368;">
                    Estamos emocionados de que te unas a <strong>CarrerOn</strong>. Para finalizar tu registro como empresa y empezar a descubrir el mejor talento UTP, ingresa el siguiente código de activación en la plataforma:
                </p>
                
                <div style="background-color: #F3F3F3; padding: 20px; border-radius: 8px; border: 2px dashed #1C6B72; display: inline-block; margin-bottom: 30px;">
                    <span style="font-size: 32px; font-weight: bold; color: #1C6B72; letter-spacing: 8px;">{code}</span>
                </div>
                
                <p style="font-size: 14px; color: #5F6368;">
                    Este código es confidencial. Si no has solicitado este registro, por favor ignora este correo.
                </p>
            </div>
            
            <!-- Footer -->
            <div style="background-color: #DCE5EC; padding: 20px; text-align: center; border-top: 1px solid #F3F3F3;">
                <p style="margin: 0; font-size: 12px; color: #5F6368;">
                    &copy; 2026 CarrerOn - Hackathon UTP. Todos los derechos reservados.
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    msg = MIMEMultipart()
    msg['From'] = f"CarrerOn <{settings.SMTP_EMAIL}>"
    msg['To'] = to_email
    msg['Subject'] = "Código de Activación - CarrerOn"
    msg.attach(MIMEText(html_content, 'html'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(settings.SMTP_EMAIL, settings.SMTP_PASSWORD)
        text = msg.as_string()
        server.sendmail(settings.SMTP_EMAIL, to_email, text)
        server.quit()
        return {"status": "success", "message": "Correo enviado vía SMTP"}
    except Exception as e:
        print(f"Error enviando correo SMTP: {str(e)}")
        raise e
