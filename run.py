from flask import Flask, render_template, request, redirect, url_for
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'masanja_key_123'

# Data za majaribio (Maana SQLite inasumbua Vercel kuanzia mwanzo)
products = [
    {'id': 1, 'name': 'Cement', 'buying_price': 15000, 'selling_price': 18000, 'stock': 20},
    {'id': 2, 'name': 'Nondo', 'buying_price': 12000, 'selling_price': 15000, 'stock': 3}
]

@app.route('/')
def index():
    total_sales = sum([p['selling_price'] for p in products])
    low_stock_count = len([p for p in products if p['stock'] <= 5])
    return render_template('index.html', products=products, total_sales=total_sales, low_stock_count=low_stock_count)

@app.route('/inventory')
def inventory():
    return render_template('inventory.html', products=products)

if __name__ == '__main__':
    app.run(debug=True)

