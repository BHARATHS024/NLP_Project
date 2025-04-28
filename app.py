# backend/app.py
from flask import Flask, request, jsonify, render_template
from flask_mysqldb import MySQL
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import re
import json
import pickle
import os
from datetime import datetime

app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static')

# Configuration
app.config.from_pyfile('config.py')

mysql = MySQL(app)

# Initialize NLP components
nltk.download('stopwords')
nltk.download('wordnet')
stop_words = set(stopwords.words('english'))
lemmatizer = WordNetLemmatizer()

# Model paths
MODEL_DIR = os.path.join(os.path.dirname(__file__), 'nlp_model')
os.makedirs(MODEL_DIR, exist_ok=True)
VECTORIZER_PATH = os.path.join(MODEL_DIR, 'vectorizer.pkl')
KMEANS_PATH = os.path.join(MODEL_DIR, 'kmeans_model.pkl')

# Initialize or load models
if os.path.exists(VECTORIZER_PATH) and os.path.exists(KMEANS_PATH):
    with open(VECTORIZER_PATH, 'rb') as f:
        vectorizer = pickle.load(f)
    with open(KMEANS_PATH, 'rb') as f:
        kmeans = pickle.load(f)
else:
    vectorizer = TfidfVectorizer(max_features=1000)
    kmeans = KMeans(n_clusters=10, random_state=42)

def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    words = text.split()
    words = [lemmatizer.lemmatize(word) for word in words if word not in stop_words]
    return ' '.join(words)

def save_models():
    with open(VECTORIZER_PATH, 'wb') as f:
        pickle.dump(vectorizer, f)
    with open(KMEANS_PATH, 'wb') as f:
        pickle.dump(kmeans, f)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/schemes')
def schemes():
    return render_template('schemes.html')

@app.route('/notifications')
def notifications():
    return render_template('notifications.html')

@app.route('/api/schemes', methods=['GET', 'POST'])
def handle_schemes():
    if request.method == 'POST':
        data = request.json
        title = data['title']
        description = data['description']
        raw_text = f"{title} {description}"
        
        processed_text = preprocess_text(raw_text)
        vectorized = vectorizer.transform([processed_text])
        cluster = kmeans.predict(vectorized)[0]
        
        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO schemes 
            (title, description, raw_text, vectorized_data, category, publish_date) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (title, description, raw_text, json.dumps(vectorized.toarray().tolist()), 
              f"Category_{cluster}", datetime.now()))
        mysql.connection.commit()
        cur.close()
        
        return jsonify({"message": "Scheme added successfully", "category": f"Category_{cluster}"})
    
    else:  # GET
        category = request.args.get('category')
        cur = mysql.connection.cursor()
        
        if category:
            cur.execute("SELECT * FROM schemes WHERE category = %s", (category,))
        else:
            cur.execute("SELECT * FROM schemes")
            
        schemes = cur.fetchall()
        cur.close()
        
        scheme_list = []
        for scheme in schemes:
            scheme_list.append({
                'id': scheme[0],
                'title': scheme[1],
                'description': scheme[2],
                'category': scheme[4],
                'publish_date': scheme[8].strftime('%Y-%m-%d') if scheme[8] else None
            })
        
        return jsonify(scheme_list)

@app.route('/api/train-model', methods=['POST'])
def train_model():
    cur = mysql.connection.cursor()
    cur.execute("SELECT raw_text FROM schemes")
    texts = [row[0] for row in cur.fetchall()]
    cur.close()
    
    if len(texts) < 2:
        return jsonify({"error": "Need at least 2 schemes to train"}), 400
    
    processed_texts = [preprocess_text(text) for text in texts]
    vectorized = vectorizer.fit_transform(processed_texts)
    kmeans.fit(vectorized)
    save_models()
    
    cur = mysql.connection.cursor()
    for i, text in enumerate(texts):
        cluster = kmeans.predict(vectorized[i])[0]
        cur.execute("UPDATE schemes SET category = %s WHERE raw_text = %s", 
                   (f"Category_{cluster}", text))
    mysql.connection.commit()
    cur.close()
    
    return jsonify({"message": f"Model trained successfully on {len(texts)} schemes"})

@app.route('/api/notifications', methods=['GET'])
def get_notifications():
    # In a real app, you would filter by user ID
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT n.notification_id, s.title, s.description, s.category 
        FROM notifications n
        JOIN schemes s ON n.scheme_id = s.scheme_id
        ORDER BY n.notified_at DESC
        LIMIT 10
    """)
    notifications = cur.fetchall()
    cur.close()
    
    notification_list = []
    for note in notifications:
        notification_list.append({
            'id': note[0],
            'title': note[1],
            'description': note[2],
            'category': note[3]
        })
    
    return jsonify(notification_list)

if __name__ == '__main__':
    app.run(debug=True)