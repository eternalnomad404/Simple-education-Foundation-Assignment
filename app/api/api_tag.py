from enum import Enum


class APITag(str, Enum):
    CAMPAIGN = "Campaign"
    COHORT = "Cohort"
    TEACHER = "Teacher"
    MESSAGE = "Message"
    USER = "User"
    WEBHOOK = "Webhook"