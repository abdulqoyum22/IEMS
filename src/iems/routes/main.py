"""HTML pages and JSON endpoints for the local IEMS application."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from functools import wraps
from io import BytesIO
from pathlib import Path

from flask import Blueprint, jsonify, request, send_file, render_template
from flask_login import current_user, login_required, login_user, logout_user
from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import or_, select

from iems.extensions import db, login_manager
from iems.models import AuditLog, Category, CategoryType, ExpenseTransaction, IncomeTransaction, Role, User
from iems.models.base import utc_now
from iems.services.report_service import build_report


main_blueprint = Blueprint("main", __name__)


@login_manager.user_loader
def load_user(user_id: str):
    return db.session.get(User, int(user_id))


def api_error(message: str, status: int = 400):
    return jsonify(error=message), status


def admin_required(function):
    @wraps(function)
    @login_required
    def wrapped(*args, **kwargs):
        if current_user.role != Role.ADMIN:
            return api_error("Administrator access is required.", 403)
        return function(*args, **kwargs)
    return wrapped


def parse_date(value: str | None, field_name: str) -> date:
    try:
        return date.fromisoformat(value or "")
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a valid date.") from exc


def money(value) -> Decimal:
    try:
        result = Decimal(str(value)).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError) as exc:
        raise ValueError("Amount must be a valid number.") from exc
    if result <= 0:
        raise ValueError("Amount must be greater than zero.")
    return result


def audit(action: str, entity_type: str, description: str, entity_id: int | None = None) -> None:
    db.session.add(AuditLog(
        user_id=current_user.id if current_user.is_authenticated else None,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
    ))


def user_data(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role.value,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat(),
    }


def transaction_data(item, category_names: dict[int, str]) -> dict:
    party = item.source if isinstance(item, IncomeTransaction) else item.payee
    return {
        "id": item.id,
        "date": item.transaction_date.isoformat(),
        "category_id": item.category_id,
        "category": category_names.get(item.category_id, "Uncategorised"),
        "party": party,
        "description": item.description,
        "reference": item.reference_no or "",
        "amount": str(item.amount),
        "created_at": item.created_at.isoformat(),
    }


def transaction_class(kind: str):
    if kind == "income":
        return IncomeTransaction, "source", CategoryType.INCOME
    if kind == "expense":
        return ExpenseTransaction, "payee", CategoryType.EXPENSE
    raise ValueError("Transaction type must be income or expense.")


@main_blueprint.get("/")
def home():
    return render_template("index.html")


@main_blueprint.get("/health")
def health_check():
    return jsonify(status="ok", application="IEMS")


@main_blueprint.get("/api/bootstrap")
def bootstrap():
    return jsonify(needs_setup=db.session.scalar(select(User.id).limit(1)) is None)


@main_blueprint.post("/api/auth/setup")
def setup_admin():
    if db.session.scalar(select(User.id).limit(1)) is not None:
        return api_error("Initial setup has already been completed.", 409)
    payload = request.get_json() or {}
    username = str(payload.get("username", "")).strip().lower()
    full_name = str(payload.get("full_name", "")).strip()
    password = str(payload.get("password", ""))
    if len(username) < 3 or len(full_name) < 3 or len(password) < 8:
        return api_error("Use a name and username of at least 3 characters, and a password of at least 8 characters.")
    user = User(username=username, full_name=full_name, role=Role.ADMIN)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()
    audit("CREATE", "USER", f"Created initial administrator account for {username}.", user.id)
    db.session.commit()
    login_user(user)
    return jsonify(user=user_data(user)), 201


@main_blueprint.post("/api/auth/login")
def login():
    payload = request.get_json() or {}
    username = str(payload.get("username", "")).strip().lower()
    user = db.session.scalar(select(User).where(User.username == username))
    if not user or not user.is_active or not user.check_password(str(payload.get("password", ""))):
        return api_error("Invalid username or password.", 401)
    login_user(user)
    audit("LOGIN", "USER", f"{user.username} signed in.", user.id)
    db.session.commit()
    return jsonify(user=user_data(user))


@main_blueprint.post("/api/auth/forgot-password")
def forgot_password():
    """Log an offline recovery request without revealing whether an account exists."""
    username = str((request.get_json() or {}).get("username", "")).strip().lower()
    if not username:
        return api_error("Enter your username to request a reset.")
    user = db.session.scalar(select(User).where(User.username == username))
    if user:
        try:
            db.session.add(AuditLog(user_id=user.id, action="PASSWORD_RESET_REQUEST", entity_type="USER", entity_id=user.id, description=f"Password reset requested for {username}."))
            db.session.commit()
        except Exception:
            # Fail gracefully: don't reveal errors to the client. Keep a server-side record.
            import logging
            logging.exception("Failed to record password reset request for %s", username)
            try:
                db.session.rollback()
            except Exception:
                pass
    return jsonify(message="Password reset request received. Please contact your IEMS Administrator to complete the verification process.")


@main_blueprint.post("/api/users/<int:user_id>/reset-password")
@admin_required
def admin_reset_password(user_id: int):
    """Allow an administrator to reset a user's password.

    The administrator must provide a new temporary password in JSON payload as
    `{"password": "..."}`. Passwords must meet the existing length
    requirement (>= 8). The same hashing method is reused via `User.set_password()`.
    """
    payload = request.get_json() or {}
    new_password = str(payload.get("password", ""))
    if len(new_password) < 8:
        return api_error("Password must be at least 8 characters.")
    user = db.session.get(User, user_id)
    if not user:
        return api_error("User not found.", 404)
    # Use existing setter to ensure same hashing is applied
    user.set_password(new_password)
    audit("PASSWORD_RESET_BY_ADMIN", "USER", f"Administrator reset password for {user.username}.", user.id)
    db.session.commit()
    return jsonify(message="Password reset successfully.")


@main_blueprint.post("/api/auth/logout")
@login_required
def logout():
    audit("LOGOUT", "USER", f"{current_user.username} signed out.", current_user.id)
    db.session.commit()
    logout_user()
    return jsonify(message="Signed out.")


@main_blueprint.get("/api/auth/me")
def current_account():
    if not current_user.is_authenticated:
        return api_error("Not signed in.", 401)
    return jsonify(user=user_data(current_user))


@main_blueprint.get("/api/categories")
@login_required
def categories():
    kind = request.args.get("type", "")
    try:
        category_type = CategoryType(kind)
    except ValueError:
        return api_error("Category type must be income or expense.")
    records = db.session.scalars(select(Category).where(Category.category_type == category_type, Category.is_active.is_(True)).order_by(Category.name)).all()
    return jsonify(categories=[{"id": item.id, "name": item.name, "type": item.category_type.value} for item in records])


@main_blueprint.get("/api/dashboard")
@login_required
def dashboard():
    today = date.today()
    first_day = today.replace(day=1)
    month_report = build_report(first_day, today)
    all_time = build_report(date(2000, 1, 1), today)
    recent = sorted(month_report["income"] + month_report["expenses"], key=lambda item: item["date"], reverse=True)[:6]
    return jsonify(
        current_month=month_report,
        totals={key: all_time[key] for key in ("income_total", "expense_total", "balance")},
        recent=recent,
    )


@main_blueprint.route("/api/transactions/<kind>", methods=["GET", "POST"])
@login_required
def transactions(kind: str):
    try:
        model, party_field, category_type = transaction_class(kind)
    except ValueError as exc:
        return api_error(str(exc))
    if request.method == "GET":
        statement = select(model).where(model.is_deleted.is_(False))
        if request.args.get("start"):
            statement = statement.where(model.transaction_date >= parse_date(request.args.get("start"), "Start date"))
        if request.args.get("end"):
            statement = statement.where(model.transaction_date <= parse_date(request.args.get("end"), "End date"))
        if request.args.get("category_id"):
            statement = statement.where(model.category_id == int(request.args["category_id"]))
        search = request.args.get("search", "").strip()
        if search:
            statement = statement.where(or_(model.description.ilike(f"%{search}%"), getattr(model, party_field).ilike(f"%{search}%"), model.reference_no.ilike(f"%{search}%")))
        records = db.session.scalars(statement.order_by(model.transaction_date.desc(), model.id.desc())).all()
        names = {item.id: item.name for item in db.session.scalars(select(Category)).all()}
        return jsonify(transactions=[transaction_data(item, names) for item in records])

    payload = request.get_json() or {}
    try:
        category_id = int(payload.get("category_id"))
        category = db.session.get(Category, category_id)
        if not category or category.category_type != category_type or not category.is_active:
            raise ValueError("Select a valid category.")
        party = str(payload.get("party", "")).strip()
        description = str(payload.get("description", "")).strip()
        if not party or not description:
            raise ValueError("Source/payee and description are required.")
        record = model(
            transaction_date=parse_date(payload.get("date"), "Transaction date"),
            category_id=category_id,
            amount=money(payload.get("amount")),
            description=description,
            reference_no=str(payload.get("reference", "")).strip() or None,
            created_by_id=current_user.id,
            **{party_field: party},
        )
    except (TypeError, ValueError) as exc:
        return api_error(str(exc))
    db.session.add(record)
    db.session.flush()
    audit("CREATE", kind.upper(), f"Added {kind} transaction #{record.id}.", record.id)
    db.session.commit()
    return jsonify(transaction=transaction_data(record, {category.id: category.name})), 201


@main_blueprint.route("/api/transactions/<kind>/<int:record_id>", methods=["PUT", "DELETE"])
@login_required
def transaction_detail(kind: str, record_id: int):
    try:
        model, party_field, category_type = transaction_class(kind)
    except ValueError as exc:
        return api_error(str(exc))
    record = db.session.get(model, record_id)
    if not record or record.is_deleted:
        return api_error("Transaction not found.", 404)
    if request.method == "DELETE":
        record.is_deleted = True
        record.deleted_at = utc_now()
        record.deleted_by_id = current_user.id
        audit("DELETE", kind.upper(), f"Soft-deleted {kind} transaction #{record.id}.", record.id)
        db.session.commit()
        return jsonify(message="Transaction deleted.")
    payload = request.get_json() or {}
    try:
        category_id = int(payload.get("category_id"))
        category = db.session.get(Category, category_id)
        if not category or category.category_type != category_type or not category.is_active:
            raise ValueError("Select a valid category.")
        party = str(payload.get("party", "")).strip()
        description = str(payload.get("description", "")).strip()
        if not party or not description:
            raise ValueError("Source/payee and description are required.")
        record.transaction_date = parse_date(payload.get("date"), "Transaction date")
        record.category_id = category_id
        record.amount = money(payload.get("amount"))
        record.description = description
        record.reference_no = str(payload.get("reference", "")).strip() or None
        setattr(record, party_field, party)
        record.updated_by_id = current_user.id
    except (TypeError, ValueError) as exc:
        return api_error(str(exc))
    audit("UPDATE", kind.upper(), f"Updated {kind} transaction #{record.id}.", record.id)
    db.session.commit()
    return jsonify(transaction=transaction_data(record, {category.id: category.name}))


def requested_report():
    try:
        start_date = parse_date(request.args.get("start"), "Start date")
        end_date = parse_date(request.args.get("end"), "End date")
        if end_date < start_date:
            raise ValueError("End date cannot be before start date.")
        return build_report(start_date, end_date)
    except ValueError as exc:
        return api_error(str(exc))


@main_blueprint.get("/api/reports")
@login_required
def report():
    result = requested_report()
    return result if isinstance(result, tuple) else jsonify(report=result)


@main_blueprint.get("/api/reports/export/<format_name>")
@login_required
def export_report(format_name: str):
    result = requested_report()
    if isinstance(result, tuple):
        return result
    report_data = result
    audit("EXPORT", "REPORT", f"Exported {format_name.upper()} report for {report_data['start_date']} to {report_data['end_date']}.")
    db.session.commit()
    if format_name == "excel":
        workbook = Workbook()
        summary = workbook.active
        summary.title = "Summary"
        summary.append(["CESA Income and Expenditure Report"])
        summary.append(["Period", f"{report_data['start_date']} to {report_data['end_date']}"])
        summary.append(["Total income", report_data["income_total"]])
        summary.append(["Total expenses", report_data["expense_total"]])
        summary.append(["Net balance", report_data["balance"]])
        for title, rows in (("Income", report_data["income"]), ("Expenses", report_data["expenses"])):
            sheet = workbook.create_sheet(title)
            sheet.append(["Date", "Category", "Source / Payee", "Description", "Reference", "Amount"])
            for row in rows:
                sheet.append([row["date"], row["category"], row["party"], row["description"], row["reference"], float(row["amount"])])
            sheet.freeze_panes = "A2"
            for column in sheet.columns:
                sheet.column_dimensions[column[0].column_letter].width = min(max(len(str(cell.value or "")) for cell in column) + 2, 35)
        output = BytesIO()
        workbook.save(output)
        output.seek(0)
        return send_file(output, as_attachment=True, download_name="CESA-IEMS-report.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    if format_name == "pdf":
        output = BytesIO()
        document = SimpleDocTemplate(output, pagesize=A4, rightMargin=1.5 * cm, leftMargin=1.5 * cm)
        styles = getSampleStyleSheet()
        items = [Paragraph("CESA Income and Expenditure Report", styles["Title"]), Paragraph(f"Period: {report_data['start_date']} to {report_data['end_date']}", styles["Normal"]), Spacer(1, 0.4 * cm)]
        totals = [["Total Income", report_data["income_total"]], ["Total Expenses", report_data["expense_total"]], ["Net Balance", report_data["balance"]]]
        table = Table(totals, colWidths=[9 * cm, 7 * cm])
        table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#eaf7ef")), ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#b8c9be")), ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"), ("ALIGN", (1, 0), (1, -1), "RIGHT")]))
        items.extend([table, Spacer(1, 0.5 * cm)])
        for title, rows in (("Income", report_data["income"]), ("Expenses", report_data["expenses"])):
            items.append(Paragraph(title, styles["Heading2"]))
            data = [["Date", "Category", "Source / Payee", "Amount"]] + [[row["date"], row["category"], row["party"], row["amount"]] for row in rows]
            item_table = Table(data, repeatRows=1, colWidths=[3 * cm, 5.2 * cm, 6.1 * cm, 2.7 * cm])
            item_table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#087443")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d0d5dd")), ("FONTSIZE", (0, 0), (-1, -1), 8), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (-1, 1), (-1, -1), "RIGHT")]))
            items.extend([item_table, Spacer(1, 0.4 * cm)])
        document.build(items)
        output.seek(0)
        return send_file(output, as_attachment=True, download_name="CESA-IEMS-report.pdf", mimetype="application/pdf")
    return api_error("Export format must be pdf or excel.")


@main_blueprint.get("/api/users")
@admin_required
def users():
    return jsonify(users=[user_data(item) for item in db.session.scalars(select(User).order_by(User.full_name)).all()])


@main_blueprint.post("/api/users")
@admin_required
def create_user():
    payload = request.get_json() or {}
    username = str(payload.get("username", "")).strip().lower()
    full_name = str(payload.get("full_name", "")).strip()
    password = str(payload.get("password", ""))
    try:
        role = Role(payload.get("role", "treasurer"))
    except ValueError:
        return api_error("Role must be admin or treasurer.")
    if len(username) < 3 or len(full_name) < 3 or len(password) < 8:
        return api_error("Use a name and username of at least 3 characters, and a password of at least 8 characters.")
    if db.session.scalar(select(User).where(User.username == username)):
        return api_error("That username is already in use.")
    user = User(username=username, full_name=full_name, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()
    audit("CREATE", "USER", f"Created {role.value} account for {username}.", user.id)
    db.session.commit()
    return jsonify(user=user_data(user)), 201


@main_blueprint.patch("/api/users/<int:user_id>/status")
@admin_required
def update_user_status(user_id: int):
    user = db.session.get(User, user_id)
    if not user:
        return api_error("User not found.", 404)
    if user.id == current_user.id:
        return api_error("You cannot deactivate your own account.")
    user.is_active = bool((request.get_json() or {}).get("is_active"))
    audit("UPDATE", "USER", f"{'Activated' if user.is_active else 'Deactivated'} user {user.username}.", user.id)
    db.session.commit()
    return jsonify(user=user_data(user))


@main_blueprint.get("/api/audit-logs")
@admin_required
def audit_logs():
    rows = db.session.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(250)).all()
    return jsonify(logs=[{"id": row.id, "action": row.action, "entity_type": row.entity_type, "description": row.description, "created_at": row.created_at.isoformat(), "user_id": row.user_id} for row in rows])
