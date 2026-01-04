from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
app.config['SECRET_KEY'] = 'business_system_secret_key'

# Hifadhi ya muda (Data zitaanza hivi bosi akifungua)
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

@app.route('/add_product', methods=['POST'])
def add_product():
    # Tunapokea data kutoka kwenye fomu
    name = request.form.get('name')
    buying = int(request.form.get('buying_price'))
    selling = int(request.form.get('selling_price'))
    stock = int(request.form.get('stock'))
    
    # Tunatengeneza bidhaa mpya
    new_id = len(products) + 1
    products.append({'id': new_id, 'name': name, 'buying_price': buying, 'selling_price': selling, 'stock': stock})
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)

