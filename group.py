import os
import string 
import json 
import gensim.downloader
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from scipy.cluster.hierarchy import linkage, dendrogram
import matplotlib.pyplot as plt 

LINKAGE_MATRIX_PATH = 'linkage_matrix.npy'
CORP_DATA_PATH = 'corp_data.json'
word2vec_model = gensim.downloader.load('word2vec-google-news-300')

with open(CORP_DATA_PATH, 'r') as f:
    CORP_DATA = json.load(f)


def text_preprocess(corporate):
    text_data = ' '.join([
        corporate['name'],
        corporate['description'],
        ' '.join([(theme[0] + ' ') * int(theme[1]) for theme in corporate['startup_themes'] if theme[0] != 'Other'])

    ])
    text_data = text_data.lower().split()

    return text_data

def get_embedding(words):
    valid_words = [word for word in words if word in word2vec_model]

    if not valid_words:
        return np.zeros(word2vec_model.vector_size)
    
    embedding = np.mean(word2vec_model[valid_words], axis=0)
    return embedding

def get_sim_matrix():

    embeddings_matrix = [get_embedding(text_preprocess(corp)) for corp in CORP_DATA]
    embeddings_matrix = np.array(embeddings_matrix)
    epsilon = 1e-8
    similarity_matrix = cosine_similarity(embeddings_matrix + epsilon)
    return similarity_matrix

def write_and_return_linkage_matrix():
    similarity_matrix = get_sim_matrix()
    
    linkage_matrix = linkage(similarity_matrix, method='average', metric='cosine')
    np.save('linkage_matrix.npy', linkage_matrix)
    return linkage_matrix

def write_results():

    if os.path.exists(LINKAGE_MATRIX_PATH): 
        linkage_matrix = np.load(LINKAGE_MATRIX_PATH)
    else: 
        linkage_matrix = write_and_return_linkage_matrix()
    
    threshold = 0.8

    dendrogram(linkage_matrix, color_threshold=threshold, orientation='top', leaf_rotation=90)
    plt.title('Hierarchical Clustering Dendrogram')
    plt.xlabel('Companies')
    plt.ylabel('Distance')
    plt.show()
    
write_results()