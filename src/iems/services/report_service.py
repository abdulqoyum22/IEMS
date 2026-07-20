"""Reusable financial report calculations and export data preparation."""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import Decimal

from sqlalchemy import select

from iems.extensions import db
from iems.models.category import Category
from iems.models.expense import ExpenseTransaction
from iems.models.income import IncomeTransaction


def build_report(start_date: date, end_date: date) -> dict:
    """Return all data required by the dashboard, reports and exports."""
    income = db.session.scalars(
        select(IncomeTransaction)
        .where(
            IncomeTransaction.is_deleted.is_(False),
            IncomeTransaction.transaction_date.between(start_date, end_date),
        )
        .order_by(IncomeTransaction.transaction_date.desc(), IncomeTransaction.id.desc())
    ).all()
    expenses = db.session.scalars(
        select(ExpenseTransaction)
        .where(
            ExpenseTransaction.is_deleted.is_(False),
            ExpenseTransaction.transaction_date.between(start_date, end_date),
        )
        .order_by(ExpenseTransaction.transaction_date.desc(), ExpenseTransaction.id.desc())
    ).all()
    category_names = {category.id: category.name for category in db.session.scalars(select(Category)).all()}

    def as_item(transaction, party_label: str) -> dict:
        return {
            "id": transaction.id,
            "date": transaction.transaction_date.isoformat(),
            "category": category_names.get(transaction.category_id, "Uncategorised"),
            "party": getattr(transaction, party_label),
            "description": transaction.description,
            "reference": transaction.reference_no or "—",
            "amount": str(transaction.amount),
        }

    income_total = sum((item.amount for item in income), Decimal("0.00"))
    expense_total = sum((item.amount for item in expenses), Decimal("0.00"))
    expense_by_category: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
    for item in expenses:
        expense_by_category[category_names.get(item.category_id, "Uncategorised")] += item.amount

    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "income_total": str(income_total),
        "expense_total": str(expense_total),
        "balance": str(income_total - expense_total),
        "income": [as_item(item, "source") for item in income],
        "expenses": [as_item(item, "payee") for item in expenses],
        "expense_by_category": [
            {"category": name, "amount": str(amount)}
            for name, amount in sorted(expense_by_category.items(), key=lambda item: item[1], reverse=True)
        ],
    }
