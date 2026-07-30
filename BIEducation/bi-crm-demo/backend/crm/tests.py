from io import StringIO
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase

from .business_logic import calculate_total
from .models import ActivityLog, Branch, Child, ClassQuota, Contact, Deal, Funnel, Partner, Stage, Task


class PricingCalculationTests(TestCase):
    def test_riviera_standard_primary_secondary(self):
        self.assertEqual(
            calculate_total(
                branch_code="RIVIERA",
                grade_band="PRIMARY_SECONDARY",
                tariff_name="Стандарт",
                has_food=True,
                has_transport=True,
                transport_zone="CITY",
                has_second_child_discount=False,
                has_subsidy=False,
            ),
            Decimal("4_900_000") + Decimal("752_400") + Decimal("57_000"),
        )

    def test_riviera_preschool_profitable(self):
        self.assertEqual(
            calculate_total(
                branch_code="RIVIERA",
                grade_band="PRESCHOOL",
                tariff_name="Выгодный",
                has_food=False,
                has_transport=False,
                transport_zone="CITY",
                has_second_child_discount=False,
                has_subsidy=False,
            ),
            Decimal("3_500_000"),
        )

    def test_quantum_basic(self):
        self.assertEqual(
            calculate_total(
                branch_code="QUANTUM_STEM",
                grade_band="PRIMARY_SECONDARY",
                tariff_name="Основной (9 траншей)",
                has_food=True,
                has_transport=False,
                transport_zone="CITY",
                has_second_child_discount=False,
                has_subsidy=False,
            ),
            Decimal("4_410_000") + Decimal("630_000") + Decimal("200_000"),
        )

    def test_aldi_bi_subsidy_and_second_child(self):
        branch = Branch.objects.create(
            name="ALDI BI Capital Park",
            code="ALDI_BI_CAPITAL_PARK",
            city="Астана",
            segment="KINDERGARTEN",
            is_free=False,
            subsidy_amount=Decimal("50_000"),
        )
        self.assertEqual(
            calculate_total(
                branch_code=branch.code,
                grade_band="PRESCHOOL",
                tariff_name="",
                has_food=False,
                has_transport=False,
                transport_zone="CITY",
                has_second_child_discount=True,
                has_subsidy=True,
            ),
            Decimal("250_000") - Decimal("50_000") - Decimal("25_000"),
        )


class DealModelTests(TestCase):
    def test_deal_clean_blocks_b2c_with_partner(self):
        funnel = Funnel.objects.create(slug="b2c_schools", name="B2C Schools")
        stage = Stage.objects.create(funnel=funnel, name="Qualification", order=1)
        branch = Branch.objects.create(name="Riviera", code="RIVIERA", city="Астана", segment="SCHOOL")
        parent = Contact.objects.create(full_name="Parent", phone="+77010000001", contact_type="PARENT")
        child = Child.objects.create(parent=parent, full_name="Child", grade_or_group="1 класс", grade_band="PRIMARY_SECONDARY")
        partner = Partner.objects.create(company_name="Acme", partner_type="CONSTRUCTION", contact_person="Person", contact_phone="+77010000002")
        deal = Deal(funnel=funnel, stage=stage, branch=branch, parent=parent, child=child, partner=partner)
        with self.assertRaises(ValidationError):
            deal.clean()

    def test_deal_clean_blocks_b2b_with_contact(self):
        funnel = Funnel.objects.create(slug="b2b_partnership", name="B2B")
        stage = Stage.objects.create(funnel=funnel, name="Qualification", order=1)
        branch = Branch.objects.create(name="BIART", code="BIART", city="Астана", segment="CREATIVE")
        parent = Contact.objects.create(full_name="Parent", phone="+77010000003", contact_type="PARENT")
        partner = Partner.objects.create(company_name="Acme", partner_type="BIART_RENTAL", contact_person="Person", contact_phone="+77010000004")
        deal = Deal(funnel=funnel, stage=stage, branch=branch, parent=parent, partner=partner)
        with self.assertRaises(ValidationError):
            deal.clean()


class QuotaReleaseTests(TestCase):
    def test_release_quota_slot_assigns_first_waitlisted_deal(self):
        branch = Branch.objects.create(name="Riviera", code="RIVIERA", city="Астана", segment="SCHOOL")
        quota = ClassQuota.objects.create(branch=branch, grade_or_group="1 класс", capacity=1, occupied=1)
        funnel = Funnel.objects.create(slug="b2c_schools", name="B2C Schools")
        stage = Stage.objects.create(funnel=funnel, name="Qualification", order=1)
        parent1 = Contact.objects.create(full_name="Parent 1", phone="+77010000005", contact_type="PARENT")
        child1 = Child.objects.create(parent=parent1, full_name="Child 1", grade_or_group="1 класс", grade_band="PRIMARY_SECONDARY")
        parent2 = Contact.objects.create(full_name="Parent 2", phone="+77010000006", contact_type="PARENT")
        child2 = Child.objects.create(parent=parent2, full_name="Child 2", grade_or_group="1 класс", grade_band="PRIMARY_SECONDARY")
        first = Deal.objects.create(funnel=funnel, stage=stage, branch=branch, parent=parent1, child=child1, status="WAITLIST", total_amount=Decimal("100"))
        second = Deal.objects.create(funnel=funnel, stage=stage, branch=branch, parent=parent2, child=child2, status="WAITLIST", total_amount=Decimal("200"))

        quota.occupied = 0
        quota.save(update_fields=["occupied"])
        first.release_quota_slot()

        first.refresh_from_db()
        self.assertEqual(first.status, "ACTIVE")
        self.assertEqual(ActivityLog.objects.filter(deal=first).count(), 1)
        self.assertEqual(Task.objects.filter(deal=second).count(), 0)


class MockDataGenerationTests(TestCase):
    def test_generate_mock_data_creates_varied_lead_statuses(self):
        call_command("generate_mock_data", stdout=StringIO(), stderr=StringIO())

        deals = Deal.objects.all()
        statuses = set(deals.values_list("status", flat=True))

        self.assertGreaterEqual(deals.count(), 20)
        self.assertIn(Deal.STATUS_ACTIVE, statuses)
        self.assertIn(Deal.STATUS_WAITLIST, statuses)
        self.assertIn(Deal.STATUS_LOST, statuses)
        self.assertIn(Deal.STATUS_WON, statuses)
