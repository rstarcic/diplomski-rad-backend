import asyncio
from datetime import datetime, timedelta, timezone

from app.applications.models import Application
from app.dashboard.schemas import (
    DashboardListItem,
    DashboardPaymentSummary,
    DashboardResponse,
    DashboardStatCard,
)
from app.integrations.client import (
    get_contract_dashboard_summary,
    get_payment_dashboard_summary,
)
from app.jobs.models import Job
from app.profiles.models import Profile
from app.reviews.models import Review
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session


def _money(amount_minor: int, currency: str = "EUR") -> str:
    symbol = "€" if currency.upper() == "EUR" else f"{currency.upper()} "
    return f"{symbol}{amount_minor / 100:,.2f}"


def _relative_time(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    seconds = max(0, int((datetime.now(timezone.utc) - value).total_seconds()))
    if seconds < 60:
        return "Just now"
    if seconds < 3600:
        return f"{seconds // 60} min ago"
    if seconds < 86400:
        return f"{seconds // 3600} hours ago"
    if seconds < 172800:
        return "Yesterday"
    return f"{seconds // 86400} days ago"


async def get_dashboard(
    db: Session,
    current_user: Profile,
) -> DashboardResponse:
    contracts, payments = await asyncio.gather(
        get_contract_dashboard_summary(current_user.user_id, current_user.role),
        get_payment_dashboard_summary(current_user.user_id, current_user.role),
    )

    if current_user.role == "client":
        return _client_dashboard(db, current_user, contracts, payments)
    return _contractor_dashboard(db, current_user, contracts, payments)


def _client_dashboard(db, user, contracts, payments) -> DashboardResponse:
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    week_start = (
        now - timedelta(days=now.weekday())
    ).replace(hour=0, minute=0, second=0, microsecond=0)
    active_work_statuses = (
        "awaiting_contract",
        "in_progress",
        "done_by_contractor",
    )
    active_job_filter = or_(
        and_(Job.status == "open", Job.deadline > now),
        Job.status.in_(active_work_statuses),
    )

    active_jobs = (
        db.query(func.count(Job.id))
        .filter(Job.client_id == user.user_id, active_job_filter)
        .scalar()
    )
    new_jobs = (
        db.query(func.count(Job.id))
        .filter(
            Job.client_id == user.user_id,
            active_job_filter,
            Job.created_at >= month_start,
        )
        .scalar()
    )
    applications = (
        db.query(func.count(Application.id))
        .join(Job, Job.id == Application.job_id)
        .filter(Job.client_id == user.user_id, Application.status != "withdrawn")
        .scalar()
    )
    weekly_applications = (
        db.query(func.count(Application.id))
        .join(Job, Job.id == Application.job_id)
        .filter(
            Job.client_id == user.user_id,
            Application.status != "withdrawn",
            Application.created_at >= week_start,
        )
        .scalar()
    )

    recent_applications = (
        db.query(Application, Job, Profile)
        .join(Job, Job.id == Application.job_id)
        .join(Profile, Profile.user_id == Application.contractor_id)
        .filter(Job.client_id == user.user_id)
        .order_by(Application.created_at.desc())
        .limit(5)
        .all()
    )
    activities = [
        DashboardListItem(
            id=f"application-{application.id}",
            title="New application received",
            subtitle=(
                f"{contractor.full_name or 'A contractor'} applied to "
                f"{job.title}."
            ),
            meta=_relative_time(application.created_at),
        )
        for application, job, contractor in recent_applications
    ]
    activities.extend(
        DashboardListItem(
            id=f"payment-{item.id}",
            title="Payment updated",
            subtitle=f"{item.job_title} payment is {item.status}.",
            meta=_relative_time(item.updated_at),
        )
        for item in payments.recent
    )
    activities = sorted(
        activities,
        key=lambda item: item.meta == "Just now",
        reverse=True,
    )[:5]

    pending_rows = (
        db.query(Job, func.count(Application.id))
        .join(Application, Application.job_id == Job.id)
        .filter(
            Job.client_id == user.user_id,
            Job.status == "open",
            Application.status == "pending",
        )
        .group_by(Job.id)
        .order_by(func.count(Application.id).desc())
        .limit(3)
        .all()
    )
    actions = [
        DashboardListItem(
            id=f"review-applications-{job.id}",
            title="Review new applications",
            subtitle=(
                f"{count} candidate{'s' if count != 1 else ''} waiting for "
                f"feedback for {job.title}."
            ),
            meta="High priority",
            metaAccent="warning",
        )
        for job, count in pending_rows
    ]
    if contracts.pending_signature_count:
        actions.append(
            DashboardListItem(
                id="pending-contract-signatures",
                title="Contract signature required",
                subtitle=(
                    f"{contracts.pending_signature_count} contract"
                    f"{'s are' if contracts.pending_signature_count != 1 else ' is'} "
                    "waiting for signatures."
                ),
                meta="Due soon",
                metaAccent="warning",
            )
        )

    return DashboardResponse(
        stats_cards=[
            DashboardStatCard(
                id="active_jobs",
                title="Active jobs",
                value=active_jobs,
                subtitle=f"+{new_jobs} new this month",
            ),
            DashboardStatCard(
                id="applications",
                title="Applications",
                value=applications,
                subtitle=f"+{weekly_applications} new this week",
            ),
            DashboardStatCard(
                id="signed_contracts",
                title="Signed contracts",
                value=contracts.signed_count,
                subtitle="Total signed",
            ),
            DashboardStatCard(
                id="hiring_spend",
                title="Hiring spend",
                value=_money(payments.paid_total_minor, payments.currency),
                subtitle=(
                    f"{_money(payments.paid_this_month_minor, payments.currency)} "
                    "this month"
                ),
            ),
        ],
        recent_activity=activities,
        pending_actions=actions[:3],
        payment_summary=_payment_summary(payments, client=True),
    )


def _contractor_dashboard(db, user, contracts, payments) -> DashboardResponse:
    terminal_jobs = (
        db.query(Job.status, func.count(Job.id))
        .join(Application, Application.job_id == Job.id)
        .filter(
            Application.contractor_id == user.user_id,
            Application.status == "accepted",
            Job.status.in_(("completed_by_client", "incomplete")),
        )
        .group_by(Job.status)
        .all()
    )
    totals = dict(terminal_jobs)
    completed = totals.get("completed_by_client", 0)
    terminal_total = completed + totals.get("incomplete", 0)
    success_rate = round(completed / terminal_total * 100) if terminal_total else 0

    rating = (
        db.query(
            func.avg(
                (
                    Review.communication_rating
                    + Review.clarity_rating
                    + Review.reliability_rating
                    + Review.collaboration_rating
                )
                / 4
            )
        )
        .filter(
            Review.target_type == "contractor",
            Review.target_id == user.user_id,
        )
        .scalar()
    )
    rating = float(rating or 0)

    recent_applications = (
        db.query(Application, Job)
        .join(Job, Job.id == Application.job_id)
        .filter(Application.contractor_id == user.user_id)
        .order_by(Application.updated_at.desc())
        .limit(5)
        .all()
    )
    activities = [
        DashboardListItem(
            id=f"application-{application.id}",
            title=(
                "Application approved"
                if application.status == "accepted"
                else "Application updated"
            ),
            subtitle=f"Your application for {job.title} is {application.status}.",
            meta=_relative_time(application.updated_at),
        )
        for application, job in recent_applications
    ]
    activities.extend(
        DashboardListItem(
            id=f"payment-{item.id}",
            title="Payment released" if item.status == "paid" else "Payment updated",
            subtitle=(
                f"{_money(item.amount_minor, item.currency)} for "
                f"{item.job_title} is {item.status}."
            ),
            meta=_relative_time(item.updated_at),
        )
        for item in payments.recent
    )

    actions = []
    if contracts.pending_signature_count:
        actions.append(
            DashboardListItem(
                id="pending-contract-signatures",
                title="Client waiting for signature",
                subtitle=(
                    f"{contracts.pending_signature_count} contract"
                    f"{'s need' if contracts.pending_signature_count != 1 else ' needs'} "
                    "your attention."
                ),
                meta="Due soon",
                metaAccent="warning",
            )
        )
    pending_applications = (
        db.query(func.count(Application.id))
        .filter(
            Application.contractor_id == user.user_id,
            Application.status.in_(("pending", "selected")),
        )
        .scalar()
    )
    if pending_applications:
        actions.append(
            DashboardListItem(
                id="pending-applications",
                title="Applications in progress",
                subtitle=(
                    f"You have {pending_applications} application"
                    f"{'s' if pending_applications != 1 else ''} awaiting a decision."
                ),
                meta="In review",
                metaAccent="info",
            )
        )

    return DashboardResponse(
        stats_cards=[
            DashboardStatCard(
                id="active_contracts",
                title="Active contracts",
                value=contracts.active_count,
                subtitle=f"{contracts.ending_soon_count} ending soon",
            ),
            DashboardStatCard(
                id="pending_payments",
                title="Pending payments",
                value=_money(payments.pending_total_minor, payments.currency),
                subtitle=f"{payments.pending_count} awaiting payout",
            ),
            DashboardStatCard(
                id="job_success",
                title="Job success",
                value=f"{success_rate}%",
                subtitle=f"★ {rating:.1f} rating",
            ),
            DashboardStatCard(
                id="total_earnings",
                title="Total earnings",
                value=_money(payments.paid_total_minor, payments.currency),
                subtitle=(
                    f"+{_money(payments.paid_this_month_minor, payments.currency)} "
                    "this month"
                ),
            ),
        ],
        recent_activity=activities[:5],
        pending_actions=actions,
        payment_summary=_payment_summary(payments, client=False),
    )


def _payment_summary(payments, *, client: bool) -> DashboardPaymentSummary:
    return DashboardPaymentSummary(
        availableBalance=(
            f"{payments.currency} "
            f"{payments.paid_total_minor / 100:,.2f}"
        ),
        pendingPayments=(
            f"{payments.currency} "
            f"{payments.pending_total_minor / 100:,.2f}"
        ),
        nextPayoutDate="Not scheduled",
        status=(
            f"{payments.pending_count} payment"
            f"{'s' if payments.pending_count != 1 else ''} "
            f"awaiting {'approval' if client else 'payout'}"
        ),
    )
