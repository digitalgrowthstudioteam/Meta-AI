# Import ALL models here to register them with SQLAlchemy
# ⚠️ Order matters — keep models only, no logic

from app.users.models import User

from app.plans.models import Plan
from app.plans.subscription_models import Subscription

from app.auth.models import MagicLoginToken, Session

from app.meta_api.models import MetaAdAccount, UserMetaAdAccount, MetaOAuthToken
from app.campaigns.models import Campaign

from app.ai_engine.models import AIAction

from app.billing.payment_models import Payment
from app.billing.invoice_models import Invoice
