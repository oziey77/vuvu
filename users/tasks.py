from django.core.mail import EmailMessage
from celery import shared_task
from django.template.loader import render_to_string, get_template

from payments.models import OneTimeDeposit
from datetime import date, datetime, timedelta,timezone



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

@shared_task
def sendPasswordOTP(username,email,otp):
    context = {
        'username':username,
        'otp':otp,
    }
    message = get_template('users/email/password-otp.html').render(context)
    subject = 'Reset Your Password'
    msg = EmailMessage(
        subject,
        message,
        'Vuvu <no-reply@vuvu.ng>',
        [email],
    )
    msg.content_subtype ="html"# Main content is now text/html
    msg.send()

@shared_task
def updateOnetimeDeposit():
    created_time = datetime.now() - timedelta(minutes=15)
    failedTransactions = OneTimeDeposit.objects.filter(created__lte=created_time,status='Pending')
    if failedTransactions.count() > 0:
        failedTransactions.update(status='Failed')