import os
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import requests  

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///product.sqlite')

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
    app.logger.info(f"Fetching cart for user_id: {user_id}")
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

    app.logger.info(f"Cart fetched for user_id: {user_id}, total_price: {total_price}")
    return jsonify({
        "cart": cart_list,
        "total_price": total_price
    })

# Endpoint 2: add products to the cart
@app.route('/cart/<int:user_id>/add/<int:product_id>', methods=['POST'])
def add_to_cart(user_id, product_id):
    app.logger.info(f"Adding product_id: {product_id} to cart for user_id: {user_id}")
    quantity = request.json.get('quantity', 1)
    
    # Updating the Product Service
    product_service_url = os.environ.get('PRODUCT_SERVICE_URL', 'http://127.0.0.1:5000')
    response = requests.patch(f'{product_service_url}/products/{product_id}/quantity', json={'quantity': -quantity})
    if response.status_code != 200:
        app.logger.error(f"Failed to update product quantity for product_id: {product_id}")
        return jsonify({"error": "Failed to update product quantity"}), 500
    
    item = CartItem.query.filter_by(user_id=user_id, product_id=product_id).first()
    if item:
        item.quantity += quantity
    else:
        new_item = CartItem(user_id=user_id, product_id=product_id, quantity=quantity)
        db.session.add(new_item)
    
    db.session.commit()
    app.logger.info(f"Product added to cart for user_id: {user_id}, product_id: {product_id}, quantity: {quantity}")
    return jsonify({"message": "Product added to cart"})

# Endpoint 3: delete products from the cart
@app.route('/cart/<int:user_id>/remove/<int:product_id>', methods=['POST'])
def remove_from_cart(user_id, product_id):
    app.logger.info(f"Removing product_id: {product_id} from cart for user_id: {user_id}")
    item = CartItem.query.filter_by(user_id=user_id, product_id=product_id).first()
    if item:
        
        # Updating the Product Service
        product_service_url = os.environ.get('PRODUCT_SERVICE_URL', 'http://127.0.0.1:5000')
        response = requests.patch(f'{product_service_url}/products/{product_id}/quantity', json={'quantity': item.quantity})
        if response.status_code != 200:
            app.logger.error(f"Failed to update product quantity for product_id: {product_id}")
            return jsonify({"error": "Failed to update product quantity"}), 500
        
        db.session.delete(item)
        db.session.commit()
        app.logger.info(f"Product removed from cart for user_id: {user_id}, product_id: {product_id}")
        return jsonify({"message": "Product removed from cart"})
    else:
        app.logger.warning(f"Product not found in cart for user_id: {user_id}, product_id: {product_id}")
        return jsonify({"error": "Product not in cart"}), 404
    
if __name__ == '__main__':
    db.create_all()  
    app.run(debug=True,port=5004)
