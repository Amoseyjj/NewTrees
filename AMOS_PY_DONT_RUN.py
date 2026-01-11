from flask import Flask, render_template, request, redirect, url_for, jsonify
from Forms import CreateContactForm
import shelve
import ContactForm

app = Flask(__name__)
app.static_folder = 'static'
DATABASE = "contact.db"

# Hardcoded chatbot responses
responses = {
    "hi": "Hello! How can I help you today?",
    "hello": "Hey there! What do you need help with?",
    "buying": "Buying help: You can browse products in our Marketplace.",
    "selling": "Selling help: List your items under the Pre-Owned section.",
    "account": "Account help: You can update your profile in the settings.",
    "help": "I can help with Buying, Selling, and Account Management. Ask away!",
    "default": "Sorry, I didn’t understand that. Can you rephrase?",
    "i need help with a return": "Got it! Let’s sort out your return. Could you please provide your order number so I "
                                 "can assist you?",
    "sure, it's #123456789": "Would you like to return this item? If yes, can you tell me the reason? (e.g. defective, "
                             "change of mind, missing items, etc.)",
    "the item was defective": "Sorry to hear that! I’ll process your return request. Please pack the item securely and "
    "use the shipping label sent to your email. Once the item is received and inspected, your refund will be processed "
    "within 5 business days.",
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


@app.route('/')
def home():
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


if __name__ == '__main__':
    app.run()
