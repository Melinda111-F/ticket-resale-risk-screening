# Ticket Resale Account Risk Screening Tool

This beginner-friendly Python project screens accounts on a fictional ticket
resale marketplace. It uses account activity and follower-network patterns to
identify accounts with unusual behaviour and sellers whose apparent popularity
may be supported mainly by high-risk accounts.

## Motivation

Peer-to-peer ticket marketplaces depend heavily on seller reputation. A seller
may appear trustworthy because many accounts follow them, but that signal is
less meaningful when most of those followers also show unusual behaviour. This
project demonstrates an explainable, rules-based way to prioritize accounts for
manual review. It does not determine that any account has committed fraud.

## How it works

1. Read account activity from `data/accounts.csv` into a nested dictionary.
2. Add follower and following relationships from `data/connections.csv`.
3. Count reciprocal connections for every account.
4. Calculate activity thresholds using quantiles from the dataset.
5. Assign one or more explainable risk groups to accounts meeting the rules.
6. Find sellers whose followers are more than 50% risk candidates.
7. Rank candidates and sellers with a manually implemented selection sort.

## Risk groups

- High messages with low listings
- High messages with low mutual connections
- High messages from a recently created account
- High following count with a low follower count

These are screening indicators for demonstration, not proof of fraud.

## Run

From the project directory:

```bash
python ticket_account_risk.py
python -m unittest discover -s tests
```

The project uses only the Python standard library.

## Skills demonstrated

- CSV file processing
- Nested dictionaries and lists
- Relationship-network analysis
- Quantile-based thresholds
- Rule-based risk classification
- Filtering and manual sorting
- Unit testing

## Data

All accounts and relationships are fictional and were created only for this
educational demonstration.
