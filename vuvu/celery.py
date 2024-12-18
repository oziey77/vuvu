import os
from celery import Celery
from celery.schedules import crontab


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vuvu.settings")
app = Celery("vuvu")
app.config_from_object("django.conf:settings", namespace="CELERY")





# app.conf.beat_schedule = {
#     "Update ATN Data Plans":{
#         'task':'telecomms.tasks.updateDataPlans',
#         # 'schedule':crontab(hour='*/3',minute=00 )
#         'schedule':crontab(minute='*/15')
#     },
# }

app.conf.beat_schedule = {
    "Update OneTime Deposit2":{
        'task':'users.tasks.updateOnetimeDeposit',
        'schedule':crontab(minute='*/2')
    }
}

app.conf.beat_schedule = {
    "Update User Last Activity 2":{
        'task':'users.tasks.updateUserLastActivity',
        'schedule':crontab(minute='*/15')
    }
}

app.conf.beat_schedule = {
    "Check ATN Balance":{
        'task':'adminbackend.tasks.checkAirtimeNgBalance',
        'schedule':crontab(minute='*/15')
    }
}

app.conf.beat_schedule = {
    "Check Suspicious Activities":{
        'task':'users.tasks.checkSuspiciousActivities',
        'schedule':crontab(minute='*/5')
    }
}





app.autodiscover_tasks()