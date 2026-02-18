# validators.py

from datetime import datetime, timedelta


def is_valid_effective_date(effective_date):
    today = datetime.today().date()
    three_months_ago = today - timedelta(days=90)

    effective_date = datetime.strptime(effective_date, "%m/%d/%Y").date()

    if effective_date > today or effective_date < three_months_ago:
        return False

    return True
