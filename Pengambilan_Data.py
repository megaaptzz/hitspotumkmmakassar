import googlemaps
import csv
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm  # Untuk menampilkan progress bar

# Masukkan API Key Anda
API_KEY = 'AIzaSyBEi02MRGEO16mawpoDzzm8-OcNXgaVKcQ'
gmaps = googlemaps.Client(key=API_KEY)

# Fungsi untuk mencari kuliner di satu area
def cari_kuliner(lokasi, radius=5000, keyword="kuliner"):
    try:
        semua_hasil = []
        hasil = gmaps.places_nearby(
            location=lokasi, radius=radius, keyword=keyword
        )
        semua_hasil.extend(hasil['results'])

        # Pagination untuk hasil tambahan
        while 'next_page_token' in hasil:
            next_page_token = hasil['next_page_token']
            time.sleep(2)  # Tunggu agar token valid
            hasil = gmaps.places_nearby(
                location=lokasi, radius=radius, keyword=keyword, page_token=next_page_token
            )
            semua_hasil.extend(hasil['results'])

        return semua_hasil
    except Exception as e:
        print(f"Error di lokasi {lokasi}: {e}")
        return []

# Fungsi untuk membagi area pencarian menjadi grid berdasarkan bounding box
def generate_grid_from_bbox(bbox, step):
    lat_min, lat_max, lng_min, lng_max = bbox
    grid = []
    lat = lat_min
    while lat <= lat_max:
        lng = lng_min
        while lng <= lng_max:
            grid.append((lat, lng))
            lng += step
        lat += step
    return grid

# Bounding box untuk kota Makassar
bbox_makassar = (-5.23, -5.075, 119.374, 119.48)  # (lat_min, lat_max, lng_min, lng_max)
step = 0.005  # Langkah per grid (~550 meter)

# Membuat grid area berdasarkan bounding box
grid = generate_grid_from_bbox(bbox_makassar, step)

# Mengambil semua kuliner dari semua grid secara paralel
print(f"Memulai pencarian di {len(grid)} lokasi grid dengan paralelisasi...")

semua_hasil = []
with ThreadPoolExecutor(max_workers=10) as executor:  # Maksimum 10 thread
    futures = {executor.submit(cari_kuliner, lokasi, 5000): lokasi for lokasi in grid}
    for future in tqdm(as_completed(futures), total=len(futures), desc="Progres Pencarian"):
        hasil = future.result()
        semua_hasil.extend(hasil)

# Hapus duplikasi berdasarkan place_id
hasil_unik = {tempat['place_id']: tempat for tempat in semua_hasil}.values()

# Simpan hasil ke dalam file CSV
file_csv = "C:/Users/Asus/OneDrive/Documents/kuliner_makassar_all.csv"
try:
    with open(file_csv, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        # Tulis header
        writer.writerow(["Nama", "Alamat", "Rating", "Place ID", "Lokasi"])
        
        # Tulis data
        for tempat in tqdm(hasil_unik, desc="Progres Penyimpanan"):  # Progress bar untuk penyimpanan
            nama = tempat.get('name', 'Tidak ada nama')
            alamat = tempat.get('vicinity', 'Tidak ada alamat')
            rating = tempat.get('rating', 'Tidak ada rating')
            place_id = tempat.get('place_id', 'Tidak ada place_id')
            lokasi = tempat['geometry']['location']
            writer.writerow([nama, alamat, rating, place_id, lokasi])

    print(f"Hasil pencarian telah disimpan dalam file {file_csv}.")
except PermissionError as e:
    print(f"Gagal menyimpan file ke lokasi yang diberikan. Pesan error: {e}")
