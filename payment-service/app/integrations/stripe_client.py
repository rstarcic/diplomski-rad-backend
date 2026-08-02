import os

from stripe import StripeClient


STRIPE_SECRET_KEY = os.getenv("STRIPE_API_KEY")

if not STRIPE_SECRET_KEY:
    raise RuntimeError("STRIPE_API_KEY environment variable is not set")

stripe_client = StripeClient(STRIPE_SECRET_KEY)
