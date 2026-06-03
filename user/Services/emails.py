from django.core.mail import send_mail


def send_otp_email(otp, user):
    send_mail(
        subject="Verify your email - Hallmark Manager",
        message=f"Hi {user.username}, your OTP is: {otp}. expires in 10 minutes.",
        from_email="Hallmark Manager <onbording@resend.dev>",
        recipient_list=[user.email],
        html_message=f"""
                <div style="font-family: Arial, sans-serif; max-width: 500px;">
                    <h2>Hi {user.username},<h2>
                    <p>Use this otp to verify your account:</p>
                    <div style="font-size: 36px; font-weight: bold; letter-spacing: 10px;
                            padding: 20px; background: #f5f5f5; text-align: center;">
                    "{otp}"
                    </div>
                <p> Expires in <strong>10 minutes<strong>. If you didn't sign up, ignore this.</p>
            
                </div>
""",
    )


def send_verified_email(user):
    send_mail(
        subject="Account verified - Hallmark Manager",
        message=f"Hi {user.username}, your account has been verified.",
        from_email="Hallmark Manager <onboarding@resend.dev>",
        recipient_list=[user.email],
        html_message=f"""
                <div style="font-family: Arial, sans-serif; max-width: 500px;">
                    <h2>Hi {user.username},<h2>
                    <p>your account has been <strong>successfully verified</strong>.</p>    
                    <p>Welcome to hallmark Manger!</p>
                    <p>A clean workspace for your daily workflow.</p>
                </div>
                """,
    )
