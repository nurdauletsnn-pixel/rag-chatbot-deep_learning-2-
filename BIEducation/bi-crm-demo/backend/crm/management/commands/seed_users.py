from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from crm.models import Branch, UserProfile


class Command(BaseCommand):
    help = "Seed CRM users with roles and branches"

    def handle(self, *args, **options):
        User = get_user_model()
        users = [
            ("admin", "admin@test.com", "admin", None),
            ("sales_head", "sales_head@test.com", "sales_head", None),
            ("rm", "rm@test.com", "rm", ["RIVIERA", "QUANTUM_STEM", "QUANTUM_TECH"]),
            ("manager", "manager@test.com", "manager", ["ALDI_BI_GREENLINE_AQUA", "ALDI_BI_FLAGMAN"]),
            ("sales", "sales@test.com", "sales", ["RIVIERA"]),
            ("sales_assistant", "sales_assistant@test.com", "sales_assistant", ["QUANTUM_STEM"]),
            ("network_coordinator", "network_coordinator@test.com", "network_coordinator", None),
            ("hr", "hr@test.com", "hr", None),
            ("site", "site@test.com", "site", None),
        ]

        branches = list(Branch.objects.all())
        for username, email, role, branch_codes in users:
            user, created = User.objects.get_or_create(username=username, defaults={"email": email, "is_staff": role == "admin"})
            if created:
                user.set_password("administrator")
                user.save()
            profile, _ = UserProfile.objects.get_or_create(user=user, defaults={"role": role})
            profile.role = role
            profile.save()
            if branch_codes:
                profile.branches.set([branch for branch in branches if branch.code in branch_codes])
            else:
                profile.branches.clear()

        self.stdout.write(self.style.SUCCESS("Seeded CRM users"))
