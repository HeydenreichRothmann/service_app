from flask import Flask, render_template, request, redirect, url_for
import csv
from datetime import datetime

import os
from werkzeug.utils import secure_filename


app = Flask(__name__)


UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)




def read_cards():
    cards = []
    try:
        with open('cards.csv', mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                cards.append(row)
    except FileNotFoundError:
        with open('cards.csv', mode='w', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['name', 'description', 'image', 'location', 'date_logged', 'user', 'contact_details'])
    return cards

def write_card(data):
    with open('cards.csv', mode='a', encoding='utf-8', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['name', 'description', 'image', 'location', 'date_logged', 'user', 'contact_details'])
        writer.writerow(data)

def update_card(index, data):
    cards = read_cards()
    if 0 <= index < len(cards):
        cards[index] = data
        with open('cards.csv', mode='w', encoding='utf-8', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=['name', 'description', 'image', 'location', 'date_logged', 'user', 'contact_details'])
            writer.writeheader()
            writer.writerows(cards)

def delete_card(index):
    cards = read_cards()
    if 0 <= index < len(cards):
        del cards[index]
        with open('cards.csv', mode='w', encoding='utf-8', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=['name', 'description', 'image', 'location', 'date_logged', 'user', 'contact_details'])
            writer.writeheader()
            writer.writerows(cards)

@app.route('/')
def home():
    cards = read_cards()
    return render_template('home.html', cards=cards)

@app.route('/account')
def account():
    return render_template('account.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/socials')
def socials():
    return render_template('socials.html')

@app.route('/ai-post-generator')
def ai_post_generator():
    return render_template('ai_post_generator.html')

@app.route('/profile')
def profile():
    return render_template('profile.html')



@app.route('/create-card', methods=['GET', 'POST'])
def create_card():
    if request.method == 'POST':
        name = request.form['cardName']
        description = request.form['cardDescription']
        image_file = request.files.get('cardImage')
        location = request.form['cardLocation']
        user = request.form['cardUser']
        contact_details = request.form['cardContact']
        date_logged = datetime.now().strftime('%Y-%m-%d %H:%M')

        # Save image if provided
        image_filename = ''
        if image_file and image_file.filename != '':
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(image_path)
            image_filename = image_path  # Save relative path in CSV

        new_card = {
            'name': name,
            'description': description,
            'image': image_filename,
            'location': location,
            'date_logged': date_logged,
            'user': user,
            'contact_details': contact_details
        }

        write_card(new_card)
        return redirect(url_for('home'))

    return render_template('create_card.html')

@app.route('/edit-cards', methods=['GET', 'POST'])
def edit_cards():
    cards = read_cards()
    if request.method == 'POST':
        if 'edit_index' in request.form:
            index = int(request.form['edit_index'])
            if 0 <= index < len(cards):
                name = request.form.get(f'edit_name_{index}', cards[index]['name'])
                description = request.form.get(f'edit_description_{index}', cards[index]['description'])
                location = request.form.get(f'edit_location_{index}', cards[index]['location'])
                user = request.form.get(f'edit_user_{index}', cards[index]['user'])
                contact_details = request.form.get(f'edit_contact_{index}', cards[index]['contact_details'])
                updated_card = {
                    'name': name,
                    'description': description,
                    'image': cards[index]['image'],
                    'location': location,
                    'date_logged': cards[index]['date_logged'],
                    'user': user,
                    'contact_details': contact_details
                }
                update_card(index, updated_card)
        elif 'remove_index' in request.form:
            index = int(request.form['remove_index'])
            delete_card(index)
        return redirect(url_for('edit_cards'))

    return render_template('edit_cards.html', cards=cards)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)