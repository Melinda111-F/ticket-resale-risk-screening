"""Screen ticket-resale marketplace accounts using explainable network rules."""

from copy import deepcopy
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


def main() -> None:
    """Run the account-risk screening pipeline on the sample files."""
    with open("data/accounts.csv", "r", encoding="utf-8") as accounts_file:
        accounts = create_accounts_dictionary(accounts_file)

    with open("data/connections.csv", "r", encoding="utf-8") as connections_file:
        add_account_connections(accounts, connections_file)

    add_num_mutual_connections(accounts)
    add_risk_candidate_groups(accounts)

    print("Risk candidates:")
    for account_id in order_risk_candidates(accounts):
        print(account_id, accounts[account_id][RISK_GROUPS])

    print("\nSellers potentially manipulating trust:")
    print(order_sellers_manipulating_trust(accounts))


if __name__ == "__main__":
    main()
