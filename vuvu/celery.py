import os
from celery import Celery
from celery.schedules import crontab


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vuvu.settings")
app = Celery("vuvu")
app.config_from_object("django.conf:settings", namespace="CELERY")



app.conf.beat_schedule = {
    "Update One Time Deposit":{
        'task':'users.tasks.updateOnetimeDeposit',
        'schedule':crontab(minute='*/1')
    }
}

app.conf.beat_schedule = {
    "Update ATN Data Plans":{
        'task':'telecomms.tasks.updateDataPlans',
        # 'schedule':crontab(hour='*/3',minute=00 )
        'schedule':crontab(minute='*/15')
    },
}

app.autodiscover_tasks()