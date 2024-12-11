from django.core.mail import EmailMessage
from celery import shared_task
from django.template.loader import render_to_string, get_template

from payments.models import OneTimeDeposit
from datetime import date, datetime, timedelta,timezone

from users.models import User



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

@shared_task
def updateUserLastActivity():
    userGroups  = User.objects.filter(admin=True)
    time_buffer = datetime.now(timezone.utc) - timedelta(minutes=15)
    for user in userGroups:
        if user.last_activity < time_buffer:
            user.secret_key_timedout = True
            user.save()