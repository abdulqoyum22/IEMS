"""Database models and starter data."""

from iems.extensions import db
from iems.models.audit_log import AuditLog
from iems.models.access_request import PasswordResetRequest, RequestStatus, SignupRequest
from iems.models.category import Category, CategoryType
from iems.models.expense import ExpenseTransaction
from iems.models.income import IncomeTransaction
from iems.models.user import Role, User


DEFAULT_CATEGORIES = {
    CategoryType.INCOME: (
        "Membership Dues",
        "Departmental Levies",
        "Event Registration Fees",
        "Sponsorships",
        "Donations",
        "Other Income",
    ),
    CategoryType.EXPENSE: (
        "Event Organization",
        "Printing",
        "Publicity",
        "Transportation",
        "Refreshments",
        "Equipment Purchase",
        "Administrative Expense",
        "Other Expense",
    ),
}


def seed_default_categories() -> None:
    """Create CESA's initial categories once, without overwriting user changes."""
    changed = False
    for category_type, names in DEFAULT_CATEGORIES.items():
        for name in names:
            exists = db.session.scalar(
                db.select(Category).where(
                    Category.name == name,
                    Category.category_type == category_type,
                )
            )
            if not exists:
                db.session.add(Category(name=name, category_type=category_type))
                changed = True
    if changed:
        db.session.commit()


__all__ = [
    "AuditLog",
    "PasswordResetRequest",
    "RequestStatus",
    "SignupRequest",
    "Category",
    "CategoryType",
    "ExpenseTransaction",
    "IncomeTransaction",
    "Role",
    "User",
]
