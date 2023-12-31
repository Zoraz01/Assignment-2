import os
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import requests  

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///cart.sqlite')

#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cart.sqlite'
db = SQLAlchemy(app)

# CartItem model
class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    product_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)


# Endpoint 1: get total contents of the cart
@app.route('/cart/<int:user_id>', methods=['GET'])
def get_cart(user_id):
    cart_items = CartItem.query.filter_by(user_id=user_id).all()
    cart_list = []
    total_price = 0

    for item in cart_items:

        product_service_url = os.environ.get('PRODUCT_SERVICE_URL', 'http://127.0.0.1:5000')
        product_data = requests.get(f'{product_service_url}/products/{item.product_id}').json()['product']

        #product_data = requests.get(f'http://127.0.0.1:5000/products/{item.product_id}').json()['product']
        cart_list.append({
            'product_name': product_data['name'],
            'quantity': item.quantity,
            'price': product_data['price'],
            'total_price': product_data['price'] * item.quantity
        })
        total_price += product_data['price'] * item.quantity

    return jsonify({
        "cart": cart_list,
        "total_price": total_price
    })

# Endpoint 2: add products to the cart
@app.route('/cart/<int:user_id>/add/<int:product_id>', methods=['POST'])
def add_to_cart(user_id, product_id):
    quantity = request.json.get('quantity', 1)
    
    # Updating the Product Service
    product_service_url = os.environ.get('PRODUCT_SERVICE_URL', 'http://127.0.0.1:5000')
    response = requests.patch(f'{product_service_url}/products/{product_id}/quantity', json={'quantity': -quantity})
    if response.status_code != 200:
        app.logger.info("Debug: %s", response.json())
        return jsonify({"error": "Failed to update product quantity"}), 500
    
    item = CartItem.query.filter_by(user_id=user_id, product_id=product_id).first()
    if item:
        item.quantity += quantity
    else:
        new_item = CartItem(user_id=user_id, product_id=product_id, quantity=quantity)
        db.session.add(new_item)
    
    db.session.commit()
    return jsonify({"message": "Product added to cart"})

# Endpoint 3: delete products from the cart
@app.route('/cart/<int:user_id>/remove/<int:product_id>', methods=['POST'])
def remove_from_cart(user_id, product_id):
    payload = request.json
    if not payload or 'quantity' not in payload:
        return jsonify({"error": "Missing 'quantity' in payload"}), 400

    quantity_to_remove = payload['quantity']

    item = CartItem.query.filter_by(user_id=user_id, product_id=product_id).first()
    if item:
        if item.quantity < quantity_to_remove:
            return jsonify({"error": "Not enough items in the cart to remove"}), 400

        # Updating the Product Service
        product_service_url = os.environ.get('PRODUCT_SERVICE_URL', 'http://127.0.0.1:5000')
        response = requests.patch(f'{product_service_url}/products/{product_id}/quantity', json={'quantity': quantity_to_remove})
        
        if response.status_code != 200:
            app.logger.info("Debug: %s", response.json())
            return jsonify({"error": "Failed to update product quantity"}), 500

        item.quantity -= quantity_to_remove

        if item.quantity == 0:
            db.session.delete(item)
        else:
            db.session.merge(item)

        db.session.commit()
        return jsonify({"message": "Product quantity updated in cart"})
    else:
        return jsonify({"error": "Product not in cart"}), 404
    
if __name__ == '__main__':
#    db.create_all()  
    app.run(debug=True,port=5004)
