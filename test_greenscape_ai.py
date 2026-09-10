import unittest
from datetime import date, timedelta

from greenscape_ai import (
    Contractor,
    Equipment,
    EstimationService,
    GreenScapeAIPlatform,
    Lead,
    LineItem,
    RouteStop,
    WeatherSnapshot,
)


class GreenScapeAITests(unittest.TestCase):
    def test_lead_scoring_and_assignment(self):
        platform = GreenScapeAIPlatform()
        lead = Lead(
            id="L1",
            customer_name="Alex",
            address="123 Main St, Tampa",
            requested_services=["mowing", "mulch"],
            property_square_feet=4500,
            budget=1200,
            urgency="high",
        )

        self.assertGreaterEqual(platform.lead_crm.score_lead(lead), 70)

        contractor = platform.lead_crm.auto_assign(
            lead,
            [
                Contractor(id="C1", name="Crew A", service_areas=["Tampa"], specialties=["mowing"], active_jobs=1),
                Contractor(id="C2", name="Crew B", service_areas=["Orlando"], specialties=["trees"], active_jobs=0),
            ],
        )

        self.assertIsNotNone(contractor)
        self.assertEqual(contractor.id, "C1")

    def test_proposal_invoice_payment_flow(self):
        platform = GreenScapeAIPlatform()
        proposal = platform.billing.generate_proposal(
            customer_id="cust_1",
            line_items=[LineItem("Weekly mowing", 4, 55), LineItem("Bed edging", 1, 80)],
            terms="Standard lawn terms",
        )

        invoice = platform.billing.create_invoice(proposal, recurring_interval_days=30)
        self.assertEqual(invoice.amount_due, 300)
        self.assertEqual(platform.billing.next_recurring_invoice_date(invoice), invoice.due_date + timedelta(days=30))
        self.assertTrue(platform.customer_portal.pay_invoice(platform.billing, invoice, 300))

    def test_yard_measurement_route_weather_and_estimation(self):
        platform = GreenScapeAIPlatform()

        area = platform.yard_measurement.polygon_square_footage([(0, 0), (40, 0), (40, 30), (0, 30)])
        self.assertEqual(area, 1200)
        mix = platform.yard_measurement.detect_surface_mix({"grass": 80, "mulch": 20})
        self.assertEqual(set(mix.keys()), {"grass", "mulch", "trees", "driveway"})

        origin = RouteStop("O", 28.0, -82.0)
        stops = [RouteStop("A", 28.01, -82.01), RouteStop("B", 28.5, -82.5)]
        route = platform.route_optimization.optimize(origin, stops)
        self.assertEqual(route[0].id, "A")

        weather = WeatherSnapshot(rain_probability=0.8, heat_index=95, storm_alert=False, rainfall_inches_week=0.6, average_temp_f=80)
        self.assertTrue(platform.weather.should_delay_service(weather))
        self.assertEqual(platform.weather.grass_growth_rate(weather), "fast")

        estimator = EstimationService()
        self.assertEqual(estimator.mulch_cubic_yards(540, 3), 5.0)
        self.assertEqual(estimator.mulch_cubic_yards(-10, 3), 0.0)
        self.assertEqual(estimator.mulch_cubic_yards(100, -1), 0.0)
        self.assertEqual(estimator.labor_cost(3.5, 45, 2), 315)
        self.assertEqual(estimator.mowing_time_hours(-100), 0.0)
        self.assertEqual(estimator.sod_area_rolls(101, 10.5), 10)
        self.assertEqual(estimator.sod_area_rolls(101, 0), 0)
        self.assertEqual(estimator.labor_cost(-1, 45, 2), 0)
        self.assertEqual(estimator.labor_cost(2, -5, 3), 0)
        self.assertEqual(estimator.labor_cost(2, 25, -2), 0)

    def test_equipment_runtime_and_reminders(self):
        platform = GreenScapeAIPlatform()
        mower = Equipment(id="E1", name="ZTR Mower", runtime_hours=48)
        platform.equipment.add_runtime(mower, 3)
        reminders = platform.equipment.service_reminders(mower)
        self.assertIn("oil change", reminders)

        platform.equipment.log_maintenance(mower, "Oil change complete", 35, task="oil change")
        self.assertEqual(mower.total_cost, 35)
        self.assertNotIn("oil change", platform.equipment.service_reminders(mower))

    def test_terms_signature_is_deterministic(self):
        platform = GreenScapeAIPlatform()
        terms = platform.terms.generate_terms(["lawn_care", "weather_delay"])
        sig_a = platform.terms.sign("cust_1", terms)
        sig_b = platform.terms.sign("cust_1", terms)
        self.assertEqual(sig_a, sig_b)

    def test_customer_service_request_and_history(self):
        platform = GreenScapeAIPlatform()
        request = platform.customer_portal.request_service("cust_2", "fertilizer", date.today(), "Backyard only")
        self.assertEqual(request.service_type, "fertilizer")
        self.assertEqual(len(platform.customer_portal.service_requests), 1)
        history = platform.customer_portal.view_service_history(["Mowing - complete", "Mulch refresh - complete"])
        self.assertEqual(len(history), 2)


if __name__ == "__main__":
    unittest.main()
