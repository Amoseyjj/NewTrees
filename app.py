from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
from werkzeug.utils import secure_filename
import os

UPLOAD_FOLDER = 'static/product_images/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,   -- Unique ID for each product
            name TEXT NOT NULL,                     -- Name of the product
            description TEXT NOT NULL,              -- Description of the product
            price REAL NOT NULL,                    -- Price of the product (supports decimal)
            username TEXT DEFAULT 'Guest',          -- Default username as Guest
            ptype TEXT NOT NULL,                    -- Pre-owned or marketplace
            image TEXT,                             -- Store the image filename
            image_extension TEXT                    -- Store the image file extension
        )
    ''')  # Create the table if it doesn't exist
    conn.commit()
    conn.close()

init_db()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def actual_home():
    return render_template('actual_home.html')

@app.route('/home')
def home():
    #connect to the db
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    #fetch db data
    cursor.execute("SELECT * FROM products WHERE ptype = 'pre-owned'")
    products = cursor.fetchall()
    conn.close()

    #price 2dp
    products = [(p[0], p[1], p[2], "{:.2f}".format(p[3]), p[4], p[5], p[6]) for p in products]

    return render_template('home.html', products=products)

@app.route('/form_fields/<product_type>', methods=['POST'])
def submit_form(product_type):
    product_name = request.form['product_name']
    product_desc = request.form['product_desc']
    product_price = float(request.form['product_price'])

    # Step 1: Insert product WITHOUT image filename and extension (temporary NULL values)
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO products (name, description, price, ptype, image, image_extension) VALUES (?, ?, ?, ?, NULL, NULL)",
        (product_name, product_desc, product_price, product_type)
    )
    product_id = cursor.lastrowid  # Get the auto-incremented product ID
    print(f"Product ID: {product_id}")
    
    # Step 2: Handle Image Upload
    if 'product_image' in request.files:
        print('Image uploaded!')
        file = request.files['product_image']
        print(f"File name: {file.filename}")
        
        if file and allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower()  # Get the file extension
            filename = f"{product_id}.{ext}"  # Rename file using product_id and extension
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)  # Save the file

            # Step 3: Update the product record with the new image filename and extension
            cursor.execute("UPDATE products SET image = ?, image_extension = ? WHERE id = ?", (filename, ext, product_id))
    
    conn.commit()
    conn.close()

    # Redirect to the appropriate page based on product type
    if product_type == 'pre-owned':
        return redirect(url_for('home'))  # Redirect to home page if product type is 'pre-owned'
    else:
        return redirect(url_for('market'))  # Redirect to market page if it's another type

@app.route('/product/<int:product_id>')
def product_details(product_id):
    referrer = request.args.get('referrer', request.referrer)  # Get the referrer or fallback to request.referrer
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,)) #select from db based on id
    product = cursor.fetchone()
    conn.close()
    if not product:
        return "Product not found", 404
    return render_template('product_details.html', product=product, referrer=referrer)

#get all products
def get_products():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    conn.close()
    return products

@app.route('/update_product/<int:product_id>', methods=['POST'])
def update_product(product_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Get the form data
    new_product_name = request.form.get('new_product_name')
    new_product_desc = request.form.get('new_product_desc')
    new_product_price = request.form.get('new_product_price')
    new_product_seller = request.form.get('new_product_seller')
    referrer = request.form.get('referrer')  # Capture the original referrer

    #use form data to create update
    update_query = "UPDATE products SET"
    params = []

    if new_product_name:
        update_query += " name = ?,"
        params.append(new_product_name)
    if new_product_desc:
        update_query += " description = ?,"
        params.append(new_product_desc)
    if new_product_price:
        update_query += " price = ?,"
        params.append(new_product_price)
    if new_product_seller:
        update_query += " username = ?,"
        params.append(new_product_seller)

    update_query = update_query.rstrip(',')
    update_query += " WHERE id = ?"
    params.append(product_id)

    # Execute the query
    cursor.execute(update_query, tuple(params))
    conn.commit()
    conn.close()

    return redirect(url_for('product_details', product_id=product_id, referrer=referrer))

@app.route('/delete_product')
def delete_product():
    product_id = request.args.get('product_id')
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,)) #delete based off id
    conn.commit()
    conn.close()
    # Redirect to the referring page or fallback to 'home' if referrer is not available
    referrer = request.args.get('referrer') or request.referrer or url_for('home')
    return redirect(referrer)

@app.route('/market')
def market():
    #connect to the db
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    #fetch db data
    cursor.execute("SELECT * FROM products WHERE ptype = 'market'")
    products = cursor.fetchall()
    conn.close()

    #price 2dp
    products = [(p[0], p[1], p[2], "{:.2f}".format(p[3]), p[4], p[5], p[6]) for p in products]

    return render_template('market.html', products=products)



"""
AMOS CONTACT FUNCTIONS
"""
from Forms import CreateContactForm
import shelve
import ContactForm

app.static_folder = 'static'
DATABASE = "contact.db"

# Hardcoded chatbot responses
responses = {
    "hi": "Hello! How can I help you today?",
    "hello": "Hey there! What do you need help with?",
    "buying": "Buying help: You can browse products in our Marketplace and Pre-Owned section.",
    "selling": "Selling help: List your items under the Pre-Owned and Marketplace section. You must be logged in to an account list a product.",
    "account": "Account help: You can view your account details in the footer.",
    "help": "I can help with Buying, Selling, and Account Management. Ask away!",
    "default": "Sorry, I didn’t understand that. Could you rephrase your question?",
    "i need help with a return": "Got it! Let’s sort out your return. Could you please provide your order number so I "
                                 "can assist you?",
    "sure, it's #123456789": "Would you like to return this item? If yes, can you tell me the reason? (e.g. defective, "
                             "change of mind, missing items, etc.)",
    "the item was defective": "Sorry to hear that! I’ll process your return request. Please pack the item securely and "
    "use the shipping label sent to your email. Once the item is received and inspected, your refund will be processed "
    "within 5 business days.",
    #i added some incase -reygan
    "1":"Buying help: You can browse products in our Marketplace and Pre-Owned section.",
    "1.buying":"Buying help: You can browse products in our Marketplace and Pre-Owned section.",
    "2":"Selling help: List your items under the Pre-Owned and Marketplace section. You must be logged in to an account list a product.",
    "2.selling":"Selling help: List your items under the Pre-Owned and Marketplace section. You must be logged in to an account list a product.",
    "3": "Account help: You can view your account details in the footer.",
    "3.account": "Account help: You can view your account details in the footer.",
}


def store_rating(rating):
    """Stores a rating and updates individual rating counts and satisfaction count."""
    with shelve.open("ratings_db") as db:
        # Initialize rating storage if not present
        if "ratings" not in db:
            db["ratings"] = {
                "bad": 0,
                "average": 0,
                "good": 0,
                "total_ratings": 0,
                "satisfied_count": 0,
                "rating_prompts": 0
            }

        ratings = db["ratings"]

        # Increment the respective rating count
        if rating in ["bad", "average", "good"]:
            ratings[rating] += 1
            ratings["total_ratings"] += 1  # Track total ratings

        # Update satisfied count (Average and Good are considered satisfied)
        if rating in ["average", "good"]:
            ratings["satisfied_count"] += 1

        db["ratings"] = ratings  # Save updated ratings


def increment_rating_prompt():
    """Tracks how many times users are prompted to rate."""
    with shelve.open("ratings_db", writeback=True) as db:
        if "ratings" not in db:
            db["ratings"] = {
                "bad": 0, "average": 0, "good": 0,
                "total_ratings": 0, "satisfied_count": 0,
                "rating_prompts": 0
            }

        db["ratings"]["rating_prompts"] += 1  # Increment prompt count


def get_statistics():
    """Returns total ratings, individual rating counts, satisfaction rate, and participation rate."""
    with shelve.open("ratings_db") as db:
        ratings = db.get("ratings", {
            "bad": 0, "average": 0, "good": 0, "total_ratings": 0,
            "satisfied_count": 0, "rating_prompts": 0
        })

        total_ratings = ratings["total_ratings"]
        satisfied_count = ratings["satisfied_count"]
        rating_prompts = ratings["rating_prompts"]

        # Calculate rates
        satisfaction_rate = (satisfied_count / total_ratings * 100) if total_ratings else 0
        participation_rate = (total_ratings / rating_prompts * 100) if rating_prompts else 0

        return {
            "bad": ratings["bad"],
            "average": ratings["average"],
            "good": ratings["good"],
            "total_ratings": total_ratings,
            "satisfaction_rate": satisfaction_rate,
            "participation_rate": participation_rate
        }


def get_next_id():
    """Find the lowest available ID or assign a new one."""
    with shelve.open(DATABASE, writeback=True) as db:
        contact_form_dict = db.get("ContactForms", {})
        available_ids = db.get("available_ids", set())

        if available_ids:
            next_id = min(available_ids)
            available_ids.remove(next_id)
        else:
            next_id = max(map(int, contact_form_dict.keys()), default=0) + 1

        db["available_ids"] = available_ids  # Save updated available IDs
    return next_id


@app.route('/support')
def support():
    return render_template('Support.html')


@app.route('/ContactUs', methods=['GET', 'POST'])
def contact_us():
    create_contact_form = CreateContactForm(request.form)
    if request.method == 'POST' and create_contact_form.validate():
        db = shelve.open(DATABASE, writeback=True)

        contact_form_dict = db.get("ContactForms", {})
        next_id = get_next_id()  # Get lowest available ID

        contact_form = ContactForm.ContactForm(
            create_contact_form.first_name.data,
            create_contact_form.last_name.data,
            create_contact_form.phone_number.data,
            create_contact_form.email.data,
            create_contact_form.message.data
        )

        contact_form.set_form_id(next_id)  # Assign the selected ID
        contact_form_dict[str(next_id)] = contact_form  # Store in dictionary
        db["ContactForms"] = contact_form_dict  # Save back to shelve

        db.close()

        return jsonify({'success': True, 'form_id': next_id})
    return render_template('ContactUs.html', form=create_contact_form)


@app.route('/retrieveContactForms')
def retrieve_contact_forms():
    with shelve.open(DATABASE) as db:
        contact_form_dict = db.get("ContactForms", {})

    # Convert dictionary values to a sorted list based on form ID
    contact_form_list = sorted(contact_form_dict.values(), key=lambda form: form.get_form_id())

    return render_template('retrieveContactForms.html', count=len(contact_form_list), contact_form_list=contact_form_list, active_page='retrieveContactForms')


@app.route('/viewContactForm/<int:id>')
def view_contact_form(id):
    with shelve.open(DATABASE) as db:
        contact_form_dict = db.get("ContactForms", {})
        contact_form = contact_form_dict.get(str(id))

        if not contact_form:
            return jsonify({"error": "Contact Form not found"}), 404

    return render_template('viewContactForm.html', contact_form=contact_form, active_page='retrieveContactForms')


@app.route('/updateContactForm/<int:id>/', methods=['GET', 'POST'])
def update_contact(id):
    update_contact_form = CreateContactForm(request.form)
    with shelve.open(DATABASE, writeback=True) as db:
        contact_form_dict = db.get("ContactForms", {})
        contact_form = contact_form_dict.get(str(id))

        if not contact_form:
            return jsonify({"error": "Contact Form not found"}), 404

        if request.method == 'POST' and update_contact_form.validate():
            contact_form.set_first_name(update_contact_form.first_name.data)
            contact_form.set_last_name(update_contact_form.last_name.data)
            contact_form.set_phone_number(update_contact_form.phone_number.data)
            contact_form.set_email(update_contact_form.email.data)
            contact_form.set_message(update_contact_form.message.data)

            db["ContactForms"] = contact_form_dict  # Save changes
            return redirect(url_for('retrieve_contact_forms'))

    # Pre-fill form fields for editing
    update_contact_form.first_name.data = contact_form.get_first_name()
    update_contact_form.last_name.data = contact_form.get_last_name()
    update_contact_form.phone_number.data = contact_form.get_phone_number()
    update_contact_form.email.data = contact_form.get_email()
    update_contact_form.message.data = contact_form.get_message()

    return render_template('updateContactForm.html', form=update_contact_form, active_page='retrieveContactForms')


@app.route('/deleteContactForm/<int:id>', methods=['POST'])
def delete_contact_form(id):
    with shelve.open(DATABASE, writeback=True) as db:
        contact_form_dict = db.get("ContactForms", {})
        available_ids = db.get("available_ids", set())

        if str(id) in contact_form_dict:
            del contact_form_dict[str(id)]  # Remove form
            available_ids.add(id)  # Mark ID as reusable
            db["ContactForms"] = contact_form_dict
            db["available_ids"] = available_ids  # Save available IDs
            return redirect(url_for('retrieve_contact_forms'))
        else:
            return jsonify({"error": "Form ID not found"}), 404


@app.route('/ChatBot')
def chatbot():
    return render_template('ChatBot.html')


@app.route('/get_response', methods=['POST'])
def get_response():
    user_message = request.form.get("message").lower()
    response = responses.get(user_message, responses["default"])
    return jsonify({"response": response})


@app.route("/submit_rating", methods=["POST"])
def submit_rating():
    rating = request.form.get("rating")

    if rating in ["bad", "average", "good"]:
        store_rating(rating)
        return jsonify(get_statistics())  # Return updated stats after storing

    return jsonify({"error": "Invalid rating"}), 400


@app.route("/prompt_rating", methods=["POST"])
def prompt_rating():
    increment_rating_prompt()
    with shelve.open("ratings_db") as db:
        rating_prompts = db["ratings"].get("rating_prompts", 0)

    return jsonify({"message": "Rating prompt recorded", "rating_prompts": rating_prompts})


@app.route('/ChatBotFeedback')
def chatbot_feedback():
    return render_template('ChatBotFeedback.html', active_page='ChatBotFeedback')


@app.route("/get_ChatBotStats")
def get_chatbot_stats():
    stats = get_statistics()  # Use your existing function
    return jsonify(stats)  # Send JSON response to frontend









if __name__ == '__main__':#ALWAYS PUT B4 THIS FUNC
    app.run(debug=True)

