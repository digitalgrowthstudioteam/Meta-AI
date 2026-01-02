"""
Central SQLAlchemy model registry.

Importing this file guarantees that ALL models
are registered on the canonical Base before
any DB session or mapper initialization occurs.
"""

# Users
from app.users.models import User

# Auth
from app.auth.models import Session, MagicLoginToken

# Plans & Subscriptions
from app.plans.models import Plan
from app.plans.subscription_models import Subscription
