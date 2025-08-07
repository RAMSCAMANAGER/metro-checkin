from flask import Flask, render_template, request, jsonify
import json
from datetime import datetime

app = Flask(__name__)

DB_FILE = 'db.json'

def read_db():
    try:
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"queue": []}

def write_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f)

@app.route('/')
def checkin():
    return render_template('checkin.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/display')
def display():
    db = read_db()
    queue = db.get("queue", [])
    current = queue[0] if queue else {"name": "Nadie / No one", "number": "--"}
    people_ahead = max(len(queue) - 1, 0)
    return render_template('display.html', current_number=current["number"], people_ahead=people_ahead)

@app.route('/checkin', methods=['POST'])
def check_in():
    data = request.get_json()
    name = data.get("name")
    reason = data.get("reason")

    if not name or not reason:
        return jsonify({"error": "Nombre y motivo requeridos / Name and reason required"}), 400

    db = read_db()
    queue = db.get("queue", [])

    prefix = {"Pago de factura": "A", "Comprar telÃ©fono": "C", "Otro": "B"}.get(reason, "B")

    today = datetime.now().strftime('%Y-%m-%d')
    today_entries = [q for q in queue if q.get("date") == today and q.get("number", "").startswith(prefix)]
    ticket_number = f"{prefix}{len(today_entries)+1}"

    queue.append({"name": name, "reason": reason, "number": ticket_number, "date": today})
    db["queue"] = queue
    write_db(db)

    return jsonify({"success": True, "number": ticket_number})

@app.route('/next', methods=['POST'])
def next_customer():
    db = read_db()
    queue = db.get("queue", [])
    if queue:
        queue.pop(0)
    db["queue"] = queue
    write_db(db)
    return jsonify({"success": True})

@app.route('/reset', methods=['POST'])
def reset_queue():
    write_db({"queue": []})
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(debug=True)