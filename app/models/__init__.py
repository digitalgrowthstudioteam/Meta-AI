# Import ALL models here to register them with SQLAlchemy
# ⚠️ This file MUST ONLY contain model imports

# ======================
# Core Domain Models
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
# Meta API
# ======================
from app.meta_api.models import MetaAdAccount, Campaign

# ======================
# AI Engine
# ======================
from app.ai.models import AIAction
from app.ai.audience_models import AudienceInsight

# ======================
# Billing
# ======================
from app.billing.payment_models import Payment
from app.billing.invoice_models import Invoice
