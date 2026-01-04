from flask import Flask, render_template, request, redirect, url_for, flash, session

app = Flask(__name__)
app.secret_key = 'business_system_op_key'

# Data za Bidhaa
products = [
    {'id': 1, 'name': 'Cement', 'buying_price': 15000, 'selling_price': 18000, 'stock': 20},
    {'id': 2, 'name': 'Nondo', 'buying_price': 12000, 'selling_price': 15000, 'stock': 3}
]

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form.get('username')
        pwd = request.form.get('password')
        
        # Username: admin | Password: password123
        if user == 'admin' and pwd == 'password123':
            session['logged_in'] = True
            session['user_role'] = 'admin'
            return redirect(url_for('index'))
        else:
            flash('Jina au Namba ya siri siyo sahihi!')
            
    return render_template('login.html')

@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    total_sales = sum([p['selling_price'] for p in products])
    low_stock_count = len([p for p in products if p['stock'] <= 5])
    return render_template('index.html', products=products, total_sales=total_sales, low_stock_count=low_stock_count)

@app.route('/inventory')
def inventory():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('inventory.html', products=products)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)

