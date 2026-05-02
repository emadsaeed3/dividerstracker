from flask import Flask, render_template, request, redirect, url_for, flash, send_file
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
