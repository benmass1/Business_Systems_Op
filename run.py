from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_SET'] = 'sqlite:///business.db'
app.config['SECRET_KEY'] = 'masanja_secret_key'
db = SQLAlchemy(app)

# Model ya Bidhaa
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    buying_price = db.Column(db.Float, nullable=False)
    selling_price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)

# 1. Page ya Dashboard (Admin)
@app.route('/')
def index():
    products = Product.query.all()
    total_sales = sum([p.selling_price for p in products]) # Mfano wa mauzo
    low_stock_count = Product.query.filter(Product.stock <= 5).count()
    return render_template('index.html', products=products, total_sales=total_sales, low_stock_count=low_stock_count)

# 2. Page ya Inventory (Stoo)
@app.route('/inventory')
def inventory():
    products = Product.query.all()
    return render_template('inventory.html', products=products)

# 3. Kazi ya Kuongeza Bidhaa
@app.route('/add_product', methods=['POST'])
def add_product():
    name = request.form.get('name')
    buying = float(request.form.get('buying_price'))
    selling = float(request.form.get('selling_price'))
    stock = int(request.form.get('stock'))
    
    new_p = Product(name=name, buying_price=buying, selling_price=selling, stock=stock)
    db.session.add(new_p)
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

