import os
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///product.sqlite')

#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'product.sqlite')
db = SQLAlchemy(app)

# Product model
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float)
    quantity = db.Column(db.Integer)


#Endpoint 1: Get all products
@app.route('/products', methods = ['GET'])
def get_products():
    products = Product.query.all()
    product_list = [{"id": product.id, "name": product.name, "price": product.price, "quantity": product.quantity} for product in products]
    return jsonify({"Products": product_list})

#Endpoint 2: get specific product
@app.route('/products/<int:product_id>', methods = {'GET'})
def get_product(product_id):
    product = Product.query.get(product_id)
    if product:
        return jsonify({"product": {"id": product.id, "name": product.name, "price": product.price, "quantity": product.quantity}})
    else:
        return jsonify({"error": "Product not found"}), 404
#Endpoint 3: add specific product    
@app.route('/products', methods = {'POST'})
def add_product():
    data = request.json
    if 'name' not in data:
        return jsonify({"error": "Name is required"}), 400
    new_product = Product(name = data['name'],price = data['price'], quantity = data['quantity'])

    db.session.add(new_product)
    db.session.commit()

    return jsonify({"message": "Task created", "task": {"id": new_product.id, "name": new_product.name, "price": new_product.price, "quantity": new_product.quantity}}), 201
#Endpoint 4: Change quantity of product
@app.route('/products/<int:product_id>/quantity', methods=['PATCH'])
def update_product_quantity(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    
    data = request.json
    change = data.get('quantity', 0)
    product.quantity += change
    
    if product.quantity < 0:
        return jsonify({"error": "Product quantity cannot be negative"}), 400
    
    db.session.commit()
    return jsonify({"message": "Product quantity updated"})

if __name__ == '__main__':
#    db.create_all()
    app.run()