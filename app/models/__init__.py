# Import ALL models here to register them with SQLAlchemy
# ⚠️ Order matters — keep models only, no logic

# 1. Global Configuration (No dependencies)
from app.admin.models import GlobalSettings

# 2. Base dependencies (Payment, Invoice, Billing Providers)
from app.billing.payment_models import Payment
from app.billing.invoice_models import Invoice
from app.billing.provider_models import BillingProvider  # <-- ADDED

# 3. Plans and Subscriptions (depend on Payment)
from app.plans.models import Plan
from app.plans.subscription_models import Subscription

# 4. User (Depends on Subscription)
from app.users.models import User

# 5. Auth models
from app.auth.models import MagicLoginToken, Session

# 6. Feature models
from app.meta_api.models import MetaAdAccount, UserMetaAdAccount, MetaOAuthToken
from app.campaigns.models import Campaign
from app.ai_engine.models import AIAction
