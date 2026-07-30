import random
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand

from crm.business_logic import calculate_total
from crm.models import ActivityLog, BotMessage, Branch, Child, ClassQuota, Contact, Deal, Funnel, Partner, PaymentSchedule, Stage, Tariff, Task


class Command(BaseCommand):
    help = "Populate the database with realistic CRM mock data"

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Recreate mock data even if deals already exist")

    def handle(self, *args, **options):
        if Deal.objects.exists() and not options["force"]:
            self.stdout.write(self.style.WARNING("Mock data already exists. Nothing to do."))
            return

        ActivityLog.objects.all().delete()
        BotMessage.objects.all().delete()
        PaymentSchedule.objects.all().delete()
        Task.objects.all().delete()
        Deal.objects.all().delete()
        Stage.objects.all().delete()
        Funnel.objects.all().delete()
        ClassQuota.objects.all().delete()
        Tariff.objects.all().delete()
        Child.objects.all().delete()
        Contact.objects.all().delete()
        Partner.objects.all().delete()
        Branch.objects.all().delete()

        branches = [
            {"name": "Riviera International School", "code": "RIVIERA", "city": "Астана", "segment": Branch.SEGMENT_SCHOOL},
            {"name": "Quantum STEM School", "code": "QUANTUM_STEM", "city": "Астана", "segment": Branch.SEGMENT_SCHOOL},
            {"name": "Quantum TECH School", "code": "QUANTUM_TECH", "city": "Астана", "segment": Branch.SEGMENT_SCHOOL},
            {"name": "ALDI BI Capital Park", "code": "ALDI_BI_CAPITAL_PARK", "city": "Астана", "segment": Branch.SEGMENT_KINDERGARTEN, "subsidy_amount": Decimal("50000")},
            {"name": "ALDI BI GreenLine.Aqua", "code": "ALDI_BI_GREENLINE_AQUA", "city": "Астана", "segment": Branch.SEGMENT_KINDERGARTEN},
            {"name": "ALDI BI Flagman", "code": "ALDI_BI_FLAGMAN", "city": "Астана", "segment": Branch.SEGMENT_KINDERGARTEN},
            {"name": "BINOM Astana 1", "code": "BINOM_ASTANA_1", "city": "Астана", "segment": Branch.SEGMENT_FREE_SCHOOL, "is_free": True},
            {"name": "BINOM Astana 2", "code": "BINOM_ASTANA_2", "city": "Астана", "segment": Branch.SEGMENT_FREE_SCHOOL, "is_free": True},
            {"name": "BINOM Atyrau 1", "code": "BINOM_ATYRAU_1", "city": "Атырау", "segment": Branch.SEGMENT_FREE_SCHOOL, "is_free": True},
            {"name": "BIART", "code": "BIART", "city": "Астана", "segment": Branch.SEGMENT_CREATIVE},
        ]
        branch_objs = [Branch.objects.create(**payload) for payload in branches]

        for branch in branch_objs:
            if branch.segment in {Branch.SEGMENT_SCHOOL, Branch.SEGMENT_KINDERGARTEN}:
                for grade in ["1 класс", "2 класс", "Ясли"]:
                    ClassQuota.objects.create(branch=branch, grade_or_group=grade, capacity=20, occupied=0)
            elif branch.segment == Branch.SEGMENT_FREE_SCHOOL:
                ClassQuota.objects.create(branch=branch, grade_or_group="Бесплатная группа", capacity=20, occupied=0)

        funnel_data = [
            ("b2c_schools", "B2C Schools"),
            ("b2c_kindergarten", "B2C Kindergarten"),
            ("b2b_partnership", "B2B Partnership"),
        ]
        funnels = []
        for slug, name in funnel_data:
            funnel = Funnel.objects.create(slug=slug, name=name)
            funnels.append(funnel)
            stages = []
            if slug == "b2c_schools":
                stages = ["Unsorted", "Qualification", "Tour/Test Scheduled", "Tour/Test Passed", "Tariff & Addons Selection", "Entrance Fee Paid", "Contract Signed"]
            elif slug == "b2c_kindergarten":
                stages = ["New Lead", "Free Trial Day Set", "Adaptation Period", "Entrance Fee", "Monthly Payment", "Won"]
            else:
                stages = ["Primary Contact", "Qualification/Meeting", "Commercial Proposal", "Contract/Tender Negotiation", "Invoicing", "Deal Closed"]
            for order, stage_name in enumerate(stages, start=1):
                Stage.objects.create(funnel=funnel, name=stage_name, order=order, is_won=stage_name in {"Contract Signed", "Won", "Deal Closed"})

        for branch in branch_objs[:6]:
            Tariff.objects.create(branch=branch, name="Выгодный", grade_band="PRIMARY_SECONDARY", base_amount=Decimal("4500000"), entrance_fee=Decimal("350000"), installments_count=1)
            Tariff.objects.create(branch=branch, name="Стандарт", grade_band="PRIMARY_SECONDARY", base_amount=Decimal("4900000"), entrance_fee=Decimal("350000"), installments_count=3)
            Tariff.objects.create(branch=branch, name="Стандарт Плюс", grade_band="PRIMARY_SECONDARY", base_amount=Decimal("5180000"), entrance_fee=Decimal("350000"), installments_count=8)
            Tariff.objects.create(branch=branch, name="Основной (9 траншей)", grade_band="PRIMARY_SECONDARY", base_amount=Decimal("4410000"), entrance_fee=Decimal("200000"), installments_count=9)
            Tariff.objects.create(branch=branch, name="3 транша", grade_band="PRIMARY_SECONDARY", base_amount=Decimal("4200000"), entrance_fee=Decimal("200000"), installments_count=3)

        for funnel in funnels:
            if not funnel.stages.filter(is_won=True).exists():
                Stage.objects.create(funnel=funnel, name="Won", order=999, is_won=True)
            if not funnel.stages.filter(is_lost=True).exists():
                Stage.objects.create(funnel=funnel, name="Lost", order=1000, is_lost=True)

        parent_names = ["Айгуль Серикова", "Нурлан Токтаев", "Мадина Оспанова", "Аслан Жумабаев", "Динара Бекетова", "Серик Куанышев", "Ляззат Айтмухамбетова", "Марина Куанышова"]
        child_names = ["Аружан", "Нурали", "Дарина", "Рамазан", "Аня", "Ильяс", "София", "Али"]
        partner_names = ["Alem Logistics", "Global Education", "Bright Labs", "North Star", "EduBridge"]

        for index in range(30):
            funnel = random.choice(funnels[:2]) if index % 5 != 0 else funnels[2]
            branch = random.choice(branch_objs[:6]) if funnel.slug != "b2b_partnership" else random.choice(branch_objs[:4])
            tariffs_for_branch = list(Tariff.objects.filter(branch=branch))
            if branch.code in {"QUANTUM_STEM", "QUANTUM_TECH"}:
                tariffs_for_branch = [tariff for tariff in tariffs_for_branch if tariff.name in {"Основной (9 траншей)", "3 транша"}]
            tariff = random.choice(tariffs_for_branch) if tariffs_for_branch else None
            parent = Contact.objects.create(full_name=parent_names[index % len(parent_names)], phone=f"+7701{1000000 + index}", contact_type=Contact.CONTACT_TYPE_PARENT)
            child = Child.objects.create(parent=parent, full_name=child_names[(index + 2) % len(child_names)], grade_or_group="1 класс" if index % 2 == 0 else "Ясли", grade_band="PRIMARY_SECONDARY")
            has_food = index % 2 == 0
            has_transport = index % 3 == 0
            status = [Deal.STATUS_ACTIVE, Deal.STATUS_ACTIVE, Deal.STATUS_ACTIVE, Deal.STATUS_ACTIVE, Deal.STATUS_WAITLIST, Deal.STATUS_WAITLIST, Deal.STATUS_WON, Deal.STATUS_LOST][index % 8]
            stage_candidates = list(funnel.stages.order_by("order"))
            if status == Deal.STATUS_WON:
                stage = funnel.stages.filter(is_won=True).first() or stage_candidates[-1]
            elif status == Deal.STATUS_LOST:
                stage = funnel.stages.filter(is_lost=True).first() or stage_candidates[-1]
            else:
                stage = stage_candidates[index % len(stage_candidates)] if stage_candidates else funnel.stages.order_by("order").first()

            if funnel.slug == "b2b_partnership":
                partner = Partner.objects.create(company_name=partner_names[index % len(partner_names)], partner_type=Partner.PARTNER_TYPE_CONSTRUCTION, contact_person="Aynur", contact_phone=f"+7701{2000000 + index}")
                deal = Deal.objects.create(funnel=funnel, stage=stage, branch=branch, partner=partner, contract_value=Decimal("5000000"), total_amount=Decimal("5000000"), status=status)
            else:
                tariff_name = tariff.name if tariff else "Стандарт"
                if branch.code == "RIVIERA":
                    tariff_name = tariff_name if tariff_name in {"Выгодный", "Стандарт", "Стандарт Плюс"} else "Стандарт"
                elif branch.code in {"QUANTUM_STEM", "QUANTUM_TECH"}:
                    tariff_name = tariff_name if tariff_name in {"Основной (9 траншей)", "3 транша"} else "Основной (9 траншей)"
                total_amount = calculate_total(branch.code, "PRIMARY_SECONDARY", tariff_name, has_food=has_food, has_transport=has_transport, transport_zone="CITY", has_second_child_discount=False, has_subsidy=False)
                deal = Deal.objects.create(
                    funnel=funnel,
                    stage=stage,
                    branch=branch,
                    parent=parent,
                    child=child,
                    tariff=tariff,
                    has_food=has_food,
                    has_transport=has_transport,
                    total_amount=total_amount,
                    status=status,
                )
                if status == Deal.STATUS_WAITLIST:
                    quota = ClassQuota.objects.filter(branch=branch, grade_or_group=child.grade_or_group).first()
                    if quota is not None:
                        quota.occupied = quota.capacity
                        quota.save(update_fields=["occupied"])
                    ActivityLog.objects.create(deal=deal, type="SYSTEM", actor="SYSTEM", content="Класс заполнен, лид переведён в лист ожидания")

            if status == Deal.STATUS_WON:
                ActivityLog.objects.create(deal=deal, type="SYSTEM", actor="SYSTEM", content="Сделка успешно закрыта и передана в финансовый блок")
            elif status == Deal.STATUS_LOST:
                ActivityLog.objects.create(deal=deal, type="SYSTEM", actor="SYSTEM", content="Лид не прошёл по критериям и закрыт как проигранный")

            schedule_status = "PAID" if status == Deal.STATUS_WON else "OVERDUE" if index % 5 == 0 else "PENDING"
            PaymentSchedule.objects.create(deal=deal, title="Entrance fee", due_date=date.today() + timedelta(days=10 + index % 7), amount=Decimal("200000"), status=schedule_status)

            if status != Deal.STATUS_LOST:
                Task.objects.create(deal=deal, title="Проверить следующий шаг по лид-обработке", due_date=date.today() + timedelta(days=2 + index % 3), is_done=status == Deal.STATUS_WON, auto_generated=True)

        binom_branch = Branch.objects.get(code="BINOM_ASTANA_1")
        parent = Contact.objects.create(full_name="Нурлан BINOM", phone="+77019999999", contact_type=Contact.CONTACT_TYPE_PARENT)
        child = Child.objects.create(parent=parent, full_name="Миша BINOM", grade_or_group="1 класс", grade_band="PRIMARY_SECONDARY")
        deal = Deal.objects.create(funnel=funnels[0], stage=funnels[0].stages.order_by("order").first(), branch=binom_branch, parent=parent, child=child, total_amount=Decimal("0"), status="ACTIVE")
        ActivityLog.objects.create(deal=deal, type="SYSTEM", actor="SYSTEM", content="Заявка перенаправлена в BINOM через Mektep Smart Nation")

        self.stdout.write(self.style.SUCCESS("Created CRM mock data."))
