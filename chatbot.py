# An example LLM chatbot using Cohere API and Streamlit that references a PDF
# Adapted from the StreamLit OpenAI Chatbot example - https://github.com/streamlit/llm-examples/blob/main/Chatbot.py

import streamlit as st
import cohere
import fitz # An alias for PyMuPDF
import os
import pandas as pd
import csv
from PIL import Image

csv_path = 'docs/cosmetics.csv'
# Handle PDF or CSV 
def documents_from_file(file_path):

    ext = os.path.splitext(file_path)[1]

    if ext == '.pdf':  
        return pdf_to_documents(file_path) 
    elif ext == '.csv':
        return csv_to_documents(file_path)

    
# New CSV function   
# New CSV function   
def csv_to_documents(csv_path):

  documents = []

  with open(csv_path) as f:
    reader = csv.DictReader(f)

    for row in reader:

      document = {
        "product_name": row["Name"],
        "product_brand": row["Brand"],
        "product_price": row["Price"],
        "product_rank": row["Rank"],
        "product_ingredients": row["Ingredients"],
        "product_combination": row["Combination"], 
        "product_dry": row["Dry"],
        "product_normal": row["Normal"],
        "product_oily": row["Oily"],
        "product_sensitive": row["Sensitive"],
        "snippet": row["Name"] + " " + row["Brand"] 
      }

      documents.append(document)
      
  return documents


def pdf_to_documents(pdf_path):
    """
    Converts a PDF to a list of 'documents' which are chunks of a larger document that can be easily searched 
    and processed by the Cohere LLM. Each 'document' chunk is a dictionary with a 'title' and 'snippet' key
    
    Args:
        pdf_path (str): The path to the PDF file.
    
    Returns:
        list: A list of dictionaries representing the documents. Each dictionary has a 'title' and 'snippet' key.
        Example return value: [{"title": "Page 1 Section 1", "snippet": "Text snippet..."}, ...]
    """

    doc = fitz.open(pdf_path)
    documents = []
    text = ""
    chunk_size = 1000
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text()
        part_num = 1
        for i in range(0, len(text), chunk_size):
            documents.append({"title": f"Page {page_num + 1} Part {part_num}", "snippet": text[i:i + chunk_size]})
            part_num += 1
    return documents

# Add a sidebar to the Streamlit app
with st.sidebar:
    if hasattr(st, "secrets"):
        cohere_api_key = st.secrets["COHERE_API_KEY"]
        # st.write("API key found.")
    else:
        cohere_api_key = st.text_input("Cohere API Key", key="chatbot_api_key", type="password")
        st.markdown("[Get a Cohere API Key](https://dashboard.cohere.ai/api-keys)")
    
    skin_type = st.selectbox('Select your skin type',
    ['Oily','Dry','Normal','Combination','Sensitive'])

    skin_concern = st.multiselect(
    "What is your skin concern?",
    ["Acne", "Fungal Acne", "Fine Lines", "Wrinkles", "Redness", "Rosacea", "Sensitivity", "Eczema", "Dryness","Dark Spots", "Oilliness", "Pores", "Dullness", "Texture"],
    ["Acne"])

    product_specify = st.multiselect(
    "What do you look for in a skincare product?",
    ["Vegan", "Cruelty Free", "Fungal Acne Safe", "Fragrance Free", "EU Allergen Free", "Alcohol Free", "Reef Safe", "Silicon Free", "Sulfate Free","Oil Free", "Paraben Free"],
    ["Vegan"])

    price_range = st.slider(
    "Select the price range in pounds",
    0.0, 300.0, (0.0, 100.0))


    # st.write(f"Selected document: {selected_doc}")

# Set the title of the Streamlit app

#image_path = "Icon.png"
#image = Image.open(image_path)
#image = image.resize((75, 75))
#st.image(image)

st.title("SkinCare Bot")

st.info(
    "This Chatbot uses a CSV file to provide skincare recommendations."
    "Check if the reponse is accurate at [CSV File](https://www.kaggle.com/datasets/kingabzpro/cosmetics-datasets).",
    icon="📃",
)


# Initialize the chat history with a greeting message
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "text": "Hi, I'm SkinBot! How can I help you today?"}]

# Display the chat messages
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["text"])

# Get user input
if prompt := st.chat_input():
    # Stop responding if the user has not added the Cohere API key
    if not cohere_api_key:
        st.info("Please add your Cohere API key to continue.")
        st.stop()

    # Create a connection to the Cohere API
    client = cohere.Client(api_key=cohere_api_key)
    
    # Display the user message in the chat window
    st.chat_message("user").write(prompt)

    preamble = f"""You are the a SkinBot apprentice. You have been tasked with answering questions and give skincare recommendations.
    Be concise with your response and provide the best possible answer. 
    The user definitely has {skin_type} skin type. Their skin concernis {skin_concern}. They would like their product to be {product_specify}. The price range is between {price_range[0]} and {price_range[1]}.
    The price is in pounds
    Use {skin_type} skin type, {skin_concern}, {product_specify} and price range to provide a recommendation.
    If they ask about their own skin, get it from the user and provide a recommendation in great detail. Explain your reasoning. """

    # Send the user message and pdf text to the model and capture the response
    response = client.chat(chat_history=st.session_state.messages,
                           message=prompt,
                           documents=documents_from_file(csv_path),
                           prompt_truncation='AUTO',
                           preamble=preamble,)
    
    # Add the user prompt to the chat history
    st.session_state.messages.append({"role": "user", "text": prompt})
    
    # Add the response to the chat history
    msg = response.text
    st.session_state.messages.append({"role": "assistant", "text": msg})

    # Write the response to the chat window
    st.chat_message("assistant").write(msg)
