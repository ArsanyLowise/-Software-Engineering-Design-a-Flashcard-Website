from flask import Flask, jsonify, render_template, request, redirect, url_for, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from bson import ObjectId
import json
from pymongo import MongoClient
import random

app = Flask(__name__)
app.secret_key = 'your_secret_key'
login_manager = LoginManager(app)
bcrypt = Bcrypt(app)

# Redirect to login page if not authenticated
login_manager.login_view = 'login'

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['flashcard_db']
flashcards_collection = db['flashcards']
users_collection = db['users']

@login_manager.user_loader
def load_user(user_id):
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if user:
        return User(user['_id'], user['username'], user['password'])
    return None

class User(UserMixin):
    def __init__(self, user_id, username, password):
        self.id = user_id
        self.username = username
        self.password = password

def serialize_mongo_document(document):
    """
    Convert a MongoDB document to a JSON-serializable format.
    """
    if isinstance(document, ObjectId):
        return str(document)
    if isinstance(document, list):
        return [serialize_mongo_document(doc) for doc in document]
    if isinstance(document, dict):
        return {k: serialize_mongo_document(v) for k, v in document.items()}
    return document

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/index')
@login_required
def index():
    if 'flashcards' not in session or 'current_index' not in session:
        initialize_session()
    current_index = session['current_index']
    flashcard = session['flashcards'][current_index]
    return render_template('index.ejs', flashcard=flashcard, total=len(session['flashcards']), current=current_index + 1)

@app.route('/next_flashcard')
@login_required
def next_flashcard():
    if 'flashcards' not in session or 'current_index' not in session:
        initialize_session()
    session['current_index'] = (session['current_index'] + 1) % len(session['flashcards'])
    return redirect(url_for('index'))

def initialize_session():
    session['current_index'] = 0
    session['flashcards'] = [serialize_mongo_document(flashcard) for flashcard in flashcards_collection.find()]
    random.shuffle(session['flashcards'])

@app.route('/check_answer', methods=['POST'])
@login_required
def check_answer():
    card_id = request.form.get('card_id')
    selected_option = request.form.get('option')
    flashcard = flashcards_collection.find_one({"_id": ObjectId(card_id)})
    
    if flashcard:
        correct_answer = flashcard['Correct Answer']
        is_correct = (selected_option == correct_answer)
        return jsonify({'is_correct': is_correct, 'correct_answer': correct_answer, 'selected_option': selected_option})
    return jsonify({'error': 'Flashcard not found'}), 404

@app.route('/show_correct_answer', methods=['POST'])
@login_required
def show_correct_answer():
    card_id = request.form.get('card_id')
    flashcard = flashcards_collection.find_one({"_id": ObjectId(card_id)})
    
    if flashcard:
        correct_answer = flashcard['Correct Answer']
        return jsonify({'correct_answer': correct_answer})
    return jsonify({'error': 'Flashcard not found'}), 404

@app.route('/add_flashcard', methods=['GET', 'POST'])
@login_required
def add_flashcard():
    if request.method == 'POST':
        question = request.form.get('question')
        choice1 = request.form.get('choice1')
        choice2 = request.form.get('choice2')
        choice3 = request.form.get('choice3')
        choice4 = request.form.get('choice4')
        correct_answer = request.form.get('correct_answer')
        category = request.form.get('category')
        
        print("Form data received:")
        print(f"Question: {question}")
        print(f"Choice1: {choice1}")
        print(f"Choice2: {choice2}")
        print(f"Choice3: {choice3}")
        print(f"Choice4: {choice4}")
        print(f"Correct Answer: {correct_answer}")
        print(f"Category: {category}")
        
        if question and choice1 and choice2 and choice3 and choice4 and correct_answer:
            flashcard = {
                'Question': question,
                'Choice1': choice1,
                'Choice2': choice2,
                'Choice3': choice3,
                'Choice4': choice4,
                'Correct Answer': correct_answer,
                'Category': category
            }
            flashcards_collection.insert_one(flashcard)
            return redirect(url_for('index'))
        else:
            return "Missing question or answer", 400
    return render_template('add_flashcard.ejs')

@app.route('/api/flashcards', methods=['GET'])
def get_flashcards():
    flashcards = list(flashcards_collection.find())
    flashcards_serialized = [serialize_mongo_document(flashcard) for flashcard in flashcards]
    return jsonify(flashcards_serialized)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users_collection.find_one({"username": username})
        if user and bcrypt.check_password_hash(user['password'], password):
            user_obj = User(user['_id'], user['username'], user['password'])
            login_user(user_obj)
            initialize_session()
            return redirect(url_for('index'))
        return 'Invalid username or password'
    return render_template('login.ejs')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('current_index', None)
    session.pop('flashcards', None)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        users_collection.insert_one({'username': username, 'password': hashed_password})
        return redirect(url_for('login'))
    return render_template('register.ejs')

@app.route('/static-page')
def static_page():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5001)  
