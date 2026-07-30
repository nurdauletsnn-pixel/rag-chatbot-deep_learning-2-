from django.contrib import admin

from .models import ActivityLog, BotMessage, Branch, Child, ClassQuota, Contact, Deal, Funnel, Partner, PaymentSchedule, Stage, Tariff, Task, UserProfile

admin.site.register(Branch)
admin.site.register(ClassQuota)
admin.site.register(Funnel)
admin.site.register(Stage)
admin.site.register(Contact)
admin.site.register(Child)
admin.site.register(Partner)
admin.site.register(Tariff)
admin.site.register(Deal)
admin.site.register(PaymentSchedule)
admin.site.register(Task)
admin.site.register(ActivityLog)
admin.site.register(BotMessage)
admin.site.register(UserProfile)
