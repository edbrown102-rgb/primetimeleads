# GreenScape AI

GreenScape AI is a modular lawn-care and landscaping SaaS foundation focused on contractor automation, estimation accuracy, and operational efficiency.

## Included modules

- Lead Generation & CRM (intake, lead scoring, auto-assignment, follow-up automation)
- Proposals & Invoices (auto-generated proposals, digital signature tokens, recurring invoices, payment processing)
- Customer Portal (proposal approval, invoice payment, service requests, service history)
- Contractor Dashboard (daily schedule views, notes, crew assignment, before/after photos)
- GPS + AI Yard Measurement (polygon draw-to-measure, square-footage calculation, surface mix detection)
- Route Assist Optimization (fuel-saving nearest-stop route optimization)
- Weather Intelligence (delay logic, heat/rain/storm checks, growth-rate prediction)
- Equipment Management (runtime tracking, maintenance logs, service reminders, cost tracking, warranty fields)
- Contractor Terms & Agreements (lawn/landscaping/weather/cancellation/recurring terms + signatures)
- Material & Labor Estimation (mulch volume, sod rolls, plant quantities, mowing time, labor cost modeling)

## Code structure

- `/home/runner/work/primetimeleads/primetimeleads/greenscape_ai.py` contains production-oriented service modules and shared models.
- `/home/runner/work/primetimeleads/primetimeleads/test_greenscape_ai.py` contains focused unit tests for core module behavior.

## Run tests

```bash
python -m unittest -v /home/runner/work/primetimeleads/primetimeleads/test_greenscape_ai.py
```
