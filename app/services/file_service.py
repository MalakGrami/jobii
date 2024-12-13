import asyncio
from transformers import AutoTokenizer, AutoModel
from sklearn.metrics.pairwise import cosine_similarity
import torch
import numpy as np
import re
import nltk
from nltk.corpus import stopwords
import fitz  

# Download NLTK stopwords
nltk.download('stopwords')

# Function to extract text from a PDF CV
def extract_pdf_text(pdf_path, max_pages=10):
    try:
        pdf_document = fitz.open(pdf_path)
        text = "" 
        for page_num in range(min(pdf_document.page_count, max_pages)):
            page = pdf_document.load_page(page_num)
            text += page.get_text()
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""