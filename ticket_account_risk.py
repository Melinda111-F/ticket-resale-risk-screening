"""Screen ticket-resale marketplace accounts using explainable network rules."""

import csv
from copy import deepcopy
from pathlib import Path
from typing import TextIO

from constants import (
    MarketplaceData,
    ACCOUNT_CREATED,
    NUM_LISTINGS,
    NUM_MESSAGES,
    FOLLOWERS,
    FOLLOWING,
    NUM_MUTUALS,
    RISK_GROUPS,
    SEP,
    ACCOUNT_ID_COL,
    ACCOUNT_CREATED_COL,
    NUM_LISTINGS_COL,
    NUM_MESSAGES_COL,
    FOLLOWER_COL,
    FOLLOWING_COL,
    HIGH_MESSAGES_LOW_LISTINGS,
    HIGH_MESSAGES_LOW_MUTUALS,
    HIGH_MESSAGES_NEW_ACCOUNT,
    HIGH_FOLLOWING_LOW_FOLLOWERS,
    P_HIGH_MESSAGES,
    P_VERY_HIGH_MESSAGES,
    P_LOW_LISTINGS,
    P_LOW_MUTUALS,
    NEW_ACCOUNT_DATE,
    FOLLOWING_TO_FOLLOWER_FACTOR,
)


def create_accounts_dictionary(accounts_file: TextIO) -> MarketplaceData:
    """Return marketplace account data created from an open CSV file."""
    accounts = {}
    accounts_file.readline()

    for line in accounts_file:
        values = line.strip().split(SEP)
        if len(values) != 4:
            continue

        account_id = values[ACCOUNT_ID_COL].strip()
        if account_id == "":
            continue

        accounts[account_id] = {
            ACCOUNT_CREATED: values[ACCOUNT_CREATED_COL].strip(),
            NUM_LISTINGS: int(values[NUM_LISTINGS_COL]),
            NUM_MESSAGES: int(values[NUM_MESSAGES_COL]),
            FOLLOWERS: [],
            FOLLOWING: [],
            RISK_GROUPS: [],
        }

    return accounts


def add_account_connections(accounts: MarketplaceData,
                            connections_file: TextIO) -> None:
    """Add valid, non-duplicate follower relationships from an open CSV file."""
    connections_file.readline()

    for line in connections_file:
        values = line.strip().split(SEP)
        if len(values) != 2:
            continue

        follower = values[FOLLOWER_COL].strip()
        following = values[FOLLOWING_COL].strip()

        if follower not in accounts or following not in accounts:
            continue

        if follower not in accounts[following][FOLLOWERS]:
            accounts[following][FOLLOWERS].append(follower)
        if following not in accounts[follower][FOLLOWING]:
            accounts[follower][FOLLOWING].append(following)


def add_num_mutual_connections(accounts: MarketplaceData) -> None:
    """Add each account's number of reciprocal follower relationships."""
    for account_id in accounts:
        count = 0
        for followed_account in accounts[account_id][FOLLOWING]:
            if followed_account in accounts[account_id][FOLLOWERS]:
                count += 1
        accounts[account_id][NUM_MUTUALS] = count


def get_quantile(integers: list[int], p: float) -> int:
    """Return the p-quantile using the nearest-rank-below rule, or -1 if invalid."""
    if integers == [] or p < 0 or p > 1:
        return -1

    sorted_integers = sorted(integers)
    index = int(p * (len(sorted_integers) - 1))
    return sorted_integers[index]


def add_risk_candidate_groups(accounts: MarketplaceData) -> None:
    """Add explainable, data-relative risk groups to marketplace accounts."""
    listings = []
    messages = []
    mutuals = []

    for account_id in accounts:
        listings.append(accounts[account_id][NUM_LISTINGS])
        messages.append(accounts[account_id][NUM_MESSAGES])
        mutuals.append(accounts[account_id][NUM_MUTUALS])

    high_messages = get_quantile(messages, P_HIGH_MESSAGES)
    very_high_messages = get_quantile(messages, P_VERY_HIGH_MESSAGES)
    low_listings = get_quantile(listings, P_LOW_LISTINGS)
    low_mutuals = get_quantile(mutuals, P_LOW_MUTUALS)

    for account_id in accounts:
        account = accounts[account_id]
        groups = account[RISK_GROUPS]

        if (account[NUM_MESSAGES] >= very_high_messages
                and account[NUM_LISTINGS] <= low_listings):
            groups.append(HIGH_MESSAGES_LOW_LISTINGS)

        if (account[NUM_MESSAGES] >= high_messages
                and account[NUM_MUTUALS] <= low_mutuals):
            groups.append(HIGH_MESSAGES_LOW_MUTUALS)

        if (account[NUM_MESSAGES] >= high_messages
                and account[ACCOUNT_CREATED] >= NEW_ACCOUNT_DATE):
            groups.append(HIGH_MESSAGES_NEW_ACCOUNT)

        if (len(account[FOLLOWING])
                > FOLLOWING_TO_FOLLOWER_FACTOR * len(account[FOLLOWERS])):
            groups.append(HIGH_FOLLOWING_LOW_FOLLOWERS)


def find_all_risk_candidates(accounts: MarketplaceData) -> MarketplaceData:
    """Return a new dictionary containing accounts with at least one risk group."""
    candidates = {}
    for account_id in accounts:
        if accounts[account_id][RISK_GROUPS] != []:
            candidates[account_id] = deepcopy(accounts[account_id])
    return candidates


def find_sellers_manipulating_trust(accounts: MarketplaceData) -> MarketplaceData:
    """Return sellers whose followers are more than 50% risk candidates."""
    sellers = {}

    for account_id in accounts:
        followers = accounts[account_id][FOLLOWERS]
        if accounts[account_id][NUM_LISTINGS] == 0 or followers == []:
            continue

        risk_follower_count = 0
        for follower in followers:
            if accounts[follower][RISK_GROUPS] != []:
                risk_follower_count += 1

        if risk_follower_count > len(followers) / 2:
            sellers[account_id] = deepcopy(accounts[account_id])

    return sellers


def order_risk_candidates(accounts: MarketplaceData) -> list[str]:
    """Return candidates ordered by risk-group count, then account ID."""
    ordered = list(find_all_risk_candidates(accounts))

    for i in range(len(ordered)):
        largest = i
        for j in range(i + 1, len(ordered)):
            current_count = len(accounts[ordered[j]][RISK_GROUPS])
            largest_count = len(accounts[ordered[largest]][RISK_GROUPS])
            if (current_count > largest_count
                    or (current_count == largest_count
                        and ordered[j] > ordered[largest])):
                largest = j
        ordered[i], ordered[largest] = ordered[largest], ordered[i]

    return ordered


def order_sellers_manipulating_trust(accounts: MarketplaceData) -> list[str]:
    """Return flagged sellers ordered by risky-follower count, then account ID."""
    ordered = list(find_sellers_manipulating_trust(accounts))
    risk_follower_counts = {}

    for account_id in ordered:
        count = 0
        for follower in accounts[account_id][FOLLOWERS]:
            if accounts[follower][RISK_GROUPS] != []:
                count += 1
        risk_follower_counts[account_id] = count

    for i in range(len(ordered)):
        largest = i
        for j in range(i + 1, len(ordered)):
            current_count = risk_follower_counts[ordered[j]]
            largest_count = risk_follower_counts[ordered[largest]]
            if (current_count > largest_count
                    or (current_count == largest_count
                        and ordered[j] > ordered[largest])):
                largest = j
        ordered[i], ordered[largest] = ordered[largest], ordered[i]

    return ordered


def export_power_bi_data(accounts: MarketplaceData,
                         output_directory: str | Path = "output") -> None:
    """Write flat account and risk-group tables for a Power BI report."""
    output_path = Path(output_directory)
    output_path.mkdir(parents=True, exist_ok=True)

    candidates = set(find_all_risk_candidates(accounts))
    flagged_sellers = set(find_sellers_manipulating_trust(accounts))
    candidate_order = order_risk_candidates(accounts)
    seller_order = order_sellers_manipulating_trust(accounts)
    candidate_ranks = {
        account_id: rank
        for rank, account_id in enumerate(candidate_order, start=1)
    }
    seller_ranks = {
        account_id: rank
        for rank, account_id in enumerate(seller_order, start=1)
    }

    readable_group_names = {
        HIGH_MESSAGES_LOW_LISTINGS: "High messages with low listings",
        HIGH_MESSAGES_LOW_MUTUALS: "High messages with low mutual connections",
        HIGH_MESSAGES_NEW_ACCOUNT: "High messages from a new account",
        HIGH_FOLLOWING_LOW_FOLLOWERS: "High following with low followers",
    }

    summary_fields = [
        "account_id",
        "account_created",
        "num_listings",
        "num_messages",
        "num_followers",
        "num_following",
        "num_mutuals",
        "risk_group_count",
        "risk_groups",
        "is_risk_candidate",
        "risk_candidate_rank",
        "risky_follower_count",
        "risky_follower_share",
        "is_seller_trust_risk",
        "seller_trust_risk_rank",
    ]

    with (output_path / "power_bi_account_risk_summary.csv").open(
            "w", encoding="utf-8", newline="") as summary_file:
        writer = csv.DictWriter(summary_file, fieldnames=summary_fields)
        writer.writeheader()

        for account_id, account in accounts.items():
            followers = account[FOLLOWERS]
            risky_follower_count = sum(
                1 for follower in followers if follower in candidates
            )
            risky_follower_share = (
                risky_follower_count / len(followers) if followers else 0.0
            )
            readable_groups = [
                readable_group_names[group] for group in account[RISK_GROUPS]
            ]

            writer.writerow({
                "account_id": account_id,
                "account_created": account[ACCOUNT_CREATED],
                "num_listings": account[NUM_LISTINGS],
                "num_messages": account[NUM_MESSAGES],
                "num_followers": len(followers),
                "num_following": len(account[FOLLOWING]),
                "num_mutuals": account[NUM_MUTUALS],
                "risk_group_count": len(account[RISK_GROUPS]),
                "risk_groups": " | ".join(readable_groups),
                "is_risk_candidate": account_id in candidates,
                "risk_candidate_rank": candidate_ranks.get(account_id, ""),
                "risky_follower_count": risky_follower_count,
                "risky_follower_share": round(risky_follower_share, 4),
                "is_seller_trust_risk": account_id in flagged_sellers,
                "seller_trust_risk_rank": seller_ranks.get(account_id, ""),
            })

    detail_fields = ["account_id", "risk_group", "risk_group_code"]
    with (output_path / "power_bi_risk_group_details.csv").open(
            "w", encoding="utf-8", newline="") as detail_file:
        writer = csv.DictWriter(detail_file, fieldnames=detail_fields)
        writer.writeheader()
        for account_id, account in accounts.items():
            for group in account[RISK_GROUPS]:
                writer.writerow({
                    "account_id": account_id,
                    "risk_group": readable_group_names[group],
                    "risk_group_code": group,
                })


def main() -> None:
    """Run the account-risk screening pipeline on the sample files."""
    with open("data/accounts.csv", "r", encoding="utf-8") as accounts_file:
        accounts = create_accounts_dictionary(accounts_file)

    with open("data/connections.csv", "r", encoding="utf-8") as connections_file:
        add_account_connections(accounts, connections_file)

    add_num_mutual_connections(accounts)
    add_risk_candidate_groups(accounts)
    export_power_bi_data(accounts)

    print("Risk candidates:")
    for account_id in order_risk_candidates(accounts):
        print(account_id, accounts[account_id][RISK_GROUPS])

    print("\nSellers potentially manipulating trust:")
    print(order_sellers_manipulating_trust(accounts))

    print("\nPower BI data written to the output directory.")


if __name__ == "__main__":
    main()
