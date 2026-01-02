# Import ALL models here to register them with SQLAlchemy
# ⚠️ This file must contain ONLY model imports

# ======================
# Users
# ======================
from app.users.models import User

# ======================
# Plans & Subscriptions
# ======================
from app.plans.models import Plan
from app.plans.subscription_models import Subscription

# ======================
# Authentication
# ======================
from app.auth.models import MagicLoginToken, Session

# ======================
# Meta API (REAL FILE)
# ======================
from app.meta_api.models import (
    MetaAdAccount,
    UserMetaAdAccount,
    MetaOAuthToken,
)

# ======================
# AI / Audience (REAL PATHS)
# ======================
from app.ai_engine.models import AIAction
from app.audience_engine.models import AudienceInsight

# ======================
# Billing
# ======================
from app.billing.payment_models import Payment
from app.billing.invoice_models import Invoice
