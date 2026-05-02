import os

os.makedirs('templates', exist_ok=True)
os.makedirs('static', exist_ok=True)

# ==================== app.py ====================
app_py = '''from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import openpyxl
from io import BytesIO

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your-secret-key-change-this'

# Low stock threshold
LOW_STOCK_THRESHOLD = 50

db = SQLAlchemy(app)


class Store(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200))
    required_30d = db.Column(db.Integer, default=0)
    required_40d = db.Column(db.Integer, default=0)
    required_60d = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    shipments = db.relationship('Shipment', backref='store', lazy=True, cascade='all, delete-orphan')


class VendorStock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    divider_type = db.Column(db.String(10), unique=True, nullable=False)
    quantity = db.Column(db.Integer, default=0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)


class Shipment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey('store.id'), nullable=False)
    date = db.Column(db.Date, default=datetime.utcnow)
    qty_30d = db.Column(db.Integer, default=0)
    qty_40d = db.Column(db.Integer, default=0)
    qty_60d = db.Column(db.Integer, default=0)
    notes = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class StockHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    divider_type = db.Column(db.String(10))
    old_qty = db.Column(db.Integer)
    new_qty = db.Column(db.Integer)
    change = db.Column(db.Integer)
    note = db.Column(db.String(200))


class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True)
    value = db.Column(db.String(200))


def get_threshold():
    s = Settings.query.filter_by(key='low_stock_threshold').first()
    return int(s.value) if s else LOW_STOCK_THRESHOLD


def calculate_alerts():
    """Calculate stock alerts and shortage warnings"""
    alerts = []
    threshold = get_threshold()
    
    stocks = {s.divider_type: s.quantity for s in VendorStock.query.all()}
    stores = Store.query.all()
    shipments = Shipment.query.all()
    
    for dtype in ['30D', '40D', '60D']:
        stock = stocks.get(dtype, 0)
        required = sum(getattr(s, f'required_{dtype.lower()}') for s in stores)
        shipped = sum(getattr(s, f'qty_{dtype.lower()}') for s in shipments)
        remaining_need = max(0, required - shipped)
        
        if stock < remaining_need:
            shortage = remaining_need - stock
            alerts.append({
                'type': dtype,
                'level': 'danger',
                'message': f'Critical! {dtype} shortage: Need to order {shortage} more units from vendor',
                'icon': 'exclamation-triangle-fill'
            })
        elif stock < threshold:
            alerts.append({
                'type': dtype,
                'level': 'warning',
                'message': f'Low stock alert: {dtype} has only {stock} units left. Consider contacting vendor',
                'icon': 'exclamation-circle-fill'
            })
    
    return alerts


@app.route('/')
def dashboard():
    stocks = {s.divider_type: s.quantity for s in VendorStock.query.all()}
    stock_30d = stocks.get('30D', 0)
    stock_40d = stocks.get('40D', 0)
    stock_60d = stocks.get('60D', 0)

    stores = Store.query.all()
    required_30d = sum(s.required_30d for s in stores)
    required_40d = sum(s.required_40d for s in stores)
    required_60d = sum(s.required_60d for s in stores)

    shipments = Shipment.query.all()
    shipped_30d = sum(s.qty_30d for s in shipments)
    shipped_40d = sum(s.qty_40d for s in shipments)
    shipped_60d = sum(s.qty_60d for s in shipments)

    gap_30d = required_30d - shipped_30d
    gap_40d = required_40d - shipped_40d
    gap_60d = required_60d - shipped_60d

    alerts = calculate_alerts()
    threshold = get_threshold()

    return render_template('dashboard.html',
                           stock_30d=stock_30d, stock_40d=stock_40d, stock_60d=stock_60d,
                           required_30d=required_30d, required_40d=required_40d, required_60d=required_60d,
                           shipped_30d=shipped_30d, shipped_40d=shipped_40d, shipped_60d=shipped_60d,
                           gap_30d=gap_30d, gap_40d=gap_40d, gap_60d=gap_60d,
                           stores_count=len(stores), shipments_count=len(shipments),
                           alerts=alerts, threshold=threshold)


@app.route('/stores')
def stores():
    all_stores = Store.query.order_by(Store.name).all()
    return render_template('stores.html', stores=all_stores)


@app.route('/stores/add', methods=['POST'])
def add_store():
    name = request.form.get('name')
    location = request.form.get('location')
    r30 = int(request.form.get('required_30d') or 0)
    r40 = int(request.form.get('required_40d') or 0)
    r60 = int(request.form.get('required_60d') or 0)
    store = Store(name=name, location=location, required_30d=r30, required_40d=r40, required_60d=r60)
    db.session.add(store)
    db.session.commit()
    flash('Store added successfully!', 'success')
    return redirect(url_for('stores'))


@app.route('/stores/edit/<int:id>', methods=['POST'])
def edit_store(id):
    store = Store.query.get_or_404(id)
    store.name = request.form.get('name')
    store.location = request.form.get('location')
    store.required_30d = int(request.form.get('required_30d') or 0)
    store.required_40d = int(request.form.get('required_40d') or 0)
    store.required_60d = int(request.form.get('required_60d') or 0)
    db.session.commit()
    flash('Store updated!', 'success')
    return redirect(url_for('stores'))


@app.route('/stores/delete/<int:id>')
def delete_store(id):
    store = Store.query.get_or_404(id)
    db.session.delete(store)
    db.session.commit()
    flash('Store deleted!', 'warning')
    return redirect(url_for('stores'))


@app.route('/vendor-stock')
def vendor_stock():
    stocks = VendorStock.query.all()
    history = StockHistory.query.order_by(StockHistory.date.desc()).limit(20).all()
    threshold = get_threshold()
    return render_template('vendor_stock.html', stocks=stocks, history=history, threshold=threshold)


@app.route('/vendor-stock/update', methods=['POST'])
def update_stock():
    divider_type = request.form.get('divider_type')
    new_qty = int(request.form.get('quantity') or 0)
    note = request.form.get('note', '')
    stock = VendorStock.query.filter_by(divider_type=divider_type).first()
    old_qty = stock.quantity if stock else 0
    if stock:
        stock.quantity = new_qty
        stock.last_updated = datetime.utcnow()
    else:
        stock = VendorStock(divider_type=divider_type, quantity=new_qty)
        db.session.add(stock)
    history = StockHistory(divider_type=divider_type, old_qty=old_qty, new_qty=new_qty, change=new_qty - old_qty, note=note)
    db.session.add(history)
    db.session.commit()
    flash(f'{divider_type} stock updated!', 'success')
    return redirect(url_for('vendor_stock'))


@app.route('/settings/threshold', methods=['POST'])
def update_threshold():
    new_val = int(request.form.get('threshold') or 50)
    s = Settings.query.filter_by(key='low_stock_threshold').first()
    if s:
        s.value = str(new_val)
    else:
        s = Settings(key='low_stock_threshold', value=str(new_val))
        db.session.add(s)
    db.session.commit()
    flash(f'Low stock threshold updated to {new_val}', 'success')
    return redirect(url_for('vendor_stock'))


@app.route('/shipments')
def shipments():
    all_shipments = Shipment.query.order_by(Shipment.date.desc()).all()
    all_stores = Store.query.order_by(Store.name).all()
    return render_template('shipments.html', shipments=all_shipments, stores=all_stores)


@app.route('/shipments/add', methods=['POST'])
def add_shipment():
    store_id = int(request.form.get('store_id'))
    date_str = request.form.get('date')
    date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else datetime.utcnow().date()
    qty_30d = int(request.form.get('qty_30d') or 0)
    qty_40d = int(request.form.get('qty_40d') or 0)
    qty_60d = int(request.form.get('qty_60d') or 0)
    notes = request.form.get('notes', '')
    shipment = Shipment(store_id=store_id, date=date, qty_30d=qty_30d, qty_40d=qty_40d, qty_60d=qty_60d, notes=notes)
    db.session.add(shipment)
    for dtype, qty in [('30D', qty_30d), ('40D', qty_40d), ('60D', qty_60d)]:
        if qty > 0:
            stock = VendorStock.query.filter_by(divider_type=dtype).first()
            if stock:
                old_qty = stock.quantity
                stock.quantity = max(0, stock.quantity - qty)
                stock.last_updated = datetime.utcnow()
                history = StockHistory(divider_type=dtype, old_qty=old_qty, new_qty=stock.quantity, change=-qty, note=f'Shipped to store #{store_id}')
                db.session.add(history)
    db.session.commit()
    flash('Shipment recorded!', 'success')
    return redirect(url_for('shipments'))


@app.route('/shipments/delete/<int:id>')
def delete_shipment(id):
    shipment = Shipment.query.get_or_404(id)
    db.session.delete(shipment)
    db.session.commit()
    flash('Shipment deleted!', 'warning')
    return redirect(url_for('shipments'))


@app.route('/reports')
def reports():
    stores = Store.query.all()
    report_data = []
    for store in stores:
        shipped_30 = sum(s.qty_30d for s in store.shipments)
        shipped_40 = sum(s.qty_40d for s in store.shipments)
        shipped_60 = sum(s.qty_60d for s in store.shipments)
        report_data.append({
            'store': store,
            'shipped_30': shipped_30, 'shipped_40': shipped_40, 'shipped_60': shipped_60,
            'gap_30': store.required_30d - shipped_30,
            'gap_40': store.required_40d - shipped_40,
            'gap_60': store.required_60d - shipped_60,
        })
    return render_template('reports.html', report_data=report_data)


@app.route('/reports/export')
def export_excel():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Stores Report"
    ws.append(['Store', 'Location', 'Required 30D', 'Shipped 30D', 'Gap 30D', 'Required 40D', 'Shipped 40D', 'Gap 40D', 'Required 60D', 'Shipped 60D', 'Gap 60D'])
    for store in Store.query.all():
        s30 = sum(s.qty_30d for s in store.shipments)
        s40 = sum(s.qty_40d for s in store.shipments)
        s60 = sum(s.qty_60d for s in store.shipments)
        ws.append([store.name, store.location or '', store.required_30d, s30, store.required_30d - s30, store.required_40d, s40, store.required_40d - s40, store.required_60d, s60, store.required_60d - s60])
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return send_file(output, as_attachment=True, download_name=f'dividers_report_{datetime.now().strftime("%Y%m%d")}.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


def init_db():
    with app.app_context():
        db.create_all()
        for dtype in ['30D', '40D', '60D']:
            if not VendorStock.query.filter_by(divider_type=dtype).first():
                db.session.add(VendorStock(divider_type=dtype, quantity=0))
        db.session.commit()


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
'''

# ==================== base.html ====================
base_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dividers Tracker</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet">
    <link href="{{ url_for('static', filename='style.css') }}" rel="stylesheet">
</head>
<body>
<nav class="navbar navbar-expand-lg navbar-dark">
    <div class="container">
        <a class="navbar-brand" href="{{ url_for('dashboard') }}">
            <i class="bi bi-box-seam"></i> Dividers Tracker
        </a>
        <div class="collapse navbar-collapse">
            <ul class="navbar-nav me-auto">
                <li class="nav-item"><a class="nav-link" href="{{ url_for('dashboard') }}"><i class="bi bi-speedometer2"></i> Dashboard</a></li>
                <li class="nav-item"><a class="nav-link" href="{{ url_for('stores') }}"><i class="bi bi-shop"></i> Stores</a></li>
                <li class="nav-item"><a class="nav-link" href="{{ url_for('vendor_stock') }}"><i class="bi bi-boxes"></i> Vendor Stock</a></li>
                <li class="nav-item"><a class="nav-link" href="{{ url_for('shipments') }}"><i class="bi bi-truck"></i> Shipments</a></li>
                <li class="nav-item"><a class="nav-link" href="{{ url_for('reports') }}"><i class="bi bi-graph-up"></i> Reports</a></li>
            </ul>
            <button id="darkModeToggle" class="btn btn-sm btn-outline-light">
                <i class="bi bi-moon-stars-fill"></i> <span id="modeText">Dark</span>
            </button>
        </div>
    </div>
</nav>
<div class="container mt-4">
    {% with messages = get_flashed_messages(with_categories=true) %}
        {% for category, message in messages %}
            <div class="alert alert-{{ category }} alert-dismissible fade show">
                {{ message }}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        {% endfor %}
    {% endwith %}
    {% block content %}{% endblock %}
</div>
<footer class="text-center py-4 mt-5 footer-custom">
    <small>Dividers Tracker © 2025 | Built with <i class="bi bi-heart-fill text-danger"></i></small>
</footer>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
// Dark Mode Toggle
const toggleBtn = document.getElementById('darkModeToggle');
const modeText = document.getElementById('modeText');
const body = document.body;

function setMode(isDark) {
    if (isDark) {
        body.classList.add('dark-mode');
        modeText.textContent = 'Light';
        toggleBtn.querySelector('i').className = 'bi bi-sun-fill';
    } else {
        body.classList.remove('dark-mode');
        modeText.textContent = 'Dark';
        toggleBtn.querySelector('i').className = 'bi bi-moon-stars-fill';
    }
}

// Load saved preference
const savedMode = localStorage.getItem('darkMode') === 'true';
setMode(savedMode);

toggleBtn.addEventListener('click', () => {
    const isDark = !body.classList.contains('dark-mode');
    setMode(isDark);
    localStorage.setItem('darkMode', isDark);
});
</script>
{% block scripts %}{% endblock %}
</body>
</html>'''

# ==================== dashboard.html ====================
dashboard_html = '''{% extends 'base.html' %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h2><i class="bi bi-speedometer2"></i> Dashboard</h2>
    <span class="badge bg-secondary p-2">Threshold: {{ threshold }} units</span>
</div>

{% if alerts %}
<div class="mb-4">
    {% for alert in alerts %}
    <div class="alert alert-{{ alert.level }} d-flex align-items-center alert-custom">
        <i class="bi bi-{{ alert.icon }} fs-4 me-3"></i>
        <div><strong>{{ alert.type }}:</strong> {{ alert.message }}</div>
    </div>
    {% endfor %}
</div>
{% endif %}

<div class="row g-3 mb-4">
    <div class="col-md-6"><div class="card stat-card stat-stores p-3"><div class="stat-icon"><i class="bi bi-shop"></i></div><h6>Total Stores</h6><h2>{{ stores_count }}</h2></div></div>
    <div class="col-md-6"><div class="card stat-card stat-shipments p-3"><div class="stat-icon"><i class="bi bi-truck"></i></div><h6>Total Shipments</h6><h2>{{ shipments_count }}</h2></div></div>
</div>

<h4 class="mb-3"><i class="bi bi-boxes"></i> Vendor Stock</h4>
<div class="row g-3 mb-4">
    <div class="col-md-4">
        <div class="card stat-card divider-30d p-3">
            <div class="stat-icon"><i class="bi bi-box"></i></div>
            <h6>30D Stock</h6>
            <h2>{{ stock_30d }}</h2>
            {% if stock_30d < threshold %}<span class="badge bg-warning text-dark mt-2"><i class="bi bi-exclamation-triangle"></i> Low Stock</span>{% endif %}
        </div>
    </div>
    <div class="col-md-4">
        <div class="card stat-card divider-40d p-3">
            <div class="stat-icon"><i class="bi bi-box"></i></div>
            <h6>40D Stock</h6>
            <h2>{{ stock_40d }}</h2>
            {% if stock_40d < threshold %}<span class="badge bg-warning text-dark mt-2"><i class="bi bi-exclamation-triangle"></i> Low Stock</span>{% endif %}
        </div>
    </div>
    <div class="col-md-4">
        <div class="card stat-card divider-60d p-3">
            <div class="stat-icon"><i class="bi bi-box"></i></div>
            <h6>60D Stock</h6>
            <h2>{{ stock_60d }}</h2>
            {% if stock_60d < threshold %}<span class="badge bg-warning text-dark mt-2"><i class="bi bi-exclamation-triangle"></i> Low Stock</span>{% endif %}
        </div>
    </div>
</div>

<h4 class="mb-3"><i class="bi bi-bar-chart"></i> Required vs Shipped</h4>
<div class="row g-3 mb-4">
    <div class="col-md-4">
        <div class="card divider-30d-border p-3">
            <h5 class="divider-30d-text">30D</h5>
            <p class="mb-1">Required: <strong>{{ required_30d }}</strong></p>
            <p class="mb-1">Shipped: <strong class="text-success">{{ shipped_30d }}</strong></p>
            <p class="mb-0">Gap: <strong class="{% if gap_30d > 0 %}text-danger{% else %}text-success{% endif %}">{{ gap_30d }}</strong></p>
            <div class="progress mt-2" style="height: 8px;"><div class="progress-bar bg-info" style="width: {{ (shipped_30d / required_30d * 100) if required_30d > 0 else 0 }}%"></div></div>
        </div>
    </div>
    <div class="col-md-4">
        <div class="card divider-40d-border p-3">
            <h5 class="divider-40d-text">40D</h5>
            <p class="mb-1">Required: <strong>{{ required_40d }}</strong></p>
            <p class="mb-1">Shipped: <strong class="text-success">{{ shipped_40d }}</strong></p>
            <p class="mb-0">Gap: <strong class="{% if gap_40d > 0 %}text-danger{% else %}text-success{% endif %}">{{ gap_40d }}</strong></p>
            <div class="progress mt-2" style="height: 8px;"><div class="progress-bar bg-warning" style="width: {{ (shipped_40d / required_40d * 100) if required_40d > 0 else 0 }}%"></div></div>
        </div>
    </div>
    <div class="col-md-4">
        <div class="card divider-60d-border p-3">
            <h5 class="divider-60d-text">60D</h5>
            <p class="mb-1">Required: <strong>{{ required_60d }}</strong></p>
            <p class="mb-1">Shipped: <strong class="text-success">{{ shipped_60d }}</strong></p>
            <p class="mb-0">Gap: <strong class="{% if gap_60d > 0 %}text-danger{% else %}text-success{% endif %}">{{ gap_60d }}</strong></p>
            <div class="progress mt-2" style="height: 8px;"><div class="progress-bar" style="width: {{ (shipped_60d / required_60d * 100) if required_60d > 0 else 0 }}%; background-color: #9b59b6;"></div></div>
        </div>
    </div>
</div>

<div class="row g-3">
    <div class="col-md-8">
        <div class="card p-3">
            <h5><i class="bi bi-bar-chart-fill"></i> Overview Chart</h5>
            <canvas id="mainChart" height="120"></canvas>
        </div>
    </div>
    <div class="col-md-4">
        <div class="card p-3">
            <h5><i class="bi bi-pie-chart-fill"></i> Stock Distribution</h5>
            <canvas id="pieChart"></canvas>
        </div>
    </div>
</div>

{% endblock %}
{% block scripts %}
<script>
const isDark = document.body.classList.contains('dark-mode');
const textColor = isDark ? '#e0e0e0' : '#2c3e50';

new Chart(document.getElementById('mainChart'), {
    type: 'bar',
    data: {
        labels: ['30D', '40D', '60D'],
        datasets: [
            { label: 'Vendor Stock', data: [{{stock_30d}}, {{stock_40d}}, {{stock_60d}}], backgroundColor: '#3498db' },
            { label: 'Required', data: [{{required_30d}}, {{required_40d}}, {{required_60d}}], backgroundColor: '#f39c12' },
            { label: 'Shipped', data: [{{shipped_30d}}, {{shipped_40d}}, {{shipped_60d}}], backgroundColor: '#27ae60' }
        ]
    },
    options: { responsive: true, plugins: { legend: { labels: { color: textColor } } }, scales: { y: { beginAtZero: true, ticks: { color: textColor } }, x: { ticks: { color: textColor } } } }
});

new Chart(document.getElementById('pieChart'), {
    type: 'doughnut',
    data: {
        labels: ['30D', '40D', '60D'],
        datasets: [{ data: [{{stock_30d}}, {{stock_40d}}, {{stock_60d}}], backgroundColor: ['#3498db', '#e67e22', '#9b59b6'] }]
    },
    options: { responsive: true, plugins: { legend: { labels: { color: textColor } } } }
});
</script>
{% endblock %}'''

# ==================== stores.html ====================
stores_html = '''{% extends 'base.html' %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h2><i class="bi bi-shop"></i> Stores</h2>
    <button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#addStoreModal"><i class="bi bi-plus-circle"></i> Add Store</button>
</div>
<div class="card"><div class="table-responsive">
<table class="table table-hover mb-0">
<thead><tr><th>Name</th><th>Location</th><th class="divider-30d-text">Req. 30D</th><th class="divider-40d-text">Req. 40D</th><th class="divider-60d-text">Req. 60D</th><th>Actions</th></tr></thead>
<tbody>
{% for store in stores %}
<tr>
    <td><strong>{{ store.name }}</strong></td>
    <td>{{ store.location or '-' }}</td>
    <td><span class="badge-30d">{{ store.required_30d }}</span></td>
    <td><span class="badge-40d">{{ store.required_40d }}</span></td>
    <td><span class="badge-60d">{{ store.required_60d }}</span></td>
    <td>
        <button class="btn btn-sm btn-warning" data-bs-toggle="modal" data-bs-target="#editStoreModal{{ store.id }}"><i class="bi bi-pencil"></i></button>
        <a href="{{ url_for('delete_store', id=store.id) }}" class="btn btn-sm btn-danger" onclick="return confirm('Delete?')"><i class="bi bi-trash"></i></a>
    </td>
</tr>
<div class="modal fade" id="editStoreModal{{ store.id }}" tabindex="-1"><div class="modal-dialog"><form method="POST" action="{{ url_for('edit_store', id=store.id) }}"><div class="modal-content">
<div class="modal-header"><h5>Edit Store</h5><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>
<div class="modal-body">
<div class="mb-2"><label>Name</label><input name="name" class="form-control" value="{{ store.name }}" required></div>
<div class="mb-2"><label>Location</label><input name="location" class="form-control" value="{{ store.location or '' }}"></div>
<div class="mb-2"><label class="divider-30d-text"><i class="bi bi-box"></i> Required 30D</label><input type="number" name="required_30d" class="form-control" value="{{ store.required_30d }}"></div>
<div class="mb-2"><label class="divider-40d-text"><i class="bi bi-box"></i> Required 40D</label><input type="number" name="required_40d" class="form-control" value="{{ store.required_40d }}"></div>
<div class="mb-2"><label class="divider-60d-text"><i class="bi bi-box"></i> Required 60D</label><input type="number" name="required_60d" class="form-control" value="{{ store.required_60d }}"></div>
</div>
<div class="modal-footer"><button class="btn btn-primary">Save</button></div>
</div></form></div></div>
{% else %}
<tr><td colspan="6" class="text-center text-muted py-4"><i class="bi bi-inbox fs-1 d-block mb-2"></i>No stores yet. Click "Add Store" to start!</td></tr>
{% endfor %}
</tbody></table></div></div>
<div class="modal fade" id="addStoreModal" tabindex="-1"><div class="modal-dialog"><form method="POST" action="{{ url_for('add_store') }}"><div class="modal-content">
<div class="modal-header"><h5>Add Store</h5><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>
<div class="modal-body">
<div class="mb-2"><label>Name *</label><input name="name" class="form-control" required></div>
<div class="mb-2"><label>Location</label><input name="location" class="form-control"></div>
<div class="mb-2"><label class="divider-30d-text"><i class="bi bi-box"></i> Required 30D</label><input type="number" name="required_30d" class="form-control" value="0"></div>
<div class="mb-2"><label class="divider-40d-text"><i class="bi bi-box"></i> Required 40D</label><input type="number" name="required_40d" class="form-control" value="0"></div>
<div class="mb-2"><label class="divider-60d-text"><i class="bi bi-box"></i> Required 60D</label><input type="number" name="required_60d" class="form-control" value="0"></div>
</div>
<div class="modal-footer"><button class="btn btn-primary">Add Store</button></div>
</div></form></div></div>
{% endblock %}'''

# ==================== vendor_stock.html ====================
vendor_stock_html = '''{% extends 'base.html' %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h2><i class="bi bi-boxes"></i> Vendor Stock</h2>
    <button class="btn btn-outline-secondary" data-bs-toggle="modal" data-bs-target="#thresholdModal"><i class="bi bi-gear"></i> Settings</button>
</div>

<div class="alert alert-info alert-custom"><i class="bi bi-info-circle"></i> Low stock threshold is set to <strong>{{ threshold }}</strong> units. You'll get a warning when stock goes below this.</div>

<div class="row g-3 mb-4">
{% for stock in stocks %}
<div class="col-md-4"><div class="card stat-card divider-{{ stock.divider_type.lower() }} p-3">
<div class="stat-icon"><i class="bi bi-box-seam"></i></div>
<h5>{{ stock.divider_type }}</h5>
<h2>{{ stock.quantity }}</h2>
{% if stock.quantity == 0 %}
<span class="badge bg-danger mt-2"><i class="bi bi-x-circle"></i> Out of Stock</span>
{% elif stock.quantity < threshold %}
<span class="badge bg-warning text-dark mt-2"><i class="bi bi-exclamation-triangle"></i> Low Stock - Contact Vendor</span>
{% else %}
<span class="badge bg-success mt-2"><i class="bi bi-check-circle"></i> In Stock</span>
{% endif %}
<small class="text-muted mt-2">Updated: {{ stock.last_updated.strftime('%Y-%m-%d %H:%M') }}</small>
<form method="POST" action="{{ url_for('update_stock') }}" class="mt-2">
<input type="hidden" name="divider_type" value="{{ stock.divider_type }}">
<div class="input-group mb-2"><input type="number" name="quantity" class="form-control" value="{{ stock.quantity }}" required></div>
<input type="text" name="note" class="form-control mb-2" placeholder="Note (optional)">
<button class="btn btn-primary w-100"><i class="bi bi-arrow-clockwise"></i> Update</button>
</form>
</div></div>
{% endfor %}
</div>

<h4><i class="bi bi-clock-history"></i> Stock History (Last 20)</h4>
<div class="card"><div class="table-responsive">
<table class="table table-hover mb-0">
<thead><tr><th>Date</th><th>Type</th><th>Old Qty</th><th>New Qty</th><th>Change</th><th>Note</th></tr></thead>
<tbody>
{% for h in history %}
<tr>
<td>{{ h.date.strftime('%Y-%m-%d %H:%M') }}</td>
<td><span class="badge-{{ h.divider_type.lower() }}">{{ h.divider_type }}</span></td>
<td>{{ h.old_qty }}</td>
<td>{{ h.new_qty }}</td>
<td class="{% if h.change >= 0 %}text-success{% else %}text-danger{% endif %}"><strong>{{ '+' if h.change >= 0 else '' }}{{ h.change }}</strong></td>
<td>{{ h.note or '-' }}</td>
</tr>
{% else %}
<tr><td colspan="6" class="text-center text-muted py-4">No history yet</td></tr>
{% endfor %}
</tbody></table></div></div>

<div class="modal fade" id="thresholdModal" tabindex="-1"><div class="modal-dialog"><form method="POST" action="{{ url_for('update_threshold') }}"><div class="modal-content">
<div class="modal-header"><h5><i class="bi bi-gear"></i> Low Stock Threshold</h5><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>
<div class="modal-body">
<p class="text-muted">Get warned when vendor stock goes below this number.</p>
<div class="mb-2"><label>Threshold (units)</label><input type="number" name="threshold" class="form-control" value="{{ threshold }}" min="0" required></div>
</div>
<div class="modal-footer"><button class="btn btn-primary">Save</button></div>
</div></form></div></div>
{% endblock %}'''

# ==================== shipments.html ====================
shipments_html = '''{% extends 'base.html' %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
<h2><i class="bi bi-truck"></i> Shipments</h2>
<button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#addShipmentModal"><i class="bi bi-plus-circle"></i> Record Shipment</button>
</div>
<div class="card"><div class="table-responsive">
<table class="table table-hover mb-0">
<thead><tr><th>Date</th><th>Store</th><th class="divider-30d-text">30D</th><th class="divider-40d-text">40D</th><th class="divider-60d-text">60D</th><th>Notes</th><th>Actions</th></tr></thead>
<tbody>
{% for s in shipments %}
<tr>
<td>{{ s.date.strftime('%Y-%m-%d') }}</td>
<td><strong>{{ s.store.name }}</strong></td>
<td><span class="badge-30d">{{ s.qty_30d }}</span></td>
<td><span class="badge-40d">{{ s.qty_40d }}</span></td>
<td><span class="badge-60d">{{ s.qty_60d }}</span></td>
<td>{{ s.notes or '-' }}</td>
<td><a href="{{ url_for('delete_shipment', id=s.id) }}" class="btn btn-sm btn-danger" onclick="return confirm('Delete?')"><i class="bi bi-trash"></i></a></td>
</tr>
{% else %}
<tr><td colspan="7" class="text-center text-muted py-4"><i class="bi bi-truck fs-1 d-block mb-2"></i>No shipments yet</td></tr>
{% endfor %}
</tbody></table></div></div>
<div class="modal fade" id="addShipmentModal" tabindex="-1"><div class="modal-dialog"><form method="POST" action="{{ url_for('add_shipment') }}"><div class="modal-content">
<div class="modal-header"><h5>Record Shipment</h5><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>
<div class="modal-body">
<div class="mb-2"><label>Store *</label><select name="store_id" class="form-select" required><option value="">-- Select Store --</option>{% for store in stores %}<option value="{{ store.id }}">{{ store.name }}</option>{% endfor %}</select></div>
<div class="mb-2"><label>Date</label><input type="date" name="date" class="form-control"></div>
<div class="mb-2"><label class="divider-30d-text"><i class="bi bi-box"></i> Quantity 30D</label><input type="number" name="qty_30d" class="form-control" value="0"></div>
<div class="mb-2"><label class="divider-40d-text"><i class="bi bi-box"></i> Quantity 40D</label><input type="number" name="qty_40d" class="form-control" value="0"></div>
<div class="mb-2"><label class="divider-60d-text"><i class="bi bi-box"></i> Quantity 60D</label><input type="number" name="qty_60d" class="form-control" value="0"></div>
<div class="mb-2"><label>Notes</label><textarea name="notes" class="form-control"></textarea></div>
</div>
<div class="modal-footer"><button class="btn btn-primary">Save Shipment</button></div>
</div></form></div></div>
{% endblock %}'''

# ==================== reports.html ====================
reports_html = '''{% extends 'base.html' %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
<h2><i class="bi bi-graph-up"></i> Reports</h2>
<a href="{{ url_for('export_excel') }}" class="btn btn-success"><i class="bi bi-file-earmark-excel"></i> Export to Excel</a>
</div>
<div class="card"><div class="table-responsive">
<table class="table table-hover mb-0">
<thead>
<tr><th rowspan="2">Store</th><th rowspan="2">Location</th><th colspan="3" class="text-center divider-30d-bg">30D</th><th colspan="3" class="text-center divider-40d-bg">40D</th><th colspan="3" class="text-center divider-60d-bg">60D</th></tr>
<tr><th>Req</th><th>Ship</th><th>Gap</th><th>Req</th><th>Ship</th><th>Gap</th><th>Req</th><th>Ship</th><th>Gap</th></tr>
</thead>
<tbody>
{% for r in report_data %}
<tr>
<td><strong>{{ r.store.name }}</strong></td>
<td>{{ r.store.location or '-' }}</td>
<td>{{ r.store.required_30d }}</td>
<td class="text-success">{{ r.shipped_30 }}</td>
<td class="{% if r.gap_30 > 0 %}text-danger{% else %}text-success{% endif %}"><strong>{{ r.gap_30 }}</strong></td>
<td>{{ r.store.required_40d }}</td>
<td class="text-success">{{ r.shipped_40 }}</td>
<td class="{% if r.gap_40 > 0 %}text-danger{% else %}text-success{% endif %}"><strong>{{ r.gap_40 }}</strong></td>
<td>{{ r.store.required_60d }}</td>
<td class="text-success">{{ r.shipped_60 }}</td>
<td class="{% if r.gap_60 > 0 %}text-danger{% else %}text-success{% endif %}"><strong>{{ r.gap_60 }}</strong></td>
</tr>
{% else %}
<tr><td colspan="11" class="text-center text-muted py-4">No data yet</td></tr>
{% endfor %}
</tbody></table></div></div>
{% endblock %}'''

# ==================== style.css ====================
style_css = '''* { font-family: 'Segoe UI', 'Tahoma', sans-serif; }

:root {
    --bg-primary: #f5f7fa;
    --bg-secondary: #ffffff;
    --text-primary: #2c3e50;
    --text-secondary: #7f8c8d;
    --navbar-bg: linear-gradient(90deg, #1a2a3a 0%, #2c3e50 100%);
    --card-shadow: 0 2px 10px rgba(0,0,0,0.06);
    --card-shadow-hover: 0 8px 25px rgba(0,0,0,0.1);
    --border-color: #ecf0f1;
    --table-header-bg: linear-gradient(90deg, #2c3e50 0%, #34495e 100%);
    --input-border: #dfe6e9;
    --hover-bg: #f8f9fb;
    
    --color-30d: #3498db;
    --color-30d-light: #5dade2;
    --color-30d-dark: #2874a6;
    
    --color-40d: #e67e22;
    --color-40d-light: #eb984e;
    --color-40d-dark: #b9691b;
    
    --color-60d: #9b59b6;
    --color-60d-light: #b07cc6;
    --color-60d-dark: #6c3483;
}

body.dark-mode {
    --bg-primary: #1a1d24;
    --bg-secondary: #252932;
    --text-primary: #e4e6eb;
    --text-secondary: #b0b3b8;
    --navbar-bg: linear-gradient(90deg, #0d1117 0%, #161b22 100%);
    --card-shadow: 0 2px 10px rgba(0,0,0,0.4);
    --card-shadow-hover: 0 8px 25px rgba(0,0,0,0.6);
    --border-color: #3a3f4b;
    --table-header-bg: linear-gradient(90deg, #161b22 0%, #21262d 100%);
    --input-border: #3a3f4b;
    --hover-bg: #2d3139;
}

body {
    background: var(--bg-primary);
    color: var(--text-primary);
    min-height: 100vh;
    transition: background 0.3s ease, color 0.3s ease;
}

/* NAVBAR */
.navbar {
    background: var(--navbar-bg) !important;
    box-shadow: 0 4px 15px rgba(0,0,0,0.15);
    padding: 0.8rem 0;
}
.navbar-brand {
    font-size: 1.4rem;
    font-weight: 700 !important;
    color: #fff !important;
}
.navbar-brand i { color: #3498db; margin-right: 8px; }
.navbar-nav .nav-link {
    color: rgba(255,255,255,0.85) !important;
    padding: 0.5rem 1rem !important;
    margin: 0 3px;
    border-radius: 8px;
    transition: all 0.3s ease;
    font-weight: 500;
}
.navbar-nav .nav-link:hover {
    background: rgba(52, 152, 219, 0.25);
    color: #fff !important;
    transform: translateY(-2px);
}
.navbar-nav .nav-link i { margin-right: 5px; }

#darkModeToggle {
    border-radius: 20px;
    padding: 6px 15px;
    transition: all 0.3s ease;
}
#darkModeToggle:hover { transform: scale(1.05); }

/* CARDS */
.card {
    background: var(--bg-secondary);
    color: var(--text-primary);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    box-shadow: var(--card-shadow);
    transition: all 0.3s ease;
    overflow: hidden;
}
.card:hover { box-shadow: var(--card-shadow-hover); transform: translateY(-2px); }

/* STAT CARDS */
.stat-card {
    border-left: 5px solid;
    position: relative;
    overflow: hidden;
}
.stat-card .stat-icon {
    position: absolute;
    top: 15px;
    right: 15px;
    font-size: 2.5rem;
    opacity: 0.15;
}
.stat-card h6 {
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: var(--text-secondary) !important;
    margin-bottom: 10px;
    font-weight: 600;
}
.stat-card h2 {
    font-size: 2.8rem;
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
}

.stat-stores { border-left-color: #3498db; }
.stat-stores .stat-icon { color: #3498db; }
.stat-shipments { border-left-color: #27ae60; }
.stat-shipments .stat-icon { color: #27ae60; }

/* DIVIDER TYPES COLORS */
.divider-30d {
    border-left-color: var(--color-30d);
    background: linear-gradient(135deg, var(--bg-secondary) 0%, rgba(52, 152, 219, 0.05) 100%);
}
.divider-30d .stat-icon { color: var(--color-30d); }
.divider-30d h5, .divider-30d h2 { color: var(--color-30d) !important; }

.divider-40d {
    border-left-color: var(--color-40d);
    background: linear-gradient(135deg, var(--bg-secondary) 0%, rgba(230, 126, 34, 0.05) 100%);
}
.divider-40d .stat-icon { color: var(--color-40d); }
.divider-40d h5, .divider-40d h2 { color: var(--color-40d) !important; }

.divider-60d {
    border-left-color: var(--color-60d);
    background: linear-gradient(135deg, var(--bg-secondary) 0%, rgba(155, 89, 182, 0.05) 100%);
}
.divider-60d .stat-icon { color: var(--color-60d); }
.divider-60d h5, .divider-60d h2 { color: var(--color-60d) !important; }

.divider-30d-text { color: var(--color-30d) !important; font-weight: 600; }
.divider-40d-text { color: var(--color-40d) !important; font-weight: 600; }
.divider-60d-text { color: var(--color-60d) !important; font-weight: 600; }

.divider-30d-border { border-top: 4px solid var(--color-30d) !important; }
.divider-40d-border { border-top: 4px solid var(--color-40d) !important; }
.divider-60d-border { border-top: 4px solid var(--color-60d) !important; }

.divider-30d-bg { background-color: var(--color-30d) !important; color: white !important; }
.divider-40d-bg { background-color: var(--color-40d) !important; color: white !important; }
.divider-60d-bg { background-color: var(--color-60d) !important; color: white !important; }

.badge-30d {
    background: var(--color-30d);
    color: white;
    padding: 5px 12px;
    border-radius: 12px;
    font-weight: 600;
    font-size: 0.85rem;
}
.badge-40d {
    background: var(--color-40d);
    color: white;
    padding: 5px 12px;
    border-radius: 12px;
    font-weight: 600;
    font-size: 0.85rem;
}
.badge-60d {
    background: var(--color-60d);
    color: white;
    padding: 5px 12px;
    border-radius: 12px;
    font-weight: 600;
    font-size: 0.85rem;
}

/* TABLES */
.table { margin: 0; color: var(--text-primary); }
.table thead { background: var(--table-header-bg) !important; }
.table thead th {
    border: none !important;
    padding: 15px !important;
    font-weight: 600;
    font-size: 0.9rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: white !important;
}
.table tbody tr {
    transition: all 0.2s ease;
    border-bottom: 1px solid var(--border-color);
}
.table tbody tr:hover { background-color: var(--hover-bg) !important; }
.table tbody td {
    padding: 14px 15px !important;
    vertical-align: middle;
    border: none !important;
    color: var(--text-primary);
}

/* BUTTONS */
.btn {
    border-radius: 8px;
    padding: 8px 18px;
    font-weight: 500;
    transition: all 0.3s ease;
    border: none;
}
.btn:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
.btn-primary { background: linear-gradient(135deg, #3498db 0%, #2980b9 100%); }
.btn-success { background: linear-gradient(135deg, #27ae60 0%, #229954 100%); }
.btn-warning { background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%); color: white; }
.btn-danger { background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%); }
.btn-sm { padding: 5px 12px; font-size: 0.85rem; }
.btn-outline-secondary { border: 1.5px solid var(--input-border); color: var(--text-primary); background: transparent; }
.btn-outline-secondary:hover { background: var(--hover-bg); color: var(--text-primary); }

/* FORMS */
.form-control, .form-select {
    background: var(--bg-secondary);
    color: var(--text-primary);
    border-radius: 8px;
    border: 1.5px solid var(--input-border);
    padding: 10px 14px;
    transition: all 0.3s ease;
}
.form-control:focus, .form-select:focus {
    background: var(--bg-secondary);
    color: var(--text-primary);
    border-color: #3498db;
    box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.15);
}
label { font-weight: 600; color: var(--text-primary); font-size: 0.9rem; margin-bottom: 5px; }

/* MODALS */
.modal-content {
    background: var(--bg-secondary);
    color: var(--text-primary);
    border-radius: 12px;
    border: none;
    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
}
.modal-header {
    background: var(--table-header-bg);
    color: white;
    border-radius: 12px 12px 0 0 !important;
    border: none;
}
.modal-header h5 { margin: 0; font-weight: 600; }
.modal-header .btn-close { filter: invert(1); }
.modal-footer { border: none; padding: 15px 20px 20px; }

/* ALERTS */
.alert {
    border-radius: 10px;
    border: none;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    font-weight: 500;
    padding: 15px 20px;
}
.alert-custom { border-left: 5px solid; animation: slideIn 0.4s ease; }
.alert-danger { border-left-color: #e74c3c; }
.alert-warning { border-left-color: #f39c12; }
.alert-info { border-left-color: #3498db; }
.alert-success { border-left-color: #27ae60; }

/* BADGES */
.badge { padding: 6px 12px; border-radius: 6px; font-weight: 600; font-size: 0.8rem; }

/* HEADINGS */
h2 {
    color: var(--text-primary);
    font-weight: 700;
    margin-bottom: 25px;
    position: relative;
    padding-bottom: 10px;
}
h2::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    width: 60px;
    height: 4px;
    background: linear-gradient(90deg, #3498db 0%, #2980b9 100%);
    border-radius: 2px;
}
h4 { color: var(--text-primary); font-weight: 600; margin-top: 15px; }
h5 { color: var(--text-primary); font-weight: 600; }

/* PROGRESS */
.progress {
    background: var(--border-color);
    border-radius: 10px;
    overflow: hidden;
}

/* FOOTER */
.footer-custom {
    color: var(--text-secondary);
    border-top: 1px solid var(--border-color);
    margin-top: 40px;
}

/* SCROLLBAR */
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: var(--bg-primary); }
::-webkit-scrollbar-thumb { background: var(--text-secondary); border-radius: 5px; }
::-webkit-scrollbar-thumb:hover { background: var(--text-primary); }

/* ANIMATIONS */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
@keyframes slideIn {
    from { opacity: 0; transform: translateX(-20px); }
    to { opacity: 1; transform: translateX(0); }
}
.container { animation: fadeIn 0.4s ease; }

/* TEXT HELPERS */
.text-danger { font-weight: 700; }
.text-success { font-weight: 600; }
.text-muted { color: var(--text-secondary) !important; }
'''

# ==================== WRITE FILES ====================
files = {
    'app.py': app_py,
    'templates/base.html': base_html,
    'templates/dashboard.html': dashboard_html,
    'templates/stores.html': stores_html,
    'templates/vendor_stock.html': vendor_stock_html,
    'templates/shipments.html': shipments_html,
    'templates/reports.html': reports_html,
    'static/style.css': style_css,
}

for path, content in files.items():
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'✅ Updated: {path}')

print('\n🎉 All files upgraded successfully!')
print('🚀 Now run: python app.py')
print('📌 Features added:')
print('   ✓ Smart alerts for low stock')
print('   ✓ Color-coded divider types (30D=Blue, 40D=Orange, 60D=Purple)')
print('   ✓ Dark Mode toggle')
print('   ✓ Progress bars for shipments')
print('   ✓ Pie chart for stock distribution')
print('   ✓ Customizable low stock threshold')
print('   ✓ Stock status badges')
print('   ✓ Animated alerts')
