from flask import Flask, render_template, request, redirect, url_for, session
from tinydb import TinyDB, Query
import datetime

app = Flask(__name__)
app.secret_key = 'metro_secret_key'
db = TinyDB('db.json')
queue = db.table('queue')
settings = db.table('settings')

PIN_CODE = "2010"

def generate_number(reason):
    today = datetime.date.today().isoformat()
    prefix = {'Pago': 'B', 'Compra': 'A', 'Servicio': 'C'}.get(reason, 'C')
    numbers_today = [x['number'] for x in queue if x['date'] == today and x['prefix'] == prefix]
    next_number = len(numbers_today) + 1
    return f"{prefix}{next_number}", prefix

@app.route('/checkin', methods=['GET', 'POST'])
def checkin():
    if request.method == 'POST':
        name = request.form['name']
        reason = request.form['reason']
        number, prefix = generate_number(reason)
        queue.insert({
            'name': name,
            'reason': reason,
            'number': number,
            'prefix': prefix,
            'date': datetime.date.today().isoformat(),
            'timestamp': datetime.datetime.now().isoformat()
        })
        session['just_checked_in'] = number
        return redirect(url_for('display'))
    return render_template('checkin.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        if session.get('authenticated'):
            if 'reset' in request.form:
                queue.truncate()
                settings.truncate()
                return redirect(url_for('admin'))
            if 'next' in request.form:
                today = datetime.date.today().isoformat()
                today_queue = sorted([x for x in queue if x['date'] == today], key=lambda x: x['timestamp'])
                if today_queue:
                    settings.upsert({
                        'current': today_queue[0]['name'],
                        'current_number': today_queue[0]['number']
                    }, Query().fragment({'current': ''}))
                    queue.remove(Query().name == today_queue[0]['name'])
                return redirect(url_for('admin'))
        elif request.form.get('pin') == PIN_CODE:
            session['authenticated'] = True
            return redirect(url_for('admin'))
    current = settings.get(Query().fragment({'current': ''}))
    today = datetime.date.today().isoformat()
    today_queue = sorted([x for x in queue if x['date'] == today], key=lambda x: x['timestamp'])
    return render_template('admin.html', authenticated=session.get('authenticated', False),
                           queue=today_queue,
                           current=current.get('current') if current else None,
                           current_number=current.get('current_number') if current else None)

@app.route('/display')
def display():
    current = settings.get(Query().fragment({'current': ''}))
    today = datetime.date.today().isoformat()
    today_queue = [x for x in queue if x['date'] == today]
    your_number = session.pop('just_checked_in', None)
    return render_template('display.html',
                           current=current.get('current') if current else '',
                           current_number=current.get('current_number') if current else 'Esperando...',
                           people_ahead=len(today_queue),
                           your_number=your_number)

if __name__ == '__main__':
    app.run(debug=True)