# Concert Ticket Resale Risk Screening Tool

## Project motivation

Online ticket resale listings can present several signals that are difficult to
evaluate consistently, including unusual pricing, limited seller history,
off-platform payment requests, unclear transfer evidence, and uncertain VIP
benefit eligibility. This project explores how transparent, rule-based analysis
can combine those signals into a consistent preliminary risk assessment.

This project is an original, educational risk-screening pipeline. It evaluates
synthetic ticket-resale listings, explains which signals raised concern, and
produces an auditable report. It is not affiliated with Ticketmaster or any other
ticketing platform and should not be used as the sole basis for a real purchase.

## What it does

- validates CSV records and rejects malformed values;
- assigns a transparent risk score from 0 to 100;
- classifies listings as Low, Medium, or High risk;
- records every rule that contributed to the score;
- summarizes risk distribution and evaluates results against synthetic labels;
- generates a chart and a machine-readable JSON summary;
- includes automated tests for scoring, boundaries, and invalid input.

## Risk signals

The model considers seller history, complaint rate, price deviation, requests for
off-platform payment, proof of ticket transfer, VIP-benefit confirmation, seller
rating, refund policy, and urgency pressure. The rules are intentionally
explainable: each output row contains both the score and the reasons.

## Demonstration results

On the included set of 250 reproducible synthetic listings, the pipeline
classified 167 as Low risk, 11 as Medium risk, and 72 as High risk. Against the
synthetic reference labels, the High-risk classification achieved 98.61%
precision and 92.21% recall. These figures describe only the generated
demonstration data and are not estimates of real-world fraud performance.

![Ticket resale listing risk distribution](output/risk_distribution.png)

## Run the project

```bash
python3 generate_sample_data.py --rows 250
python3 ticket_risk.py data/sample_listings.csv output/risk_report.csv
python3 analyze_results.py output/risk_report.csv output
python3 -m unittest discover -s tests -v
```

Install charting dependencies first:

```bash
python3 -m pip install -r requirements.txt
```

## Files

- `ticket_risk.py`: validation, scoring, classification, and CSV pipeline
- `generate_sample_data.py`: deterministic synthetic-data generator
- `analyze_results.py`: summary metrics and visualization
- `tests/test_ticket_risk.py`: automated unit tests
- `data/sample_listings.csv`: synthetic input data
- `output/risk_report.csv`: scored output
- `output/summary.json`: aggregate results and evaluation metrics
- `output/risk_distribution.png`: risk-level visualization

## Limitations and next steps

The labels and records are synthetic, and the scoring weights are judgment-based,
not learned from verified fraud outcomes. A production model would require real
consented data, bias and calibration testing, monitoring for changing fraud
patterns, privacy controls, and human review of high-risk cases.
