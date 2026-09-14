"""Constants and type aliases for the ticket marketplace risk screener."""

AccountData = dict[str, str | int | list[str]]
MarketplaceData = dict[str, AccountData]

ACCOUNT_CREATED = "account_created"
NUM_LISTINGS = "num_listings"
NUM_MESSAGES = "num_messages"
FOLLOWERS = "followers"
FOLLOWING = "following"
NUM_MUTUALS = "num_mutuals"
RISK_GROUPS = "risk_groups"

SEP = ","

ACCOUNT_ID_COL = 0
ACCOUNT_CREATED_COL = 1
NUM_LISTINGS_COL = 2
NUM_MESSAGES_COL = 3
FOLLOWER_COL = 0
FOLLOWING_COL = 1

HIGH_MESSAGES_LOW_LISTINGS = "highMessagesLowListings"
HIGH_MESSAGES_LOW_MUTUALS = "highMessagesLowMutuals"
HIGH_MESSAGES_NEW_ACCOUNT = "highMessagesNewAccount"
HIGH_FOLLOWING_LOW_FOLLOWERS = "highFollowingLowFollowers"

P_HIGH_MESSAGES = 0.80
P_VERY_HIGH_MESSAGES = 0.90
P_LOW_LISTINGS = 0.20
P_LOW_MUTUALS = 0.20
NEW_ACCOUNT_DATE = "2026-01-01"
FOLLOWING_TO_FOLLOWER_FACTOR = 2
