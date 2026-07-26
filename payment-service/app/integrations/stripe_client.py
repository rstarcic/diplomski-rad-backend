import os

from stripe import StripeClient


STRIPE_SECRET_KEY = os.getenv("STRIPE_SK")

if not STRIPE_SECRET_KEY:
    raise RuntimeError("STRIPE_SK environment variable is not set")

stripe_client = StripeClient(STRIPE_SECRET_KEY)
