from datetime import datetime
from typing import assert_never

from dateutil.relativedelta import relativedelta

from subscriptions.shared.term import Term


def calculate_next_renewal(now: datetime, term: Term) -> datetime:
    if term == Term.MONTHLY:
        delta = relativedelta(months=1)
    elif term == Term.YEARLY:
        delta = relativedelta(years=1)
    else:
        assert_never(term)

    return now + delta
