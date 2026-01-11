# Import ALL models here to register them with SQLAlchemy
# ⚠️ Order matters — keep models only, no logic

# 1. Base dependencies (Payment, Invoice) must be first
from app.billing.payment_models import Payment
from app.billing.invoice_models import Invoice

# 2. Plans and Subscriptions (depend on Payment)
from app.plans.models import Plan
from app.plans.subscription_models import Subscription

# 3. User (likely depends on Subscription/Payment)
from app.users.models import User

# 4. Auth models
from app.auth.models import MagicLoginToken, Session

# 5. Feature models
from app.meta_api.models import MetaAdAccount, UserMetaAdAccount, MetaOAuthToken
from app.campaigns.models import Campaign
from app.ai_engine.models import AIAction
