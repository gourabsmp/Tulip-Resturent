from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import razorpay

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tulip_premium_secure_key_2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///restaurant.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

razorpay_client = razorpay.Client(auth=("YOUR_RAZORPAY_KEY_ID", "YOUR_RAZORPAY_KEY_SECRET"))

# --- DATABASE MODELS ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    orders = db.relationship('Order', backref='customer', lazy=True)

class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50))
    image_url = db.Column(db.String(255)) 

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) 
    order_details = db.Column(db.String(500), nullable=False) 
    subtotal = db.Column(db.Float, nullable=False)
    tax = db.Column(db.Float, nullable=False)
    total = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default="Pending")
    razorpay_order_id = db.Column(db.String(100))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# NEW: Table Booking Model
class TableBooking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    time = db.Column(db.String(20), nullable=False)
    guests = db.Column(db.Integer, nullable=False)
    requests = db.Column(db.String(255))
    status = db.Column(db.String(20), default="Confirmed")
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# --- INITIALIZE DATABASE ---
with app.app_context():
    db.drop_all() # Resets DB to add new tables cleanly
    db.create_all() 
    
    # 20-Item Menu
    realistic_menu = [
        MenuItem(name="Sweet Corn Chicken Soup", description="Classic thick soup with sweet corn and minced chicken.", price=140.0, category="Soups & Appetizers", image_url="https://images.unsplash.com/photo-1548943487-a2e4e43b4859?w=500&q=80"),
        MenuItem(name="Hot & Sour Veg Soup", description="Spicy and tangy dark broth with finely chopped Asian greens.", price=120.0, category="Soups & Appetizers", image_url="https://images.unsplash.com/photo-1547592180-85f173990554?w=500&q=80"),
        MenuItem(name="Crispy Chilli Babycorn", description="Fried baby corn tossed in a spicy, tangy Asian sauce.", price=160.0, category="Soups & Appetizers", image_url="https://images.unsplash.com/photo-1585238342024-78d387f4a707?w=500&q=80"),
        MenuItem(name="Drums of Heaven", description="Crispy fried chicken wings tossed in a sweet and spicy Schezwan sauce.", price=220.0, category="Soups & Appetizers", image_url="https://images.unsplash.com/photo-1569058242253-92a9c755a0ec?w=500&q=80"),

        MenuItem(name="Paneer Tikka Kebab", description="Charcoal-grilled cottage cheese marinated in spiced yogurt.", price=190.0, category="Tandoor Starters", image_url="https://images.unsplash.com/photo-1599487488170-d11ec9c172f0?w=500&q=80"),
        MenuItem(name="Chicken Reshmi Kebab", description="Melt-in-mouth chicken chunks marinated in cream and cashew paste.", price=240.0, category="Tandoor Starters", image_url="https://images.unsplash.com/photo-1628296509355-6b5791cc2626?w=500&q=80"),
        MenuItem(name="Tandoori Chicken (Half)", description="Bone-in chicken marinated in traditional red spices and roasted in a clay oven.", price=260.0, category="Tandoor Starters", image_url="https://images.unsplash.com/photo-1599487488170-d11ec9c172f0?w=500&q=80"),
        MenuItem(name="Fish Tikka Amritsari", description="Tender Bhetki fish cubes marinated in mustard oil and Indian spices.", price=290.0, category="Tandoor Starters", image_url="https://images.unsplash.com/photo-1598514982205-f36b96d1e8d4?w=500&q=80"),

        MenuItem(name="Special Chicken Biryani", description="Aromatic basmati rice cooked with tender chicken, egg, and potato.", price=280.0, category="Indian Mains", image_url="https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=500&q=80"),
        MenuItem(name="Mutton Biryani", description="Classic Kolkata style biryani with succulent mutton pieces and aloo.", price=320.0, category="Indian Mains", image_url="https://images.unsplash.com/photo-1631515243349-e0cb75fb8d3a?w=500&q=80"),
        MenuItem(name="Bengali Mutton Kosha", description="Slow-cooked, dark, and spicy mutton curry. A true Bankura favorite.", price=380.0, category="Indian Mains", image_url="https://images.unsplash.com/photo-1604908176997-125f25cc6f3d?w=500&q=80"),
        MenuItem(name="Butter Paneer Masala", description="Rich tomato-butter gravy with soft cottage cheese.", price=250.0, category="Indian Mains", image_url="https://images.unsplash.com/photo-1631452180519-c014fe946bc3?w=500&q=80"),
        MenuItem(name="Chicken Tikka Masala", description="Roasted chicken chunks in a spicy, creamy, orange curry sauce.", price=270.0, category="Indian Mains", image_url="https://images.unsplash.com/photo-1565557623262-b51c2513a641?w=500&q=80"),
        MenuItem(name="Dal Makhani Classic", description="Black lentils simmered overnight with butter and fresh cream.", price=190.0, category="Indian Mains", image_url="https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=500&q=80"),

        MenuItem(name="Chilli Chicken (Dry/Gravy)", description="Diced chicken tossed with capsicum, onion, and dark soy sauce.", price=240.0, category="Chinese", image_url="https://images.unsplash.com/photo-1525755662778-989d0524087e?w=500&q=80"),
        MenuItem(name="Mixed Hakka Noodles", description="Wok-tossed noodles with chicken, egg, prawns, and veggies.", price=210.0, category="Chinese", image_url="https://images.unsplash.com/photo-1612929633738-8fe44f7ec841?w=500&q=80"),
        MenuItem(name="Burnt Garlic Fried Rice", description="Aromatic jasmine rice stir-fried with roasted garlic and scallions.", price=190.0, category="Chinese", image_url="https://images.unsplash.com/photo-1603133872878-684f208fb84b?w=500&q=80"),
        MenuItem(name="Paneer Manchurian", description="Cottage cheese dumplings in a tangy, dark coriander sauce.", price=220.0, category="Chinese", image_url="https://images.unsplash.com/photo-1564834724105-918b73d1b9e0?w=500&q=80"),

        MenuItem(name="Butter Naan", description="Soft, fluffy tandoori flatbread brushed with melted butter.", price=50.0, category="Breads & Sides", image_url="https://images.unsplash.com/photo-1626700051175-6818013e1d4f?w=500&q=80"),
        MenuItem(name="Garlic Naan", description="Tandoor-baked flatbread topped with minced garlic and coriander.", price=65.0, category="Breads & Sides", image_url="https://images.unsplash.com/photo-1601050690597-df0568f70950?w=500&q=80"),
        MenuItem(name="Tandoori Roti", description="Whole wheat bread baked in a traditional clay oven.", price=30.0, category="Breads & Sides", image_url="https://images.unsplash.com/photo-1565557623262-b51c2513a641?w=500&q=80"),
        MenuItem(name="Jeera Rice", description="Basmati rice tempered with cumin seeds and pure ghee.", price=130.0, category="Breads & Sides", image_url="https://images.unsplash.com/photo-1512621820151-d50c8ac50262?w=500&q=80"),

        MenuItem(name="Baked Mihidana", description="A local Bankura special! Baked sweet micro-boondi with rabri.", price=120.0, category="Desserts & Beverages", image_url="https://images.unsplash.com/photo-1589115795898-103630f732cc?w=500&q=80"),
        MenuItem(name="Sizzling Brownie", description="Warm chocolate brownie topped with vanilla ice cream and hot fudge.", price=180.0, category="Desserts & Beverages", image_url="https://images.unsplash.com/photo-1606313564200-e75d5e30476c?w=500&q=80"),
        MenuItem(name="Fresh Lime Mint Cooler", description="Refreshing sparkling water with crushed mint and lemon.", price=90.0, category="Desserts & Beverages", image_url="https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?w=500&q=80"),
        MenuItem(name="Virgin Mojito", description="A classic mocktail with muddled lime, mint, and sprite.", price=130.0, category="Desserts & Beverages", image_url="https://images.unsplash.com/photo-1551538827-9c037cb4f32a?w=500&q=80")
    ]
    db.session.add_all(realistic_menu)
    db.session.commit()

@app.route('/')
def home(): return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if User.query.filter_by(email=request.form['email']).first(): return "Email exists!"
        new_user = User(name=request.form['name'], email=request.form['email'], password_hash=generate_password_hash(request.form['password']))
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user and check_password_hash(user.password_hash, request.form['password']):
            session['user_id'] = user.id; session['user_name'] = user.name
            return redirect(url_for('home'))
        return "Invalid Credentials."
    return render_template('login.html')

@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('home'))

@app.route('/api/menu', methods=['GET'])
def get_menu(): return jsonify([{"id": i.id, "name": i.name, "description": i.description, "price": i.price, "category": i.category, "image": i.image_url} for i in MenuItem.query.all()])

@app.route('/api/create_order', methods=['POST'])
def create_order():
    cart = request.json.get('cart', [])
    if not cart: return jsonify({"error": "Empty Cart"}), 400
    subtotal = sum(i['price'] * i['quantity'] for i in cart); tax = subtotal * 0.05; total = subtotal + tax
    try:
        payment_data = {"amount": int(total * 100), "currency": "INR", "receipt": f"tulip_{datetime.now().strftime('%H%M%S')}"}
        razorpay_order = razorpay_client.order.create(data=payment_data)
        new_order = Order(user_id=session.get('user_id'), order_details=str([f"{i['name']} (x{i['quantity']})" for i in cart]), subtotal=subtotal, tax=tax, total=total, razorpay_order_id=razorpay_order['id'])
        db.session.add(new_order)
        db.session.commit()
        return jsonify({"razorpay_order_id": razorpay_order['id'], "amount": payment_data['amount']})
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/api/payment_success', methods=['POST'])
def payment_success():
    order = Order.query.filter_by(razorpay_order_id=request.json['razorpay_order_id']).first()
    if order: order.status = "Paid"; db.session.commit()
    return jsonify({"status": "success"})

# NEW: Route to handle table bookings
@app.route('/api/book_table', methods=['POST'])
def book_table():
    data = request.json
    try:
        new_booking = TableBooking(
            user_id=session.get('user_id'),
            name=data.get('name'), phone=data.get('phone'),
            date=data.get('date'), time=data.get('time'),
            guests=data.get('guests'), requests=data.get('requests', '')
        )
        db.session.add(new_booking)
        db.session.commit()
        return jsonify({"status": "success", "message": f"Table reserved for {data.get('guests')} guests on {data.get('date')} at {data.get('time')}."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

ADMIN_PASS = generate_password_hash("admin123")
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if check_password_hash(ADMIN_PASS, request.form['password']):
            session['admin_logged_in'] = True; return redirect(url_for('admin_dashboard'))
    return render_template('admin_login.html')

@app.route('/admin')
def admin_dashboard():
    if not session.get('admin_logged_in'): return redirect(url_for('admin_login'))
    
    # Pass orders, menu, and bookings to the admin dashboard
    orders = Order.query.order_by(Order.timestamp.desc()).all()
    menu = MenuItem.query.all()
    bookings = TableBooking.query.order_by(TableBooking.timestamp.desc()).all()
    
    return render_template('admin.html', orders=orders, menu=menu, bookings=bookings)

@app.route('/admin/logout')
def admin_logout(): session.pop('admin_logged_in', None); return redirect(url_for('home'))

if __name__ == '__main__': app.run(debug=True, host='0.0.0.0', port=5000)