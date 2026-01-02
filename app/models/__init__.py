# app/models/__init__.py
"""
Central SQLAlchemy model registry.

IMPORTANT:
- This file MUST import all models exactly once
- Ensures foreign keys resolve correctly
- Prevents NoReferencedTableError
"""

# Core models
from app.users.models import User
from app.plans.plan_models import Plan
from app.plans.subscription_models import Subscription

# Auth
from app.auth.models import MagicLoginToken
from app.auth.session_models import Session

# Meta
from app.meta_api.models import MetaOAuthToken
from app.meta_api.ad_account_models import MetaAdAccount, UserMetaAdAccount

# Campaigns
from app.campaigns.models import Campaign

# AI / Analytics
from app.ai.models import AIAction
from app.audience.models import AudienceInsight

# Billing
from app.billing.payment_models import Payment
from app.billing.invoice_models import Invoice
