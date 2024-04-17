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
            
            
def save_images_to_zip(zip_filename, directory="images"):
    # Check if the directory exists
    if not os.path.exists(directory):
        print(f"The '{directory}' directory does not exist. No images to save.")
        return

    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        for root, dirs, files in os.walk(directory):
            for file in files:
                # Ensure this logic matches the files you intend to add (e.g., .jpeg for JPEG files)
                if file.endswith('.jpeg'):  # Adjusted to check for .jpeg files
                    rel_path = os.path.relpath(os.path.join(root, file), os.path.join(directory, '..'))
                    zipf.write(os.path.join(root, file), arcname=rel_path)
    print(f"Saved all images from '{directory}' to {zip_filename}")
    

def convert_images_to_jpeg():
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
                    jpeg_path = os.path.join('jpeg_images', file.replace('.webp', '.jpeg'))
                    img.save(jpeg_path, 'JPEG', quality=95)
                    print(f"Saved {jpeg_path}")  # Print statement to confirm save
                except Exception as e:
                    print(f"Failed to convert {file}. Reason: {e}")
    print("Converted all .webp images to .jpeg")

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
    uploaded_file = st.sidebar.file_uploader("Choose a CSV file with Image_URL and SKU columns", type="csv")
    
    if 'download_clicked' not in st.session_state:
        st.session_state.download_clicked = False
    
    if uploaded_file is not None:
        clear_directory('images')  # Clear the images directory immediately after a new CSV is uploaded
        try:
            df = pd.read_csv(uploaded_file)
            if "Image_URL" in df.columns and "SKU" in df.columns:
                image_previews = []  # List to store image paths or PIL images
                
                if st.sidebar.button("Download Images from Shopify and Convert to WEBP"):
                    for _, row in df.iterrows():
                        download_and_save_image(row['Image_URL'], row['SKU'])
                        image_path = f"images/{row['SKU']}.webp"
                        if os.path.exists(image_path):
                            image_previews.append(image_path)
                    save_images_to_zip("images.zip")
                    st.success("Images downloaded and saved successfully!")
                    st.session_state.download_clicked = True 
                    
                    
                    columns = st.columns(4)  # Create 4 columns
                    for index, image_path in enumerate(image_previews):
                        with columns[index % 4]:  # Use modulo to loop through columns
                            st.image(image_path, caption=image_path.split('/')[-1], use_column_width=True)# Display images in the main container
                    
                    # Provide a download button for the WEBP images ZIP
                    with open("images.zip", "rb") as fp:
                        st.sidebar.download_button(
                            label="Download WEBP ZIP",
                            data=fp,
                            file_name="images.zip",
                            mime="application/zip"
                        )
                if st.session_state.download_clicked:
                    if st.sidebar.button("Convert WEBP to JPEG"):
                        convert_images_to_jpeg()
                        save_images_to_zip("jpeg_images.zip", "jpeg_images")  # Save converted JPEG images to a ZIP
                        st.success("All .webp images converted to .jpeg successfully!")
                        # Provide a download button for the JPEG images ZIP
                        with open("jpeg_images.zip", "rb") as fp:
                            st.sidebar.download_button(
                                label="Download JPEG ZIP",
                                data=fp,
                                file_name="jpeg_images.zip",
                                mime="application/zip"
                            )

            else:
                st.error("CSV file must contain 'Image_URL' and 'SKU' columns")
        except Exception as e:
            st.error(f"An error occurred: {e}")
            
if __name__ == "__main__":
    main()
