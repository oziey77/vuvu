from django.core.mail import EmailMessage
from celery import shared_task
from django.template.loader import render_to_string, get_template



@shared_task
def sendConfirmOTP(username,email,otp):
    context = {
        'username':username,
        'otp':otp,
    }
    message = get_template('users/email/activate-account.html').render(context)
    subject = 'Confirm Your Email'
    msg = EmailMessage(
        subject,
        message,
        'Vuvu <no-reply@vuvu.ng>',
        [email],
    )
    msg.content_subtype ="html"# Main content is now text/html
    msg.send()