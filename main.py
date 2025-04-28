import pymongo
from pymongo import MongoClient
import nltk
from nltk.stem import SnowballStemmer
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import string
import re
import numpy as np

# Download required NLTK resources
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['government_schemes']
schemes_collection = db['schemes']
clustered_collection = db['clustered_schemes']

# Sample data - 50 Indian government schemes (10 shown as example)
schemes_data = [
    {
        "name": "Pradhan Mantri Jan Dhan Yojana",
        "description": "Financial inclusion program. Provides bank accounts to all. Includes accident insurance. Overdraft facility available. No minimum balance required.",
        "link": "https://pmjdy.gov.in"
    },
    {
        "name": "Ayushman Bharat Yojana",
        "description": "Health insurance scheme. Covers hospitalization expenses. For poor and vulnerable families. Cashless treatment available. Covers pre-existing conditions.",
        "link": "https://abnhpm.gov.in"
    },
    {
        "name": "Stand Up India Scheme",
        "description": "Promotes entrepreneurship among women. Provides bank loans. For SC/ST and women entrepreneurs. Loan range 10 lakh to 1 crore. Supports greenfield projects.",
        "link": "https://www.standupmitra.in"
    },
    {
        "name": "Pradhan Mantri Mudra Yojana",
        "description": "Provides loans to small businesses. Three categories of loans available. Supports non-farm income activities. Collateral-free loans. For micro enterprises.",
        "link": "https://www.mudra.org.in"
    },
    {
        "name": "Pradhan Mantri Kisan Samman Nidhi",
        "description": "Income support scheme for farmers. Provides Rs. 6000 per year. Paid in three installments. For landholding farmer families. Direct benefit transfer.",
        "link": "https://pmkisan.gov.in"
    },
    {
        "name": "Pradhan Mantri Ujjwala Yojana",
        "description": "Provides LPG connections to women. For below poverty line families. Reduces health hazards. Empowers women beneficiaries. Subsidy on refills available.",
        "link": "https://pmuy.gov.in"
    },
    {
        "name": "Atal Pension Yojana",
        "description": "Pension scheme for unorganized sector. Guaranteed pension after 60. Contribution based on chosen pension. Government co-contribution for some. Auto-debit facility available.",
        "link": "https://www.jansuraksha.gov.in"
    },
    {
        "name": "Pradhan Mantri Awas Yojana",
        "description": "Housing for all scheme. Provides affordable housing. Interest subsidy available. For urban and rural areas. Targets completion by 2024.",
        "link": "https://pmaymis.gov.in"
    },
    {
        "name": "Sukanya Samriddhi Yojana",
        "description": "Savings scheme for girl child. Higher interest rate. Tax benefits available. Can be opened till age 10. Matures when girl turns 21.",
        "link": "https://www.indiapost.gov.in"
    },
    {
        "name": "Pradhan Mantri Fasal Bima Yojana",
        "description": "Crop insurance scheme. Protects against yield losses. Affordable premium rates. Covers pre-sowing to post-harvest. Uses technology for assessment.",
        "link": "https://pmfby.gov.in"
    }
    # Add 40 more schemes here...
]

# Insert sample data if collection is empty
if schemes_collection.count_documents({}) == 0:
    schemes_collection.insert_many(schemes_data)

# Text preprocessing
stemmer = SnowballStemmer("english")
stop_words = set(stopwords.words('english'))

def preprocess_text(text):
    if not isinstance(text, str):
        return ""
    
    # Lowercase
    text = text.lower()
    # Remove punctuation
    text = text.translate(str.maketrans('', '', string.punctuation))
    # Remove numbers
    text = re.sub(r'\d+', '', text)
    # Tokenize
    try:
        tokens = nltk.word_tokenize(text)
    except:
        tokens = text.split()
    # Remove stopwords and stem
    tokens = [stemmer.stem(word) for word in tokens if word not in stop_words and len(word) > 2]
    return ' '.join(tokens)

# Get all schemes from MongoDB
schemes = list(schemes_collection.find({}))
descriptions = [scheme.get('description', '') for scheme in schemes]

# Preprocess descriptions
processed_descriptions = []
for desc in descriptions:
    try:
        processed = preprocess_text(desc)
        processed_descriptions.append(processed)
    except Exception as e:
        print(f"Error processing description: {e}")
        processed_descriptions.append("")

# Vectorize text using TF-IDF
try:
    vectorizer = TfidfVectorizer(max_features=1000)
    X = vectorizer.fit_transform(processed_descriptions)
except ValueError as e:
    print(f"Error in vectorization: {e}")
    vectorizer = TfidfVectorizer(max_features=1000, tokenizer=lambda x: x.split())
    X = vectorizer.fit_transform(processed_descriptions)

# Determine optimal clusters using Elbow method
def find_optimal_clusters(data, max_k=10):
    if data.shape[0] < 2:  # Check number of rows instead of len()
        return 1
    
    max_k = min(max_k, data.shape[0] - 1)  # Ensure max_k is valid
    wcss = []
    for k in range(1, max_k + 1):
        kmeans = KMeans(n_clusters=k, random_state=42)
        kmeans.fit(data)
        wcss.append(kmeans.inertia_)
    
    if len(wcss) < 2:
        return 1
    
    differences = [wcss[i] - wcss[i+1] for i in range(len(wcss)-1)]
    optimal_k = differences.index(max(differences)) + 1 if differences else 1
    return optimal_k

optimal_clusters = find_optimal_clusters(X)
optimal_clusters = max(1, min(optimal_clusters, 10))  # Ensure between 1-10

# Perform K-means clustering
try:
    kmeans = KMeans(n_clusters=optimal_clusters, random_state=42)
    clusters = kmeans.fit_predict(X)
except Exception as e:
    print(f"Clustering error: {e}")
    clusters = [0] * len(schemes)

# Get cluster labels and top terms
def get_top_terms_per_cluster(vectorizer, kmeans, n_terms=5):
    terms = vectorizer.get_feature_names_out()
    top_terms = {}
    for i in range(kmeans.n_clusters):
        centroid = kmeans.cluster_centers_[i]
        top_indices = centroid.argsort()[-n_terms:][::-1]
        top_terms[i] = [terms[index] for index in top_indices]
    return top_terms

try:
    top_terms = get_top_terms_per_cluster(vectorizer, kmeans)
except:
    top_terms = {i: ["cluster"+str(i)] for i in range(optimal_clusters)}

# Prepare data for MongoDB
cluster_results = []
for i, scheme in enumerate(schemes):
    cluster_results.append({
        "scheme_id": scheme["_id"],
        "name": scheme["name"],
        "description": scheme["description"],
        "link": scheme["link"],
        "cluster": int(clusters[i]) if i < len(clusters) else 0,
        "cluster_terms": top_terms.get(clusters[i], []) if i < len(clusters) else [],
        "cluster_label": " ".join(top_terms.get(clusters[i], ["cluster"+str(clusters[i])])[:2]).title() if i < len(clusters) else "General"
    })

# Store clustered data in MongoDB
try:
    if clustered_collection.count_documents({}) > 0:
        clustered_collection.drop()
    clustered_collection.insert_many(cluster_results)
    print(f"Successfully clustered {len(schemes)} schemes into {optimal_clusters} clusters")
    print("Cluster labels and top terms:")
    for cluster_id, terms in top_terms.items():
        print(f"Cluster {cluster_id}: {', '.join(terms)}")
except Exception as e:
    print(f"Error storing results in MongoDB: {e}")

# Example query function
def get_schemes_by_cluster(cluster_id):
    try:
        return list(clustered_collection.find({"cluster": cluster_id}))
    except:
        return []

# Example usage
if __name__ == "__main__":
    print("\nSample schemes from first cluster:")
    for scheme in get_schemes_by_cluster(0)[:3]:
        print(f"{scheme['name']} - {scheme.get('cluster_label', 'General')}")