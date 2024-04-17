import streamlit as st
import pandas as pd
import requests
from PIL import Image
from io import BytesIO
import zipfile
import os
import shutil

def download_and_save_image(image_url, sku):
    # Check if the URL is valid
    if not isinstance(image_url, str) or not (image_url.startswith('http://') or image_url.startswith('https://')):
        print(f"Skipping {sku}, invalid URL: {image_url}")
        return

    response = requests.get(image_url)
    if response.status_code == 200:
        img = Image.open(BytesIO(response.content))
        # Ensure the image is converted properly while maintaining transparency
        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
            # Convert images with transparency to 'RGBA' to ensure alpha is preserved
            img = img.convert('RGBA')
        else:
            # Convert non-transparent images to 'RGB'
            img = img.convert('RGB')
        
        if not os.path.exists('images'):
            os.makedirs('images')
        img.save(f"images/{sku}.webp", "webp")
    else:
        with st.expander(f"Details for {sku}"):
            st.write(f"Skipping {sku}, URL does not exist or is inaccessible.")
            
            
def save_images_to_zip(zip_filename, directory="images",  extension=".webp"):
    # Check if the directory exists
    if not os.path.exists(directory):
        print(f"The '{directory}' directory does not exist. No images to save.")
        return

    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith(extension):  # Look for files with the specified extension
                    rel_path = os.path.relpath(os.path.join(root, file), os.path.join(directory, '..'))
                    zipf.write(os.path.join(root, file), arcname=rel_path)
    print(f"Saved all {extension} images from '{directory}' to {zip_filename}")
    

def convert_images_to_jpeg_and_zip():
    if not os.path.exists('images'):
        print("The 'images' directory does not exist. No images to convert.")
        return
    
    if not os.path.exists('jpeg_images'):
        os.makedirs('jpeg_images')
    
    for root, dirs, files in os.walk('images'):
        for file in files:
            if file.endswith('.webp'):
                try:
                    image_path = os.path.join(root, file)
                    print(f"Processing {image_path}...")  # Print statement to verify processing
                    img = Image.open(image_path)
                    # Fill transparent areas with white before converting to 'RGB'
                    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        background.paste(img, mask=img.split()[3])  # 3 is the alpha channel
                        img = background
                    else:
                        img = img.convert('RGB')
                    jpeg_file_name = file.split('.')[0] + '.jpeg'  # Change the file extension to .jpeg
                    jpeg_path = os.path.join('jpeg_images', jpeg_file_name)
                    img.save(jpeg_path, 'JPEG', quality=95)
                    print(f"Saved {jpeg_path}")  # Print statement to confirm save
                except Exception as e:
                    print(f"Failed to convert {file}. Reason: {e}")
    
    save_images_to_zip("jpeg_images.zip", "jpeg_images", ".jpeg")
    print("Converted all .webp images to .jpeg and saved them to a ZIP file")

def clear_directory(directory):
        if os.path.exists(directory):
            for file in os.listdir(directory):
                file_path = os.path.join(directory, file)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f'Failed to delete {file_path}. Reason: {e}')

def main():
    st.title("Manhead Image Download and Renamer to SKUs")
    st.sidebar.markdown("<small>_Allows users to upload a CSV file containing image URLs and corresponding SKUs, downloads those images, converts them to WEBP and JPEG formats, and saves them in ZIP files for download._</small>", unsafe_allow_html=True)
    uploaded_file = st.sidebar.file_uploader("Choose a CSV file with Image_URL and SKU columns", type="csv")
    
    if uploaded_file is not None:
        download_button = st.sidebar.button("Download from Shopify")
        
        if download_button:
            clear_directory('images')  # Clear the images directory immediately after a new CSV is uploaded
            clear_directory('jpeg_images')
            try:
                df = pd.read_csv(uploaded_file)
                if "Image_URL" in df.columns and "SKU" in df.columns:
                    image_previews = []  # List to store image paths or PIL images
                    
                    total_images = len(df)
                    progress_text = st.empty()  # Placeholder for progress text
                    progress_bar = st.progress(0)  # Initialize the progress bar
                    
                    for index, row in enumerate(df.itertuples(), start=1):
                        download_and_save_image(row.Image_URL, row.SKU)
                        image_path = f"images/{row.SKU}.webp"
                        if os.path.exists(image_path):
                            image_previews.append(image_path)
                        progress = index / total_images  # Calculate progress
                        progress_bar.progress(progress)  # Update the progress bar
                        progress_text.text(f"Downloading images... {index}/{total_images} ({progress:.2%})")
                        
                    save_images_to_zip("images.zip")
                    convert_images_to_jpeg_and_zip()
                    save_images_to_zip("jpeg_images.zip", "jpeg_images", ".jpeg")
                    
                    st.success("Images downloaded, converted to WEBP and JPEG, and saved to ZIP files successfully!")
                    
                    columns = st.columns(4)  # Create 4 columns
                    for index, image_path in enumerate(image_previews):
                        with columns[index % 4]:  # Use modulo to loop through columns
                            st.image(image_path, caption=image_path.split('/')[-1], use_column_width=True)
                else:
                    st.error("CSV file must contain 'Image_URL' and 'SKU' columns")
            except Exception as e:
                st.error(f"An error occurred: {e}")
        
        # Provide download buttons for the WEBP and JPEG ZIP files outside the conditional block
        if os.path.exists("images.zip"):
            with open("images.zip", "rb") as fp:
                btn_webp = st.sidebar.download_button(
                    label="Download WEBP ZIP",
                    data=fp,
                    file_name="images.zip",
                    mime="application/zip"
                )
        
        if os.path.exists("jpeg_images.zip"):
            with open("jpeg_images.zip", "rb") as fp:
                btn_jpeg = st.sidebar.download_button(
                    label="Download JPEG ZIP",
                    data=fp,
                    file_name="jpeg_images.zip",
                    mime="application/zip"
                )
                
if __name__ == "__main__":
    main()