from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

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

@app.route("/transaction/<int:id>")
def transaction_details(id):

    transaction = Transaction.query.get_or_404(id)

    return render_template(
        "transaction_details.html",
        transaction=transaction
    )


if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    app.run(debug=True)