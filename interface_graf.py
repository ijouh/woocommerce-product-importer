import csv
import os
import cloudinary
import cloudinary.uploader

# Config Cloudinary
cloudinary.config(
    cloud_name='djzgf1wnn',
    api_key='723947715643454',
    api_secret='l4za9y4VaspnjEyyLFNhvrkNKhU'
)

def upload_image_to_cloudinary(filepath, public_id=None):
    response = cloudinary.uploader.upload(
        filepath,
        public_id=public_id,
        overwrite=True
    )
    return response['secure_url']

def update_csv_with_cloudinary_urls(input_csv_path, output_csv_path, images_base_folder):
    with open(input_csv_path, newline='', encoding='utf-8') as infile, \
         open(output_csv_path, 'w', newline='', encoding='utf-8') as outfile:

        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            local_image_path = os.path.join(images_base_folder, row['image'])
            # Optionnel: crée un nom logique à partir du nom produit ou image
            public_id = os.path.splitext(os.path.basename(row['image']))[0].replace(' ', '-').lower()
            try:
                print(f"Upload image {local_image_path} sur Cloudinary...")
                cloud_url = upload_image_to_cloudinary(local_image_path, public_id)
                print(f"Image uploadée: {cloud_url}")
                row['image'] = cloud_url  # Remplace chemin local par URL cloudinary
            except Exception as e:
                print(f"Erreur upload image {local_image_path} : {e}")
                # Tu peux décider de garder le chemin local si erreur ou mettre vide
                row['image'] = ""

            writer.writerow(row)

if __name__ == "__main__":
    # chemin vers ton CSV avec chemins locaux d'images
    input_csv = 'produits_local.csv'
    # chemin pour sauver CSV avec URLs Cloudinary
    output_csv = 'produits_cloudinary.csv'
    # dossier local où sont les images référencées dans CSV
    images_folder = 'images'

    update_csv_with_cloudinary_urls(input_csv, output_csv, images_folder)
