from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import csv
from datetime import datetime, timedelta
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this to a secure key in production
login_manager = LoginManager(app)
login_manager.login_view = 'login'

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Simple in-memory user store (replace with database later)
users = {'user1': {'password': 'pass123'}, 'user2': {'password': 'pass456'}}

class User(UserMixin):
    def __init__(self, username):
        self.id = username

@login_manager.user_loader
def load_user(username):
    if username in users:
        return User(username)

def read_cards():
    cards = []
    try:
        with open('cards.csv', mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                row['views'] = int(row.get('views', 0))
                cards.append(row)
    except FileNotFoundError:
        with open('cards.csv', mode='w', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['name', 'description', 'image', 'location', 'date_logged', 'user', 'contact_details', 'views'])
    return cards

def write_card(data):
    with open('cards.csv', mode='a', encoding='utf-8', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['name', 'description', 'image', 'location', 'date_logged', 'user', 'contact_details', 'views'])
        writer.writerow(data)

def update_card(index, data):
    cards = read_cards()
    if 0 <= index < len(cards):
        cards[index] = data
        with open('cards.csv', mode='w', encoding='utf-8', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=['name', 'description', 'image', 'location', 'date_logged', 'user', 'contact_details', 'views'])
            writer.writeheader()
            writer.writerows(cards)

def delete_card(index):
    cards = read_cards()
    if 0 <= index < len(cards):
        del cards[index]
        with open('cards.csv', mode='w', encoding='utf-8', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=['name', 'description', 'image', 'location', 'date_logged', 'user', 'contact_details', 'views'])
            writer.writeheader()
            writer.writerows(cards)

@app.route('/')
def home():
    cards = read_cards()
    return render_template('home.html', cards=cards)

@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    if request.method == 'POST':
        name = request.form.get('user_name')
        email = request.form.get('user_email')
        if name and email:
            session['user_info'] = {'name': name, 'email': email}
            flash('Account details saved successfully.', 'success')
        else:
            flash('Please fill in all fields.', 'error')
    user_info = session.get('user_info', {'name': '', 'email': ''})
    return render_template('account.html', user_info=user_info)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        name = request.form.get('user_name')
        email = request.form.get('user_email')
        bio = request.form.get('user_bio')
        phone = request.form.get('user_phone')
        if name and email:
            session['user_info'] = {'name': name, 'email': email, 'bio': bio, 'phone': phone}
            flash('Profile details saved successfully.', 'success')
        else:
            flash('Please fill in name and email fields.', 'error')
    user_info = session.get('user_info', {'name': '', 'email': '', 'bio': '', 'phone': ''})
    return render_template('profile.html', user_info=user_info)

@app.route('/dashboard')
@login_required
def dashboard():
    cards = read_cards()
    user_cards = [card for card in cards if card['user'] == current_user.id]
    
    # Calculate stats
    total_cards = len(user_cards)
    total_views = sum(int(card['views']) for card in user_cards)
    today = datetime.now().date().strftime('%Y-%m-%d')
    cards_today = sum(1 for card in user_cards if card['date_logged'].startswith(today))
    
    # Get recent cards (last 5, sorted by date descending)
    recent_cards = sorted(user_cards, key=lambda x: x['date_logged'], reverse=True)[:5]
    for i, card in enumerate(recent_cards):
        card['index'] = cards.index(card)
    
    # Prepare chart data
    # Views per day (last 7 days)
    dates = [(datetime.now().date() - timedelta(days=x)).strftime('%Y-%m-%d') for x in range(6, -1, -1)]
    views_per_day = {date: 0 for date in dates}
    for card in user_cards:
        date = card['date_logged'].split(' ')[0]
        if date in views_per_day:
            views_per_day[date] += int(card['views'])
    
    # Cards by location
    location_counts = {}
    for card in user_cards:
        loc = card['location'] or 'Unknown'
        location_counts[loc] = location_counts.get(loc, 0) + 1
    
    chart_data = {
        'views_per_day': {
            'labels': list(views_per_day.keys()),
            'data': list(views_per_day.values())
        },
        'cards_by_location': {
            'labels': list(location_counts.keys()),
            'data': list(location_counts.values())
        }
    }
    
    stats = {
        'total_cards': total_cards,
        'total_views': total_views,
        'cards_today': cards_today
    }
    
    user_name = session.get('user_info', {}).get('name', current_user.id)
    return render_template('dashboard.html', stats=stats, recent_cards=recent_cards, chart_data=chart_data, user_name=user_name)

@app.route('/socials')
def socials():
    return render_template('socials.html')

@app.route('/ai-post-generator')
def ai_post_generator():
    return render_template('ai_post_generator.html')

@app.route('/card/<int:index>')
def card_detail(index):
    cards = read_cards()
    if 0 <= index < len(cards):
        cards[index]['views'] = int(cards[index].get('views', 0)) + 1
        update_card(index, cards[index])
        return render_template('card_detail.html', card=cards[index])
    else:
        return "Card not found", 404

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username]['password'] == password:
            user = User(username)
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password.', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('home'))

@app.route('/create-card', methods=['GET', 'POST'])
@login_required
def create_card():
    if request.method == 'POST':
        name = request.form['cardName']
        description = request.form['cardDescription']
        image_file = request.files.get('cardImage')
        location = request.form['cardLocation']
        user = current_user.id
        contact_details = request.form['cardContact']
        date_logged = datetime.now().strftime('%Y-%m-%d %H:%M')

        image_filename = ''
        if image_file and image_file.filename != '':
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(image_path)
            image_filename = image_path

        new_card = {
            'name': name,
            'description': description,
            'image': image_filename,
            'location': location,
            'date_logged': date_logged,
            'user': user,
            'contact_details': contact_details,
            'views': 0
        }

        write_card(new_card)
        return redirect(url_for('home'))

    return render_template('create_card.html')

@app.route('/edit-cards', methods=['GET', 'POST'])
@login_required
def edit_cards():
    cards = read_cards()
    if request.method == 'POST':
        if 'edit_index' in request.form:
            index = int(request.form['edit_index'])
            if 0 <= index < len(cards) and cards[index]['user'] == current_user.id:
                name = request.form.get(f'edit_name_{index}', cards[index]['name'])
                description = request.form.get(f'edit_description_{index}', cards[index]['description'])
                location = request.form.get(f'edit_location_{index}', cards[index]['location'])
                contact_details = request.form.get(f'edit_contact_{index}', cards[index]['contact_details'])
                updated_card = {
                    'name': name,
                    'description': description,
                    'image': cards[index]['image'],
                    'location': location,
                    'date_logged': cards[index]['date_logged'],
                    'user': cards[index]['user'],
                    'contact_details': contact_details,
                    'views': cards[index]['views']
                }
                update_card(index, updated_card)
        elif 'remove_index' in request.form:
            index = int(request.form['remove_index'])
            if 0 <= index < len(cards) and cards[index]['user'] == current_user.id:
                delete_card(index)
        return redirect(url_for('edit_cards'))

    user_cards = [card for card in cards if card['user'] == current_user.id]
    return render_template('edit_cards.html', cards=user_cards)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)