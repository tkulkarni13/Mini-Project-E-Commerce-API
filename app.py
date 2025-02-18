from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow import fields
from marshmallow import ValidationError
from password import password

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] =\
    f'mysql+mysqlconnector://root:{password}@localhost/e_commerce_db'
db = SQLAlchemy(app)
ma = Marshmallow(app)

# Schema
class CustomerSchema(ma.Schema):
    name = fields.String(required=True)
    email = fields.String(required=True)
    phone = fields.String(required=True)

    class Meta:
        fields = ("name", "email", "phone", "id")

customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)

class CustomerAccountSchema(ma.Schema):
    username = fields.String(required=True)
    password = fields.String(required=True)
    customer_id = fields.Integer(required=True)

    class Meta:
        fields = ("username", "password", "customer_id", "id")

customer_account_schema = CustomerAccountSchema()
customer_accounts_schema = CustomerAccountSchema(many=True)

class ProductSchema(ma.Schema):
    name = fields.String(required=True)
    price = fields.Float(required=True)
    stock = fields.Integer(required=True)

    class Meta:
        fields = ("name", "price", "stock", "id")

product_schema = ProductSchema()
products_schema = ProductSchema(many=True)

class OrderSchema(ma.Schema):
    date = fields.Date(required=True)
    customer_id = fields.Integer(required=True)
    status = fields.String(required=True)

    class Meta:
        fields = ("date", "customer_id", "status", "id")

order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)

# Setting up SQL tables
class Customer(db.Model):
    __tablename__ = 'Customers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(320))
    phone = db.Column(db.String(15))
    orders = db.relationship('Order', backref='customer')

class CustomerAccount(db.Model):
    __tablename__ = 'Customer_Accounts'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('Customers.id'))
    customer = db.relationship('Customer', backref='customer_account', uselist=False)

order_product = db.Table('Order_Product',
                db.Column('order_id', db.Integer, db.ForeignKey('Orders.id'), primary_key=True),
                db.Column('product_id', db.Integer, db.ForeignKey('Products.id'), primary_key=True))

class Product(db.Model):
    __tablename__ = "Products"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)

class Order(db.Model):
    __tablename__ = 'Orders'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('Customers.id'))
    status = db.Column(db.String(255), default='pending')
    products = db.relationship('Product', secondary=order_product, backref=db.backref('orders'))

# Routes
# Homepage
@app.route('/', methods=["GET"])
def homepage():
    return "Welcome to the e-commerce API."

# Get all customers
@app.route('/customers', methods=["GET"])
def get_customers():
    customers = Customer.query.all()
    return customers_schema.jsonify(customers)

# Add a customer
@app.route('/customers', methods=["POST"])
def add_customer():
    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    new_customer = Customer(name=customer_data['name'], email=customer_data['email'],\
                            phone=customer_data['phone'])
    db.session.add(new_customer)
    db.session.commit()
    return jsonify({'message': "New customer successfully added."}), 200

# Get customer by their id
@app.route('/customers/<int:id>', methods=["GET"])
def get_customer(id):
    customer = Customer.query.get(id)
    if customer:
        return customer_schema.jsonify(customer)
    else:
        return jsonify({"message": "Customer not found"}), 404

# Update customer
@app.route('/customers/<int:id>', methods=['PUT'])
def update_customer(id):
    customer = Customer.query.get_or_404(id)
    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    customer.name = customer_data['name']
    customer.email = customer_data['email']
    customer.phone = customer_data['phone']
    db.session.commit()
    return jsonify({'message': 'Customer updated successfully'}), 200

# Delete customer
@app.route('/customers/<int:id>', methods=['DELETE'])
def delete_customer(id):
    customer = Customer.query.get_or_404(id)
    db.session.delete(customer)
    db.session.commit()
    return jsonify({'message': 'Customer deleted sucessfully'}), 200

# Add a customer accounts
@app.route('/customer-accounts', methods=["POST"])
def add_customer_account():
    try:
        customer_account_data = customer_account_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    new_customer_account = CustomerAccount(username=customer_account_data['username'],
                                           password=customer_account_data['password'],
                                           customer_id=customer_account_data['customer_id'])
    db.session.add(new_customer_account)
    db.session.commit()
    return jsonify({'message': "New customer account successfully added."}), 200

# Get all customer accounts
@app.route('/customer-accounts', methods=["GET"])
def get_customer_accounts():
    accounts = CustomerAccount.query.all()
    return customer_accounts_schema.jsonify(accounts)

# Get customer account details by customer id
@app.route('/customer-accounts/<int:id>', methods=["GET"])
def get_customer_account_details(id):
    customer = Customer.query.get(id)
    account = CustomerAccount.query.filter_by(customer_id=id)

    if customer and account.count() > 0:
        account_data = {
        "account_id": account[0].id,
        "username": account[0].username,
        "password": account[0].password,
        "customer": {
            "id" : customer.id,
            "name" : customer.name,
            "email" : customer.email,
            "phone" : customer.phone
        }
    }

        return jsonify(account_data)
    else:
        return jsonify({"message": "Customer account not found"}), 404
    
# Update customer account
@app.route('/customer-accounts/<int:id>', methods=['PUT'])
def update_customer_account(id):
    account = CustomerAccount.query.get_or_404(id)
    try:
        account_data = customer_account_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    account.username = account_data['username']
    account.password = account_data['password']
    account.customer_id = account_data['customer_id']
    db.session.commit()
    return jsonify({'message': 'Customer account updated successfully'}), 200

# Delete customer account
@app.route('/customer-accounts/<int:id>', methods=['DELETE'])
def delete_customer_account(id):
    account = CustomerAccount.query.get_or_404(id)
    db.session.delete(account)
    db.session.commit()
    return jsonify({'message': 'Customer account deleted sucessfully'}), 200

# Add product
@app.route('/products', methods=["POST"])
def add_product():
    try:
        product_data = product_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    new_product = Product(name=product_data['name'], price=product_data['price'],\
                            stock=product_data['stock'])
    db.session.add(new_product)
    db.session.commit()
    return jsonify({'message': "New product successfully added."}), 200

# View all products
@app.route('/products', methods=["GET"])
def get_products():
    products = Product.query.all()
    return products_schema.jsonify(products)

# View product by id
@app.route('/products/<int:id>', methods=["GET"])
def get_product(id):
    product = Product.query.get(id)
    if product:
        return product_schema.jsonify(product)
    else:
        return jsonify({"message": "Product not found"}), 404

# Update product
@app.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    product = Product.query.get_or_404(id)
    try:
        product_data = product_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    product.name = product_data['name']
    product.price = product_data['price']
    product.stock = product_data['stock']
    db.session.commit()
    return jsonify({'message': 'Product updated successfully'}), 200

# Bonus - Update stock of product
@app.route("/products/<int:id>/stock", methods=["PUT"])
def update_product_stock(id):
    product = Product.query.get_or_404(id)
    try:
        product_data = request.json
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    if 'stock' in product_data:
        product.stock = product_data['stock']
        db.session.commit()
        return jsonify({"message" : "Stock level updataed"})

    return jsonify({"error" : "Invalid request"})

# Bonus - Restock products if stock is low
@app.route("/products/<int:id>/restock", methods=["PUT"])
def restock_product(id):
    restock_threshold = 3
    restock_quantity = 5
    product = Product.query.get_or_404(id)

    # Restock when only 2 items are remaining in stock
    if product.stock < restock_threshold:
        product.stock = product.stock + restock_quantity
        db.session.commit()
        return jsonify({"message": "Product restocked"})
    else:
        return jsonify({"message": "Product restocking not necessary"})

# Delete product
@app.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({'message': 'Product deleted sucessfully'}), 200

# Add order
@app.route("/orders", methods=["POST"])
def add_order():
    try:
        order_data = request.json
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    if not order_data or 'date' not in order_data or 'customer_id' not in order_data or 'products' not in order_data:
        return jsonify({"error": "Please enter order date, customer id, and order products"}), 400
    
    customer = Customer.query.get(order_data['customer_id'])
    if not customer:
        return jsonify({"error": "Customer not found"}), 404

    new_order = Order(date=order_data['date'], customer_id=order_data['customer_id'])

    for product_id in order_data['products']:
        product = Product.query.get(product_id)
        if not product:
            return jsonify ({"error": f"Product with id {product_id} not found"})
        if product.stock < 1:
            return jsonify({"error": f"Insufficient stock for product {product.name}"})

        product.stock = product.stock - 1
        new_order.products.append(product)
        
    db.session.add(new_order)
    db.session.commit()
    return jsonify({"message": "New order added successfully"})

# Get all orders
@app.route("/orders", methods=["GET"])
def get_orders():
    orders = Order.query.all()
    return orders_schema.jsonify(orders)

# Get order by id
@app.route("/orders/<int:id>", methods=["GET"])
def get_order(id):
    order = Order.query.get(id)
    if order:
        order_data = {
            "id": order.id,
            "date": order.date,
            "customer_id": order.customer_id,
            "status": order.status,
            "products": [{"product_id": p.id, "name": p.name, "price": p.price} for p in order.products]
        }
        return jsonify(order_data)
    else:
        return jsonify({"message": "Order not found"}), 404

# Track status of order
@app.route("/orders/<int:id>/status", methods=["GET"])
def track_order(id):
    order = Order.query.get(id)
    if order:
        return jsonify({"status": order.status})
    else:
        return jsonify({"error": "Order not found"}), 404

# Update status of order
@app.route("/orders/<int:id>/status", methods=["PUT"])
def update_status(id):
    order = Order.query.get(id)
    try:
        updated_status = request.json
    except ValidationError as e:
        return jsonify(e.messages), 400

    if not updated_status or 'status' not in updated_status:
        return jsonify({"error": "Please enter only the updated status"})

    if order:
        order.status = updated_status['status']
        db.session.commit()
        return jsonify({"message": "Order status updated"})
    else:
        return jsonify({"error": "Order not found"})
    
# Bonus - Manage customer order history
@app.route("/orders/customer/<int:id>", methods=["GET"])
def get_orders_from_customer_id(id):
    orders = Order.query.filter_by(customer_id=id)
    orders_data = []
    if orders.count() > 0:
        for order in orders:
            order_data = {
                "id": order.id,
                "date": order.date,
                "customer_id": order.customer_id,
                "status": order.status,
                "products": [{"product_id": p.id, "name": p.name, "price": p.price} for p in order.products]
            }
            orders_data.append(order_data)
        return jsonify(orders_data)
    else:
        return jsonify({"error": "Customer orders not found"})
    
# Bonus - Calculate order price
@app.route("/orders/<int:id>/price", methods=["GET"])
def get_order_price(id):
    order = Order.query.get(id)
    if order:
        total_price = 0
        for p in order.products:
            total_price += p.price
        return jsonify({"order price": total_price})
    else:
        return jsonify({"error": "Order not found"})

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)