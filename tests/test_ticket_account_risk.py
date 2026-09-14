"""Tests for the ticket marketplace account-risk functions."""

import io
import unittest

from constants import FOLLOWERS, FOLLOWING, NUM_MUTUALS, RISK_GROUPS
from ticket_account_risk import (
    add_account_connections,
    add_num_mutual_connections,
    add_risk_candidate_groups,
    create_accounts_dictionary,
    find_all_risk_candidates,
    find_sellers_manipulating_trust,
    get_quantile,
    order_risk_candidates,
)


ACCOUNTS_CSV = """account_id,account_created,num_listings,num_messages
safe_seller,2022-01-01,20,10
new_busy,2026-05-01,0,100
networked,2024-01-01,3,40
"""

CONNECTIONS_CSV = """follower,following
new_busy,safe_seller
networked,safe_seller
safe_seller,networked
networked,safe_seller
unknown,safe_seller
"""


class TestTicketAccountRisk(unittest.TestCase):
    def setUp(self) -> None:
        self.accounts = create_accounts_dictionary(io.StringIO(ACCOUNTS_CSV))
        add_account_connections(self.accounts, io.StringIO(CONNECTIONS_CSV))

    def test_create_accounts_dictionary(self) -> None:
        self.assertEqual(len(self.accounts), 3)
        self.assertEqual(self.accounts["new_busy"][RISK_GROUPS], [])

    def test_connections_ignore_duplicates_and_unknown_accounts(self) -> None:
        self.assertEqual(
            self.accounts["safe_seller"][FOLLOWERS], ["new_busy", "networked"]
        )
        self.assertEqual(self.accounts["networked"][FOLLOWING], ["safe_seller"])

    def test_add_num_mutual_connections(self) -> None:
        add_num_mutual_connections(self.accounts)
        self.assertEqual(self.accounts["safe_seller"][NUM_MUTUALS], 1)
        self.assertEqual(self.accounts["networked"][NUM_MUTUALS], 1)

    def test_get_quantile(self) -> None:
        self.assertEqual(get_quantile([5, 2, 1, 3, 4], 0.5), 3)
        self.assertEqual(get_quantile([], 0.5), -1)
        self.assertEqual(get_quantile([1, 2], 1.1), -1)

    def test_risk_pipeline(self) -> None:
        add_num_mutual_connections(self.accounts)
        add_risk_candidate_groups(self.accounts)
        candidates = find_all_risk_candidates(self.accounts)
        self.assertIn("new_busy", candidates)
        self.assertNotEqual(order_risk_candidates(self.accounts), [])

    def test_find_sellers_manipulating_trust(self) -> None:
        add_num_mutual_connections(self.accounts)
        for account_id in self.accounts:
            self.accounts[account_id][RISK_GROUPS] = []
        self.accounts["new_busy"][RISK_GROUPS] = ["risk"]
        self.accounts["networked"][RISK_GROUPS] = ["risk"]
        flagged = find_sellers_manipulating_trust(self.accounts)
        self.assertIn("safe_seller", flagged)


if __name__ == "__main__":
    unittest.main()
