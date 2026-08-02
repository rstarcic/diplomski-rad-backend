import asyncio
from datetime import UTC, datetime, timedelta

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
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session


def _money(amount_minor: int, currency: str = "EUR") -> str:
    symbol = "€" if currency.upper() == "EUR" else f"{currency.upper()} "
    return f"{symbol}{amount_minor / 100:,.2f}"


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _relative_time(value: datetime) -> str:
    value = _aware_utc(value)
    seconds = max(0, int((datetime.now(UTC) - value).total_seconds()))
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
    now = datetime.now(UTC)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    week_start = (now - timedelta(days=now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
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
        db.scalar(
            select(func.count(Job.id)).where(
                Job.client_id == user.user_id,
                active_job_filter,
            )
        )
        or 0
    )

    new_jobs = (
        db.scalar(
            select(func.count(Job.id)).where(
                Job.client_id == user.user_id,
                active_job_filter,
                Job.created_at >= month_start,
            )
        )
        or 0
    )

    applications = (
        db.scalar(
            select(func.count(Application.id))
            .join(Job, Job.id == Application.job_id)
            .where(
                Job.client_id == user.user_id,
                Application.status != "withdrawn",
            )
        )
        or 0
    )

    weekly_applications = (
        db.scalar(
            select(func.count(Application.id))
            .join(Job, Job.id == Application.job_id)
            .where(
                Job.client_id == user.user_id,
                Application.status != "withdrawn",
                Application.created_at >= week_start,
            )
        )
        or 0
    )

    recent_applications = db.execute(
        select(Application, Job, Profile)
        .join(Job, Job.id == Application.job_id)
        .join(
            Profile,
            Profile.user_id == Application.contractor_id,
        )
        .where(Job.client_id == user.user_id)
        .order_by(Application.created_at.desc())
        .limit(5)
    ).all()

    activity_entries = [
        (
            DashboardListItem(
                id=f"application-{application.id}",
                type="application_received",
                job_id=job.id,
                application_id=application.id,
                title="New application received",
                subtitle=(
                    f"{contractor.full_name or 'A contractor'} applied to "
                    f"{job.title}."
                ),
                meta=_relative_time(application.created_at),
            ),
            application.created_at,
        )
        for application, job, contractor in recent_applications
    ]
    activity_entries.extend(
        (
            DashboardListItem(
                id=f"payment-{item.id}",
                type="payment_updated",
                job_id=item.job_id,
                application_id=item.application_id,
                contract_id=item.contract_id,
                payment_id=item.id,
                title="Payment updated",
                subtitle=f"{item.job_title} payment is {item.status}.",
                meta=_relative_time(item.updated_at),
            ),
            item.updated_at,
        )
        for item in payments.recent
    )
    activities = [
        item
        for item, _timestamp in sorted(
            activity_entries,
            key=lambda entry: _aware_utc(entry[1]),
            reverse=True,
        )[:5]
    ]

    pending_rows = db.execute(
        select(
            Job,
            func.count(Application.id),
            func.max(Application.created_at),
        )
        .join(Application, Application.job_id == Job.id)
        .where(
            Job.client_id == user.user_id,
            Job.status == "open",
            Application.status == "pending",
        )
        .group_by(Job.id)
    ).all()

    action_entries = [
        (
            DashboardListItem(
                id=f"contract-signature-{contract.id}",
                type="contract_signature_required",
                job_id=contract.job_id,
                application_id=contract.application_id,
                contract_id=contract.id,
                title="Contract signature required",
                subtitle=(
                    f"The contract for {contract.job_title} needs your "
                    "signature."
                ),
                meta="Due soon",
                metaAccent="warning",
            ),
            contract.updated_at,
        )
        for contract in contracts.pending_signatures
    ]
    action_entries.extend(
        (
            DashboardListItem(
                id=f"review-applications-{job.id}",
                type="review_applications",
                job_id=job.id,
                title="Review new applications",
                subtitle=(
                    f"{count} candidate"
                    f"{'s' if count != 1 else ''} waiting for "
                    f"feedback for {job.title}."
                ),
                meta="High priority",
                metaAccent="warning",
            ),
            latest_application_at,
        )
        for job, count, latest_application_at in pending_rows
    )
    actions = [
        item
        for item, _timestamp in sorted(
            action_entries,
            key=lambda entry: _aware_utc(entry[1]),
            reverse=True,
        )[:3]
    ]

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
        pending_actions=actions,
        payment_summary=_payment_summary(payments, client=True),
    )


def _contractor_dashboard(db, user, contracts, payments) -> DashboardResponse:
    terminal_jobs = db.execute(
        select(Job.status, func.count(Job.id))
        .join(Application, Application.job_id == Job.id)
        .where(
            Application.contractor_id == user.user_id,
            Application.status == "accepted",
            Job.status.in_(("completed_by_client", "incomplete")),
        )
        .group_by(Job.status)
    ).all()

    totals = dict(terminal_jobs)
    completed = totals.get("completed_by_client", 0)
    terminal_total = completed + totals.get("incomplete", 0)
    success_rate = round(completed / terminal_total * 100) if terminal_total else 0

    rating = db.scalar(
        select(
            func.avg(
                (
                    Review.communication_rating
                    + Review.clarity_rating
                    + Review.reliability_rating
                    + Review.collaboration_rating
                )
                / 4
            )
        ).where(
            Review.target_type == "contractor",
            Review.target_id == user.user_id,
        )
    )

    rating = float(rating or 0)

    recent_applications = db.execute(
        select(Application, Job)
        .join(Job, Job.id == Application.job_id)
        .where(Application.contractor_id == user.user_id)
        .order_by(Application.updated_at.desc())
        .limit(5)
    ).all()

    activity_entries = [
        (
            DashboardListItem(
                id=f"application-{application.id}",
                type=(
                    "application_approved"
                    if application.status == "accepted"
                    else "application_updated"
                ),
                job_id=job.id,
                application_id=application.id,
                title=(
                    "Application approved"
                    if application.status == "accepted"
                    else "Application updated"
                ),
                subtitle=(f"Your application for {job.title} is {application.status}."),
                meta=_relative_time(application.updated_at),
            ),
            application.updated_at,
        )
        for application, job in recent_applications
    ]
    activity_entries.extend(
        (
            DashboardListItem(
                id=f"payment-{item.id}",
                type=(
                    "payment_released" if item.status == "paid" else "payment_updated"
                ),
                job_id=item.job_id,
                application_id=item.application_id,
                contract_id=item.contract_id,
                payment_id=item.id,
                title=(
                    "Payment released" if item.status == "paid" else "Payment updated"
                ),
                subtitle=(
                    f"{_money(item.amount_minor, item.currency)} for "
                    f"{item.job_title} is {item.status}."
                ),
                meta=_relative_time(item.updated_at),
            ),
            item.updated_at,
        )
        for item in payments.recent
    )
    activities = [
        item
        for item, _timestamp in sorted(
            activity_entries,
            key=lambda entry: _aware_utc(entry[1]),
            reverse=True,
        )[:5]
    ]

    action_entries = [
        (
            DashboardListItem(
                id=f"contract-signature-{contract.id}",
                type="contract_signature_required",
                job_id=contract.job_id,
                application_id=contract.application_id,
                contract_id=contract.id,
                title="Contract signature required",
                subtitle=(
                    f"The contract for {contract.job_title} needs your "
                    "signature."
                ),
                meta="Due soon",
                metaAccent="warning",
            ),
            contract.updated_at,
        )
        for contract in contracts.pending_signatures
    ]

    pending_applications = db.execute(
        select(
            func.count(Application.id),
            func.max(Application.updated_at),
        ).where(
            Application.contractor_id == user.user_id,
            Application.status.in_(("pending", "selected")),
        )
    ).one()
    pending_application_count, latest_application_at = pending_applications

    if pending_application_count and latest_application_at is not None:
        action_entries.append(
            (
                DashboardListItem(
                    id="pending-applications",
                    type="applications_in_progress",
                    title="Applications in progress",
                    subtitle=(
                        f"You have {pending_application_count} application"
                        f"{'s' if pending_application_count != 1 else ''} "
                        "awaiting a decision."
                    ),
                    meta="In review",
                    metaAccent="info",
                ),
                latest_application_at,
            )
        )

    actions = [
        item
        for item, _timestamp in sorted(
            action_entries,
            key=lambda entry: _aware_utc(entry[1]),
            reverse=True,
        )
    ]

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
        recent_activity=activities,
        pending_actions=actions,
        payment_summary=_payment_summary(payments, client=False),
    )


def _payment_summary(payments, *, client: bool) -> DashboardPaymentSummary:
    return DashboardPaymentSummary(
        availableBalance=(
            f"{payments.currency} " f"{payments.paid_total_minor / 100:,.2f}"
        ),
        pendingPayments=(
            f"{payments.currency} " f"{payments.pending_total_minor / 100:,.2f}"
        ),
        nextPayoutDate="Not scheduled",
        status=(
            f"{payments.pending_count} payment"
            f"{'s' if payments.pending_count != 1 else ''} "
            f"awaiting {'approval' if client else 'payout'}"
        ),
    )
