from dataclasses import dataclass

from app.jobs.models import Job
from app.negotiations.models import NegotiationEdit


@dataclass(frozen=True)
class ContractTerms:
    budget_amount: float
    budget_type: str
    duration: int
    hours_per_week: int
    deliverables: str


def extract_job_terms(job: Job) -> ContractTerms:
    return ContractTerms(
        budget_amount=job.budget_amount,
        budget_type=job.budget_type,
        duration=job.duration,
        hours_per_week=job.hours_per_week,
        deliverables=job.deliverables,
    )


def extract_negotiation_terms(
    edit: NegotiationEdit,
) -> ContractTerms:
    return ContractTerms(
        budget_amount=edit.budget_amount,
        budget_type=edit.budget_type,
        duration=edit.duration,
        hours_per_week=edit.hours_per_week,
        deliverables=edit.deliverables,
    )
