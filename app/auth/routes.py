"""
Auth Routes (API)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta, date

from app.core.db_session import get_db
from app.auth.service import request_magic_login, verify_magic_login
from app.auth.dependencies import (
    require_user,
    get_session_context,
)
from app.users.models import User
from app.plans.subscription_models import Subscription

router = APIRouter(prefix="/api", tags=["auth"])


# =========================================================
# REQUEST MAGIC LINK
# POST /api/auth/login
# =========================================================
@router.post("/auth/login")
async def login_request(
    payload: dict,
    db: AsyncSession = Depends(get_db),
):
    email = payload.get("email")

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email required",
        )

    sent = await request_magic_login(db, email=email)

    if not sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send login link",
        )

    return {"ok": True}


# =========================================================
# VERIFY MAGIC LINK
# GET /api/auth/verify?token=xxx
# =========================================================
@router.get("/auth/verify")
async def verify_login(
    token: str = Query(...),
    next: str = Query("/dashboard"),
    db: AsyncSession = Depends(get_db),
):
    result = await verify_magic_login(db, raw_token=token)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired login link",
        )

    session_token, user = result

    existing = await db.scalar(
        select(Subscription)
        .where(Subscription.user_id == user.id)
        .where(Subscription.status.in_(["trial", "active"]))
    )

    if not existing:
        trial_start = datetime.utcnow()
        trial_end = trial_start + timedelta(days=7)

        trial = Subscription(
            user_id=user.id,
            plan_id=1,               # FREE plan as trial base
            payment_id=None,
            status="trial",
            billing_cycle="trial",
            starts_at=trial_start,
            ends_at=trial_end,
            is_trial=True,
            is_active=True,
            trial_start=date.today(),
            trial_end=date.today() + timedelta(days=7),
            ai_campaign_limit_snapshot=3,
            created_by_admin=False,
            assigned_by_admin=False,
            razorpay_subscription_id=None,
        )

        db.add(trial)
        await db.commit()

    response = RedirectResponse(
        url=next,
        status_code=status.HTTP_302_FOUND,
    )

    response.set_cookie(
        key="meta_ai_session",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=60 * 60 * 24 * 3,
    )

    return response


# =========================================================
# GET /api/auth/me
# =========================================================
@router.get("/auth/me")
async def auth_me(
    user: User = Depends(require_user),
):
    return {
        "id": str(user.id),
        "email": user.email,
        "role": user.role,
    }


# =========================================================
# POST /api/auth/logout
# =========================================================
@router.post("/auth/logout")
async def logout(
    _: User = Depends(require_user),
):
    response = RedirectResponse(
        url="/login",
        status_code=status.HTTP_302_FOUND,
    )

    response.delete_cookie(key="meta_ai_session", path="/")
    return response


# =========================================================
# GET /api/session/context
# =========================================================
@router.get("/session/context")
async def session_context(
    context: dict = Depends(get_session_context),
):
    return context
