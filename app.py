from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask import send_file
from reportlab.pdfgen import canvas
import io

app = Flask(__name__)

# -------------------------
# Database Configuration
# -------------------------
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# -------------------------
# Database Table
# -------------------------
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    account_number = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    transaction_type = db.Column(db.String(30), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    fraud_score = db.Column(db.Integer, nullable=False)
    risk = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(30), default="Pending")
    notes = db.Column(db.Text)


# -------------------------
# Risk Calculation
# -------------------------
def calculate_risk(amount, transaction_type, location):

    score = 0

    # Amount
    if amount >= 100000:
        score += 50
    elif amount >= 50000:
        score += 30

    # Transaction Type
    if transaction_type == "RTGS":
        score += 20
    elif transaction_type == "IMPS":
        score += 10

    # Location
    if location.lower() != "bangalore":
        score += 20

    # Decide Risk
    if score >= 60:
        risk = "High"
    elif score >= 30:
        risk = "Medium"
    else:
        risk = "Safe"

    return score, risk
# -------------------------
# Routes
# -------------------------

@app.route("/")
def login():
    return render_template("login.html")


@app.route("/dashboard")
def dashboard():

    search = request.args.get("search")

    if search:

        transactions = Transaction.query.filter(
            (Transaction.customer_name.contains(search)) |
            (Transaction.account_number.contains(search))
        ).all()

    else:

        transactions = Transaction.query.all()

    total = len(transactions)

    high = len([t for t in transactions if t.risk == "High"])
    medium = len([t for t in transactions if t.risk == "Medium"])
    safe = len([t for t in transactions if t.risk == "Safe"])

    return render_template(
        "dashboard.html",
        transactions=transactions,
        total=total,
        high=high,
        medium=medium,
        safe=safe,
        search=search
    )

@app.route("/add", methods=["GET", "POST"])
def add_transaction():

    if request.method == "POST":

        customer_name = request.form["customer_name"]

        account_number = request.form["account_number"]

        amount = float(request.form["amount"])

        transaction_type = request.form["transaction_type"]

        location = request.form["location"]

        fraud_score, risk = calculate_risk(amount, transaction_type, location)

        new_transaction = Transaction(
            customer_name=customer_name,
            account_number=account_number,
            amount=amount,
            transaction_type=transaction_type,
            location=location,
            fraud_score=fraud_score,
            risk=risk
        )

        db.session.add(new_transaction)
        db.session.commit()

        return redirect(url_for("dashboard"))

    return render_template("add_transaction.html")

@app.route("/transaction/<int:id>", methods=["GET", "POST"])
def transaction_details(id):

    transaction = Transaction.query.get_or_404(id)

    if request.method == "POST":

        transaction.status = request.form["status"]
        transaction.notes = request.form["notes"]

        db.session.commit()

    return render_template(
        "transaction_details.html",
        transaction=transaction
    )
@app.route("/download/<int:id>")
def download_report(id):

    transaction = Transaction.query.get_or_404(id)

    buffer = io.BytesIO()

    pdf = canvas.Canvas(buffer)

    pdf.setTitle("Fraud Investigation Report")

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(170, 800, "Fraud Investigation Report")

    pdf.setFont("Helvetica", 12)

    y = 760

    pdf.drawString(50, y, f"Customer Name: {transaction.customer_name}")
    y -= 25

    pdf.drawString(50, y, f"Account Number: {transaction.account_number}")
    y -= 25

    pdf.drawString(50, y, f"Amount: ₹ {transaction.amount}")
    y -= 25

    pdf.drawString(50, y, f"Transaction Type: {transaction.transaction_type}")
    y -= 25

    pdf.drawString(50, y, f"Location: {transaction.location}")
    y -= 25

    pdf.drawString(50, y, f"Fraud Score: {transaction.fraud_score}/100")
    y -= 25

    pdf.drawString(50, y, f"Risk Level: {transaction.risk}")
    y -= 25

    pdf.drawString(50, y, f"Investigation Status: {transaction.status}")
    y -= 35

    pdf.drawString(50, y, "Investigator Notes:")
    y -= 20

    notes = transaction.notes if transaction.notes else "No notes available."

    pdf.drawString(70, y, notes)

    y -= 60

    pdf.setFont("Helvetica-Oblique", 10)

    pdf.drawString(50, y, "Generated by Fraud Investigation Tracking System")

    pdf.save()

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"Fraud_Report_{transaction.id}.pdf",
        mimetype="application/pdf"
    )

if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    app.run(debug=True)