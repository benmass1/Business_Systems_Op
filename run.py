from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'business_systems_op_secret_2026'

# Hifadhi ya muda (Mock Database)
products = [
    {'id': 1, 'name': 'Cement', 'buying_price': 15000, 'selling_price': 18000, 'stock': 20},
    {'id': 2, 'name': 'Nondo', 'buying_price': 12000, 'selling_price': 15000, 'stock': 3},
    {'id': 3, 'name': 'Mbao', 'buying_price': 5000, 'selling_price': 7000, 'stock': 15}
]

sales_history = []

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form.get('username').strip()
        pwd = request.form.get('password').strip()
        if user == 'admin' and pwd == '1234':
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            flash('Jina au Namba ya siri siyo sahihi!')
    return render_template('login.html')

@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    total_sales_value = sum(item['price'] for item in sales_history)
    low_stock_count = len([p for p in products if p['stock'] <= 5])
    return render_template('index.html', products=products, total_sales=total_sales_value, low_stock_count=low_stock_count)

@app.route('/inventory')
def inventory():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('inventory.html', products=products)

@app.route('/sales')
def sales():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('sales.html', sales=sales_history)

@app.route('/add_product', methods=['POST'])
def add_product():
    if not session.get('logged_in'): return redirect(url_for('login'))
    name = request.form.get('name')
    buying = int(request.form.get('buying_price'))
    selling = int(request.form.get('selling_price'))
    stock = int(request.form.get('stock'))
    new_id = len(products) + 1
    products.append({'id': new_id, 'name': name, 'buying_price': buying, 'selling_price': selling, 'stock': stock})
    return redirect(url_for('index'))

@app.route('/sell/<int:product_id>')
def sell_product(product_id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    for p in products:
        if p['id'] == product_id and p['stock'] > 0:
            p['stock'] -= 1
            sales_history.append({
                'name': p['name'],
                'price': p['selling_price'],
                'time': datetime.now().strftime("%H:%M:%S")
            })
            break
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)

