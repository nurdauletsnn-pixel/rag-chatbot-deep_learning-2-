import random
from datetime import date, timedelta
from decimal import Decimal

from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .business_logic import build_pricing_summary, calculate_total, get_initial_stage
from .models import ActivityLog, BotMessage, Branch, Child, ClassQuota, Contact, Deal, Funnel, Partner, PaymentSchedule, Stage, Tariff
from .serializers import ContactSerializer, DealSerializer


class ContactViewSet(viewsets.ModelViewSet):
    queryset = Contact.objects.prefetch_related("children", "deals").all()
    serializer_class = ContactSerializer


class DealViewSet(viewsets.ModelViewSet):
    queryset = Deal.objects.select_related("parent", "child", "branch", "funnel", "stage", "tariff", "partner").prefetch_related("payment_schedules", "activity", "bot_messages").all()
    serializer_class = DealSerializer

    def _ensure_funnel_stage(self, funnel_slug: str, stage_name: str | None = None):
        funnel, _ = Funnel.objects.get_or_create(slug=funnel_slug, defaults={"name": funnel_slug.replace("-", " ").title()})
        if stage_name:
            stage, _ = Stage.objects.get_or_create(funnel=funnel, name=stage_name, defaults={"order": 1})
        else:
            stage = funnel.stages.order_by("order").first() or Stage.objects.create(funnel=funnel, name="Qualification", order=1)
        return funnel, stage

    def _ensure_branch(self, code: str):
        branch, _ = Branch.objects.get_or_create(
            code=code,
            defaults={"name": code.replace("_", " ").title(), "city": "Астана", "segment": Branch.SEGMENT_SCHOOL},
        )
        return branch

    def _ensure_tariff(self, branch: Branch, tariff_name: str, grade_band: str):
        tariff, _ = Tariff.objects.get_or_create(
            branch=branch,
            name=tariff_name,
            grade_band=grade_band,
            defaults={"base_amount": Decimal("0.00"), "entrance_fee": Decimal("0.00"), "installments_count": 1},
        )
        return tariff

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        parent_profile = data.pop("parent_profile", None)
        child_profile = data.pop("child_profile", None)
        partner_profile = data.pop("partner_profile", None)
        funnel_slug = data.get("funnel_slug") or data.get("pipeline") or "b2c_schools"
        branch_code = data.get("branch") or "RIVIERA"
        tariff_name = data.get("tariff") or "Стандарт"
        has_food = data.get("has_food", False)
        has_transport = data.get("has_transport", False)
        transport_zone = data.get("transport_zone", "CITY")
        is_waitlisted = data.get("is_waitlisted", False)
        grade_band = data.get("grade_band") or "PRIMARY_SECONDARY"
        child_grade = child_profile.get("grade_or_group") if child_profile else None

        with transaction.atomic():
            funnel, stage = self._ensure_funnel_stage(funnel_slug, "Qualification")
            branch = self._ensure_branch(branch_code)
            tariff = self._ensure_tariff(branch, tariff_name, grade_band)
            child = None
            parent = None
            partner = None
            if partner_profile:
                partner = Partner.objects.create(**partner_profile)
                deal = Deal.objects.create(funnel=funnel, stage=stage, branch=branch, partner=partner, contract_value=data.get("contract_value"), total_amount=data.get("contract_value") or Decimal("0"))
            else:
                parent = Contact.objects.create(**parent_profile) if parent_profile else Contact.objects.create(full_name="New lead", phone=f"+7701{random.randint(1000000, 9999999)}", contact_type=Contact.CONTACT_TYPE_PARENT)
                child = Child.objects.create(parent=parent, **child_profile) if child_profile else Child.objects.create(parent=parent, full_name="New child", grade_or_group="1 класс", grade_band=grade_band)
                total_amount = calculate_total(branch_code=branch.code, grade_band=grade_band, tariff_name=tariff_name, has_food=has_food, has_transport=has_transport, transport_zone=transport_zone, has_second_child_discount=bool(child.is_second_child), has_subsidy=parent.has_subsidy)
                deal = Deal.objects.create(
                    funnel=funnel,
                    stage=stage,
                    branch=branch,
                    parent=parent,
                    child=child,
                    tariff=tariff,
                    has_food=has_food,
                    has_transport=has_transport,
                    transport_zone=transport_zone,
                    total_amount=total_amount,
                    status=Deal.STATUS_WAITLIST if is_waitlisted else Deal.STATUS_ACTIVE,
                )

            summary = build_pricing_summary(branch.code, tariff_name, has_food=has_food, has_transport=has_transport, is_second_child=child.is_second_child if child else False, grade=child_grade or "1", meals=3)
            deal.total_amount = summary["total_amount"]
            deal.save(update_fields=["total_amount"])
            PaymentSchedule.objects.filter(deal=deal).delete()
            for index, item in enumerate(summary["schedules"]):
                PaymentSchedule.objects.create(deal=deal, title=item["title"], due_date=deal.created_at.date() + timedelta(days=15 * (index + 1)), amount=item["amount"], status=item["status"])

        return Response(DealSerializer(deal).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        deal = self.get_object()
        data = request.data.copy()
        parent_profile = data.pop("parent_profile", None)
        child_profile = data.pop("child_profile", None)

        serializer = self.get_serializer(deal, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        if parent_profile and deal.parent:
            for field_name in ("full_name", "phone", "iin", "email", "contact_type", "has_subsidy"):
                value = parent_profile.get(field_name)
                if value is not None:
                    setattr(deal.parent, field_name, value)
            deal.parent.save()

        if child_profile and deal.child:
            for field_name in ("full_name", "grade_or_group", "grade_band", "allergies", "birth_date", "is_second_child"):
                value = child_profile.get(field_name)
                if value is not None:
                    setattr(deal.child, field_name, value)
            deal.child.save()

        return Response(self.get_serializer(deal).data)

    @action(detail=False, methods=["post"], url_path="simulate-lead")
    def simulate_lead(self, request):
        with transaction.atomic():
            funnel_slug = request.data.get("funnel_slug") or request.data.get("pipeline") or "b2c_schools"
            funnel, stage = self._ensure_funnel_stage(funnel_slug)
            branch = self._ensure_branch(request.data.get("branch") or random.choice(["RIVIERA", "QUANTUM_STEM", "ALDI_BI_CAPITAL_PARK"]))
            tariff_name = request.data.get("tariff") or random.choice(["Выгодный", "Стандарт", "Стандарт Плюс", "Основной (9 траншей)", "3 транша"])
            grade_band = request.data.get("grade_band") or random.choice(["PRESCHOOL", "PRIMARY_SECONDARY", "SENIOR"])
            has_food = random.choice([True, False])
            has_transport = random.choice([True, False])
            transport_zone = random.choice(["CITY", "SUBURB"])
            has_subsidy = random.choice([True, False])
            is_second_child = random.choice([True, False])
            full_name = random.choice(["Айгуль Серикова", "Нурлан Токтаев", "Мадина Оспанова", "Аслан Жумабаев", "Динара Бекетова"])
            phone = f"+7701{random.randint(1000000, 9999999)}"
            while Contact.objects.filter(phone=phone).exists():
                phone = f"+7701{random.randint(1000000, 9999999)}"
            parent = Contact.objects.create(full_name=full_name, phone=phone, email=f"parent{random.randint(1, 999)}@example.com", contact_type=Contact.CONTACT_TYPE_PARENT, has_subsidy=has_subsidy)
            child = Child.objects.create(parent=parent, full_name=random.choice(["Аружан", "Нурали", "Дарина", "Рамазан", "Аня"]), grade_or_group=random.choice(["0 класс", "1 класс", "5 класс", "7 класс", "10 класс"]), grade_band=grade_band, is_second_child=is_second_child)
            tariff = self._ensure_tariff(branch, tariff_name, grade_band)
            summary = build_pricing_summary(branch.code, tariff_name, has_food=has_food, has_transport=has_transport, is_second_child=is_second_child, grade=child.grade_or_group, meals=3)
            quota = ClassQuota.objects.filter(branch=branch, grade_or_group=child.grade_or_group).first()
            status = Deal.STATUS_ACTIVE
            if quota is not None and quota.is_full:
                status = Deal.STATUS_WAITLIST
            deal = Deal.objects.create(
                funnel=funnel,
                stage=stage,
                branch=branch,
                parent=parent,
                child=child,
                tariff=tariff,
                has_food=has_food,
                has_transport=has_transport,
                transport_zone=transport_zone,
                total_amount=summary["total_amount"],
                status=status,
            )
            if quota is not None:
                quota.occupied += 1
                quota.save(update_fields=["occupied"])
            PaymentSchedule.objects.filter(deal=deal).delete()
            for index, item in enumerate(summary["schedules"]):
                PaymentSchedule.objects.create(deal=deal, title=item["title"], due_date=deal.created_at.date() + timedelta(days=15 * (index + 1)), amount=item["amount"], status=item["status"])
            BotMessage.objects.create(deal=deal, sender="BOT", text="Здравствуйте! Подскажите, какой тариф и дополнительные услуги вам подходят?", field_filled="tariff")
            BotMessage.objects.create(deal=deal, sender="BOT", text=f"Автозаполнение: филиал {branch.name}, тариф {tariff_name}.", field_filled="profile")
            if status == Deal.STATUS_WAITLIST:
                ActivityLog.objects.create(deal=deal, type="SYSTEM", actor="SYSTEM", content="Класс заполнен, лид переведён в лист ожидания")

        return Response({"deal": DealSerializer(deal).data, "toast": {"type": "success", "message": "Lead generated and routed to the first pipeline stage."}}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], url_path="metadata")
    def metadata(self, request):
        """Return available branches and tariffs to power frontend selects."""
        branches = list(Branch.objects.all().values("id", "name", "code", "city", "segment", "is_free", "subsidy_amount"))
        tariffs = list(Tariff.objects.all().values("id", "branch_id", "name", "grade_band", "base_amount", "entrance_fee", "installments_count"))
        return Response({"branches": branches, "tariffs": tariffs})

    @action(detail=False, methods=["post"], url_path="pricing")
    def pricing(self, request):
        """Compute pricing summary without creating a deal.

        Expects: branch (code), tariff (name), has_food, has_transport, is_second_child, grade, meals, transport_zone
        """
        payload = request.data or {}
        branch_code = payload.get("branch")
        tariff_name = payload.get("tariff")
        has_food = bool(payload.get("has_food", False))
        has_transport = bool(payload.get("has_transport", False))
        is_second_child = bool(payload.get("is_second_child", False))
        grade = payload.get("grade", "1")
        meals = int(payload.get("meals", 3))
        try:
            summary = build_pricing_summary(branch_code, tariff_name, has_food=has_food, has_transport=has_transport, is_second_child=is_second_child, grade=grade, meals=meals)
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        # Make Decimal serializable
        for k in ("total_amount", "entrance_fee"):
            if k in summary:
                summary[k] = str(summary[k])
        for item in summary.get("schedules", []):
            item["amount"] = str(item["amount"])
        return Response(summary)

    @action(detail=True, methods=["post"], url_path="simulate-overdue")
    def simulate_overdue(self, request, pk=None):
        deal = self.get_object()
        deal.payment_schedules.update(status="OVERDUE")
        return Response({"status": "ok", "deal_id": deal.id})

    @action(detail=True, methods=["post"], url_path="generate-kaspi-link")
    def generate_kaspi_link(self, request, pk=None):
        deal = self.get_object()
        return Response({"link": f"https://kaspi.kz/pay/{deal.id}"})

    @action(detail=False, methods=["post"], url_path="release-quota-slot")
    def release_quota_slot(self, request):
        deal_id = request.data.get("deal_id")
        deal = Deal.objects.filter(pk=deal_id).first() if deal_id else Deal.objects.filter(status=Deal.STATUS_WAITLIST).order_by("created_at").first()
        if deal is None:
            return Response({"status": "ok"})
        deal.release_quota_slot()
        return Response({"status": "ok", "deal_id": deal.id})

    @action(detail=True, methods=["patch"], url_path="move-stage")
    def move_stage(self, request, pk=None):
        deal = self.get_object()
        stage_name = request.data.get("stage")
        if stage_name:
            stage = Stage.objects.filter(funnel=deal.funnel, name=stage_name).first()
            if stage is None:
                stage = Stage.objects.create(funnel=deal.funnel, name=stage_name, order=999)
            deal.stage = stage
            deal.clean()
            deal.save(update_fields=["stage"])
            if stage_name in {"ENTRANCE_FEE_PAID", "ENTRANCE_FEE"}:
                Task.objects.get_or_create(deal=deal, defaults={"title": "Collect entrance fee", "due_date": date.today() + timedelta(days=3)})
        return Response(DealSerializer(deal).data)

    @action(detail=False, methods=["post"], url_path="webhook/leads")
    def webhook_leads(self, request):
        payload = request.data or {}
        branch_code = payload.get("branch_code") or "RIVIERA"
        branch = self._ensure_branch(branch_code)
        funnel, stage = self._ensure_funnel_stage("b2c_schools")
        parent = Contact.objects.create(full_name=payload.get("full_name", "Web lead"), phone=payload.get("phone", f"+7701{random.randint(1000000, 9999999)}"), email=payload.get("email", ""), contact_type=Contact.CONTACT_TYPE_PARENT)
        child = Child.objects.create(parent=parent, full_name=payload.get("child_name", "New child"), grade_or_group=payload.get("grade_or_group", "1 класс"), grade_band=payload.get("grade_band", "PRIMARY_SECONDARY"))
        deal = Deal.objects.create(funnel=funnel, stage=stage, branch=branch, parent=parent, child=child, total_amount=Decimal("0"))
        return Response(DealSerializer(deal).data, status=status.HTTP_201_CREATED)
