import streamlit as st
import pandas as pd
import requests
from PIL import Image
from io import BytesIO
import zipfile
import os

def download_and_save_image(image_url, sku):
    # Check if the URL is valid
    if not isinstance(image_url, str) or not (image_url.startswith('http://') or image_url.startswith('https://')):
        print(f"Skipping {sku}, invalid URL: {image_url}")
        return

    response = requests.get(image_url)
    if response.status_code == 200:
        img = Image.open(BytesIO(response.content))
        if img.mode != 'RGB':
            img = img.convert('RGB')
        if not os.path.exists('images'):
            os.makedirs('images')
        # Remove the redundant line where the image is opened again
        img.save(f"images/{sku}.jpeg", "JPEG")  # Also ensure the image is saved in the 'images' directory
    else:
        with st.expander(f"Details for {sku}"):
            st.write(f"Skipping {sku}, URL does not exist or is inaccessible.")
        
        
def save_images_to_zip(zip_filename="images.zip"):
    # Check if the 'images' directory exists
    if not os.path.exists('images'):
        print("The 'images' directory does not exist. No images to save.")
        return

    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        for root, dirs, files in os.walk('images'):
            for file in files:
                if file.endswith('.jpeg'):
                    # Calculate relative path to keep directory structure within the ZIP
                    rel_path = os.path.relpath(os.path.join(root, file), os.path.join('images', '..'))
                    zipf.write(os.path.join(root, file), arcname=rel_path)
    print(f"Saved all images to {zip_filename}")
            
def main():
    st.title("Manhead Image Download and Renamer to SKUs")
    uploaded_file = st.sidebar.file_uploader("Choose a CSV file with Image_URL and SKU columns", type="csv")
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            if "Image_URL" in df.columns and "SKU" in df.columns:
                if st.button("Download Images"):
                    for _, row in df.iterrows():
                        download_and_save_image(row['Image_URL'], row['SKU'])
                    # Assuming your images are saved in the 'images' directory and you call save_images_to_zip here
                    save_images_to_zip("images.zip")
                    st.success("Images downloaded and saved successfully!")
                    
                    # Provide a download button for the ZIP file
                    with open("images.zip", "rb") as fp:
                        btn = st.download_button(
                            label="Download ZIP",
                            data=fp,
                            file_name="images.zip",
                            mime="application/zip"
                        )
            else:
                st.error("CSV file must contain 'Image_URL' and 'SKU' columns")
        except Exception as e:
            st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
