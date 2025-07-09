import csv
import os
import io
import cloudinary
import cloudinary.uploader
from flask import Flask, render_template_string, request, redirect, flash
from woocommerce import API
import tempfile

# Config Cloudinary
cloudinary.config(
    cloud_name='djzgf1wnn',
    api_key='723947715643454',
    api_secret='l4za9y4VaspnjEyyLFNhvrkNKhU'
)

# Config WooCommerce
wcapi = API(
    url="http://ijouhwebsite.kesug.com/",
    consumer_key="ck_7281fc1e96cf927bfd3fcbf4068745bc0e751334",
    consumer_secret="cs_bdb18f7ec5df7d56aaa309cb6cded35a8b3347c0",
    version="wc/v3",
    timeout=120
)

app = Flask(__name__)
app.secret_key = 'change_this_secret'

HTML = """
<!doctype html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Import Produits WooCommerce avec Cloudinary</title>
  <style>
    body { font-family: Arial, sans-serif; background: #f5f7fa; margin: 40px auto; max-width: 700px; padding: 20px; color: #333; }
    h1 { color: #007acc; text-align: center; margin-bottom: 30px; }
    form { background: #fff; padding: 25px; border-radius: 8px; box-shadow: 0 3px 10px rgba(0,0,0,0.1); display: flex; flex-direction: column; gap: 15px; align-items: center; }
    input[type="file"] { padding: 8px; border: 1px solid #ccc; border-radius: 5px; width: 100%; max-width: 400px; }
    input[type="submit"] { background-color: #007acc; color: white; border: none; padding: 12px 30px; font-size: 16px; border-radius: 6px; cursor: pointer; transition: background-color 0.3s ease; }
    input[type="submit"]:hover { background-color: #005f99; }
    ul { background: #ffe6e6; border: 1px solid #ff4d4d; padding: 10px 20px; border-radius: 6px; list-style-type: none; max-width: 700px; margin: 20px auto; color: #a10000; }
    pre { background: #eef3f7; padding: 20px; border-radius: 8px; max-height: 400px; overflow-y: auto; white-space: pre-wrap; word-wrap: break-word; box-shadow: inset 0 0 5px #ccc; max-width: 700px; margin: 20px auto; }
  </style>
</head>
<body>
  <h1>Importer un fichier CSV (images locales uploadées sur Cloudinary)</h1>
  <form method="POST" enctype="multipart/form-data">
    <input type="file" name="csv_file" accept=".csv" required>
    <input type="submit" value="Importer">
  </form>

  {% with messages = get_flashed_messages() %}
    {% if messages %}
      <ul>
      {% for message in messages %}
        <li>{{ message }}</li>
      {% endfor %}
      </ul>
    {% endif %}
  {% endwith %}

  {% if logs %}
  <h2>Logs :</h2>
  <pre>{{ logs }}</pre>
  {% endif %}
</body>
</html>
"""

def upload_image_to_cloudinary(filepath, public_id=None):
    response = cloudinary.uploader.upload(
        filepath,
        public_id=public_id,
        overwrite=True
    )
    return response['secure_url']

def process_csv_and_import_products(file_storage):
    logs = []
    try:
        # Lire le CSV uploadé en mémoire
        decoded = io.StringIO(file_storage.read().decode('utf-8'))
        reader = csv.DictReader(decoded)
        fieldnames = reader.fieldnames

        # Stockage temporaire du CSV modifié (avec URLs Cloudinary)
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            local_image_path = row['image']
            # Upload local image sur Cloudinary
            try:
                public_id = os.path.splitext(os.path.basename(local_image_path))[0].replace(' ', '-').lower()
                logs.append(f"Upload de l'image locale '{local_image_path}' sur Cloudinary...")
                cloud_url = upload_image_to_cloudinary(local_image_path, public_id)
                logs.append(f"Image uploadée : {cloud_url}")
                row['image'] = cloud_url
            except Exception as e:
                logs.append(f"Erreur upload image '{local_image_path}' : {e}")
                row['image'] = ""

            writer.writerow(row)

        # Relire le CSV modifié depuis output pour importer les produits
        output.seek(0)
        modif_reader = csv.DictReader(output)

        for produit in modif_reader:
            try:
                data = {
                    "name": produit["name"],
                    "type": "simple",
                    "regular_price": str(produit["price"]),
                    "categories": [{"name": produit["categorie"]}],
                    "images": [{"src": produit["image"]}] if produit["image"] else [],
                    "stock_quantity": int(produit["stock"]),
                    "manage_stock": True,
                    "in_stock": int(produit["stock"]) > 0,
                    "status": "publish"
                }
                response = wcapi.post("products", data).json()
                if "id" in response:
                    logs.append(f"Produit '{produit['name']}' ajouté avec succès (ID: {response['id']})")
                else:
                    logs.append(f"Erreur ajout produit '{produit['name']}': {response}")
            except Exception as e:
                logs.append(f"Exception produit '{produit['name']}': {e}")

    except Exception as e:
        logs.append(f"Erreur lecture CSV ou traitement : {e}")

    return "\n".join(logs)

@app.route('/', methods=['GET', 'POST'])
def index():
    logs = None
    if request.method == 'POST':
        if 'csv_file' not in request.files:
            flash("Aucun fichier sélectionné")
            return redirect(request.url)
        file = request.files['csv_file']
        if file.filename == '':
            flash("Aucun fichier sélectionné")
            return redirect(request.url)

        logs = process_csv_and_import_products(file)
    return render_template_string(HTML, logs=logs)


if __name__ == '__main__':
    app.run(debug=True)
