from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from math import radians, sin, cos, asin, sqrt
from typing import Dict, Iterable, List, Sequence, Tuple
from uuid import uuid4


# ---------- Lead Generation & CRM ----------


@dataclass(slots=True)
class Lead:
    id: str
    customer_name: str
    address: str
    requested_services: List[str]
    property_square_feet: float
    budget: float
    urgency: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(slots=True)
class Contractor:
    id: str
    name: str
    service_areas: List[str]
    specialties: List[str]
    active_jobs: int = 0


@dataclass(slots=True)
class FollowUpTask:
    lead_id: str
    send_at: datetime
    channel: str
    message: str


class LeadCRMService:
    def score_lead(self, lead: Lead) -> int:
        urgency_weights = {"high": 35, "medium": 20, "low": 10}
        service_weight = min(len(lead.requested_services) * 10, 30)
        budget_weight = 20 if lead.budget >= 1000 else 10 if lead.budget >= 500 else 0
        size_weight = 15 if lead.property_square_feet >= 5000 else 8 if lead.property_square_feet >= 2000 else 3
        return min(100, urgency_weights.get(lead.urgency.lower(), 0) + service_weight + budget_weight + size_weight)

    def auto_assign(self, lead: Lead, contractors: Sequence[Contractor]) -> Contractor | None:
        ranked: List[Tuple[int, Contractor]] = []
        address_lower = lead.address.lower()
        for contractor in contractors:
            area_match = any(area.lower() in address_lower for area in contractor.service_areas)
            specialty_matches = sum(1 for svc in lead.requested_services if svc.lower() in {s.lower() for s in contractor.specialties})
            if not area_match and specialty_matches == 0:
                continue
            score = (20 if area_match else 0) + specialty_matches * 15 - contractor.active_jobs * 2
            ranked.append((score, contractor))

        if not ranked:
            return None

        best = max(ranked, key=lambda item: item[0])[1]
        best.active_jobs += 1
        return best

    def build_follow_up_sequence(self, lead: Lead) -> List[FollowUpTask]:
        base = lead.created_at
        steps = [
            (timedelta(hours=2), "sms", f"Hi {lead.customer_name}, thanks for contacting GreenScape AI. Want an instant estimate?"),
            (timedelta(days=1), "email", "We can lock in your preferred service window this week."),
            (timedelta(days=3), "sms", "Quick reminder: your lawn care quote is ready when you are."),
        ]
        return [FollowUpTask(lead_id=lead.id, send_at=base + delay, channel=channel, message=message) for delay, channel, message in steps]


# ---------- Proposals & Invoices ----------


@dataclass(slots=True)
class LineItem:
    description: str
    quantity: float
    unit_price: float

    @property
    def total(self) -> float:
        return round(self.quantity * self.unit_price, 2)


@dataclass(slots=True)
class Proposal:
    id: str
    customer_id: str
    line_items: List[LineItem]
    terms: str
    signature_token: str = field(default_factory=lambda: uuid4().hex)

    @property
    def subtotal(self) -> float:
        return round(sum(item.total for item in self.line_items), 2)


@dataclass(slots=True)
class Invoice:
    id: str
    customer_id: str
    amount_due: float
    due_date: date
    recurring_interval_days: int | None = None
    paid: bool = False


class BillingService:
    def generate_proposal(self, customer_id: str, line_items: List[LineItem], terms: str) -> Proposal:
        return Proposal(id=f"prop_{uuid4().hex[:10]}", customer_id=customer_id, line_items=line_items, terms=terms)

    def create_invoice(self, proposal: Proposal, due_in_days: int = 14, recurring_interval_days: int | None = None) -> Invoice:
        return Invoice(
            id=f"inv_{uuid4().hex[:10]}",
            customer_id=proposal.customer_id,
            amount_due=proposal.subtotal,
            due_date=date.today() + timedelta(days=due_in_days),
            recurring_interval_days=recurring_interval_days,
        )

    def record_payment(self, invoice: Invoice, amount: float) -> bool:
        if amount < invoice.amount_due:
            return False
        invoice.paid = True
        return True

    def next_recurring_invoice_date(self, invoice: Invoice) -> date | None:
        if invoice.recurring_interval_days is None:
            return None
        return invoice.due_date + timedelta(days=invoice.recurring_interval_days)


# ---------- Customer Portal ----------


@dataclass(slots=True)
class ServiceRequest:
    customer_id: str
    service_type: str
    preferred_date: date
    notes: str


class CustomerPortalService:
    def approve_proposal(self, proposal: Proposal, customer_signature: str) -> str:
        return f"approved:{proposal.id}:{customer_signature.strip()}"

    def pay_invoice(self, billing: BillingService, invoice: Invoice, amount: float) -> bool:
        return billing.record_payment(invoice, amount)

    def request_service(self, customer_id: str, service_type: str, preferred_date: date, notes: str = "") -> ServiceRequest:
        return ServiceRequest(customer_id=customer_id, service_type=service_type, preferred_date=preferred_date, notes=notes)

    def view_service_history(self, history: Sequence[str]) -> List[str]:
        return list(history)


# ---------- Contractor Dashboard ----------


@dataclass(slots=True)
class ScheduledJob:
    id: str
    contractor_id: str
    service_date: date
    address: str
    crew: List[str]
    notes: List[str] = field(default_factory=list)
    photos: List[str] = field(default_factory=list)


class ContractorDashboardService:
    def daily_schedule(self, jobs: Iterable[ScheduledJob], target_date: date, contractor_id: str) -> List[ScheduledJob]:
        return [j for j in jobs if j.service_date == target_date and j.contractor_id == contractor_id]

    def add_job_note(self, job: ScheduledJob, note: str) -> None:
        job.notes.append(note)

    def assign_crew(self, job: ScheduledJob, crew_members: Sequence[str]) -> None:
        job.crew = list(crew_members)

    def add_before_after_photo(self, job: ScheduledJob, photo_url: str) -> None:
        job.photos.append(photo_url)


# ---------- GPS + AI Yard Measurement ----------


class YardMeasurementService:
    def polygon_square_footage(self, polygon_points: Sequence[Tuple[float, float]]) -> float:
        if len(polygon_points) < 3:
            return 0.0
        area = 0.0
        for i in range(len(polygon_points)):
            x1, y1 = polygon_points[i]
            x2, y2 = polygon_points[(i + 1) % len(polygon_points)]
            area += (x1 * y2) - (x2 * y1)
        return round(abs(area) / 2.0, 2)

    def detect_surface_mix(self, classified_pixels: Dict[str, int]) -> Dict[str, float]:
        total = sum(classified_pixels.values())
        if total <= 0:
            return {"grass": 0.0, "mulch": 0.0, "trees": 0.0, "driveway": 0.0}
        return {k: round((v / total) * 100, 2) for k, v in classified_pixels.items()}


# ---------- Route Assist Optimization ----------


@dataclass(slots=True)
class RouteStop:
    id: str
    latitude: float
    longitude: float


class RouteOptimizationService:
    @staticmethod
    def _distance_miles(a: RouteStop, b: RouteStop) -> float:
        r = 3958.8
        lat1, lon1, lat2, lon2 = map(radians, [a.latitude, a.longitude, b.latitude, b.longitude])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        h = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        return r * 2 * asin(sqrt(h))

    def optimize(self, origin: RouteStop, stops: Sequence[RouteStop]) -> List[RouteStop]:
        unvisited = list(stops)
        route: List[RouteStop] = []
        current = origin
        while unvisited:
            next_stop = min(unvisited, key=lambda stop: self._distance_miles(current, stop))
            route.append(next_stop)
            unvisited.remove(next_stop)
            current = next_stop
        return route


# ---------- Weather Intelligence ----------


@dataclass(slots=True)
class WeatherSnapshot:
    rain_probability: float
    heat_index: float
    storm_alert: bool
    rainfall_inches_week: float
    average_temp_f: float


class WeatherIntelligenceService:
    def should_delay_service(self, weather: WeatherSnapshot) -> bool:
        return weather.storm_alert or weather.rain_probability >= 0.65 or weather.heat_index >= 105

    def grass_growth_rate(self, weather: WeatherSnapshot) -> str:
        if weather.average_temp_f < 55:
            return "slow"
        if weather.average_temp_f <= 85 and weather.rainfall_inches_week >= 0.5:
            return "fast"
        return "moderate"


# ---------- Equipment Management ----------


@dataclass(slots=True)
class Equipment:
    id: str
    name: str
    runtime_hours: float
    maintenance_log: List[str] = field(default_factory=list)
    total_cost: float = 0.0
    warranty_expires_on: date | None = None


class EquipmentManagementService:
    maintenance_intervals = {
        "oil change": 50,
        "blade sharpening": 25,
        "filter change": 75,
        "belt inspection": 100,
    }

    def add_runtime(self, equipment: Equipment, hours: float) -> None:
        equipment.runtime_hours = round(equipment.runtime_hours + max(hours, 0), 2)

    def log_maintenance(self, equipment: Equipment, entry: str, cost: float = 0.0) -> None:
        equipment.maintenance_log.append(entry)
        equipment.total_cost = round(equipment.total_cost + max(cost, 0), 2)

    def service_reminders(self, equipment: Equipment) -> List[str]:
        reminders = []
        for task, interval in self.maintenance_intervals.items():
            if equipment.runtime_hours > 0 and equipment.runtime_hours % interval <= 5:
                reminders.append(task)
        return reminders


# ---------- Contractor Terms & Agreements ----------


class TermsAgreementService:
    templates = {
        "lawn_care": "Weekly mowing and edging under seasonal turf best practices.",
        "landscaping": "Install and maintain beds, plantings, and hardscape features.",
        "weather_delay": "Service windows may shift for rain, storms, or extreme heat.",
        "cancellation": "Cancellation requires 24-hour notice before arrival window.",
        "recurring_service": "Recurring services renew monthly unless terminated in writing.",
    }

    def generate_terms(self, agreement_types: Sequence[str]) -> str:
        return "\n".join(self.templates[t] for t in agreement_types if t in self.templates)

    def sign(self, customer_id: str, terms: str) -> str:
        return f"sig_{customer_id}_{abs(hash(terms)) % 1_000_000}"


# ---------- Material & Labor Estimation ----------


class EstimationService:
    def mulch_cubic_yards(self, square_feet: float, depth_inches: float) -> float:
        cubic_feet = square_feet * (depth_inches / 12)
        return round(cubic_feet / 27, 2)

    def sod_area_rolls(self, square_feet: float, roll_coverage_sqft: float = 10) -> int:
        return max(0, int((square_feet + roll_coverage_sqft - 1) // roll_coverage_sqft))

    def plant_quantity(self, bed_square_feet: float, spacing_feet: float) -> int:
        if spacing_feet <= 0:
            return 0
        return max(0, int(bed_square_feet / (spacing_feet * spacing_feet)))

    def mowing_time_hours(self, square_feet: float, mower_sqft_per_hour: float = 12000) -> float:
        if mower_sqft_per_hour <= 0:
            return 0.0
        return round(square_feet / mower_sqft_per_hour, 2)

    def labor_cost(self, estimated_hours: float, hourly_rate: float, crew_size: int) -> float:
        return round(max(estimated_hours, 0) * max(hourly_rate, 0) * max(crew_size, 0), 2)


# ---------- GreenScape AI Platform Facade ----------


@dataclass(slots=True)
class GreenScapeAIPlatform:
    lead_crm: LeadCRMService = field(default_factory=LeadCRMService)
    billing: BillingService = field(default_factory=BillingService)
    customer_portal: CustomerPortalService = field(default_factory=CustomerPortalService)
    contractor_dashboard: ContractorDashboardService = field(default_factory=ContractorDashboardService)
    yard_measurement: YardMeasurementService = field(default_factory=YardMeasurementService)
    route_optimization: RouteOptimizationService = field(default_factory=RouteOptimizationService)
    weather: WeatherIntelligenceService = field(default_factory=WeatherIntelligenceService)
    equipment: EquipmentManagementService = field(default_factory=EquipmentManagementService)
    terms: TermsAgreementService = field(default_factory=TermsAgreementService)
    estimation: EstimationService = field(default_factory=EstimationService)
