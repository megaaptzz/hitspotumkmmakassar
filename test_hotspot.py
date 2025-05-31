import pandas as pd
import ast
import folium
from folium.plugins import HeatMap
from scipy.stats import gaussian_kde
import numpy as np

# Load the dataset
file_path = r"C:\Users\Asus\OneDrive\Documents\Skripsi_Megi\kuliner_makassar.csv"
data = pd.read_csv(file_path)

# Extract latitude and longitude from the 'Lokasi' column
data['Lat'] = data['Lokasi'].apply(lambda x: ast.literal_eval(x)['lat'])
data['Lng'] = data['Lokasi'].apply(lambda x: ast.literal_eval(x)['lng'])

# Prepare the coordinates
coordinates = data[['Lat', 'Lng']].values

# Create a KDE model for density estimation
kde = gaussian_kde(coordinates.T, bw_method=0.03)

# Create a grid for density estimation
lat_min, lat_max = data['Lat'].min(), data['Lat'].max()
lng_min, lng_max = data['Lng'].min(), data['Lng'].max()

lat_values = np.linspace(lat_min, lat_max, 100)
lng_values = np.linspace(lng_min, lng_max, 100)
lat_grid, lng_grid = np.meshgrid(lat_values, lng_values)

# Evaluate KDE on the grid
density = kde(np.vstack([lat_grid.ravel(), lng_grid.ravel()]))
density = density.reshape(lat_grid.shape)

# Normalize density for better visualization
density_normalized = (density - density.min()) / (density.max() - density.min())

# Create a Folium map centered around the mean location
map_center = [data['Lat'].mean(), data['Lng'].mean()]
m = folium.Map(location=map_center, zoom_start=13)

# Create a FeatureGroup for the HeatMap
heatmap_layer = folium.FeatureGroup(name='Heatmap')
heat_data = []

for lat, lng, d in zip(lat_grid.ravel(), lng_grid.ravel(), density_normalized.ravel()):
    if d > 0.01:  # Filter out very low-density areas
        heat_data.append([lat, lng, d])

HeatMap(heat_data, radius=20, blur=30, max_zoom=1, max_val=1.0).add_to(heatmap_layer)

# Create separate FeatureGroups for rating categories
rating_below_4_layer = folium.FeatureGroup(name='Rating < 4')
rating_4_to_5_layer = folium.FeatureGroup(name='Rating 4-5')

# Iterate through the data and add points to the respective layers
for _, row in data.iterrows():
    popup_content = f"""
    <b>Nama:</b> {row['Nama']}<br>
    <b>Alamat:</b> {row['Alamat']}<br>
    <b>Rating:</b> {row['Rating']}<br>
    <b>Place ID:</b> {row['Place ID']}<br>
    <b>Lokasi:</b> {row['Lat']}, {row['Lng']}
    """
    marker = folium.Marker(
        location=[row['Lat'], row['Lng']],
        popup=folium.Popup(popup_content, max_width=300),
        tooltip=row['Nama']
    )
    if row['Rating'] < 4:
        marker.add_to(rating_below_4_layer)
    elif 4 <= row['Rating'] <= 5:
        marker.add_to(rating_4_to_5_layer)

# Add the layers to the map
heatmap_layer.add_to(m)
rating_below_4_layer.add_to(m)
rating_4_to_5_layer.add_to(m)

# Add layer control to toggle layers
folium.LayerControl(collapsed=False).add_to(m)

# Save the map to an HTML file
m.save("interactive_hotspot_map_with_ratings_combined_1.html")

print("Map saved as 'interactive_hotspot_map_with_ratings_combined_1.html'. Open this file in your browser to view the result.")
