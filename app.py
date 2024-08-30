import streamlit as st
import requests
from datetime import datetime
import folium
from streamlit_folium import st_folium

# Title of the app
st.title('Taxi Fare Prediction')

st.markdown('''
## Enter the details of your ride below:
''')

def coordinates(address):
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': address,
        'format': 'json'
    }
    headers = {'User-Agent': "My demo geomap app"}

    response = requests.get(url, params=params, headers=headers).json()
    if response and len(response) > 0:
        return (float(response[0]['lat']), float(response[0]['lon']))
    else:
        st.error(f"Could not get coordinates for address: {address}")
        return None, None
# 1. Input widgets for ride parameters
date = st.date_input('# Date of the ride', datetime.now().date())
time = st.time_input('# Time of the ride', datetime.now().time())
passenger_count = st.number_input('Passenger Count', min_value=1, max_value=8, value=1)

# Combine date and time into a single datetime string
pickup_datetime = datetime.combine(date, time).strftime('%Y-%m-%d %H:%M:%S')

# Selection of input method
input_method = st.radio(
    "Select the method to enter the pickup and dropoff locations:",
    ('Enter Coordinates Manually', 'Enter Addresses', 'Select on Map')
)

if input_method == 'Enter Coordinates Manually':
    pickup_longitude = st.number_input('Pickup Longitude', value=0.0)
    pickup_latitude = st.number_input('Pickup Latitude', value=0.0)
    dropoff_longitude = st.number_input('Dropoff Longitude', value=0.0)
    dropoff_latitude = st.number_input('Dropoff Latitude', value=0.0)

elif input_method == 'Enter Addresses':
    pickup_address = st.text_input('Enter Pickup Address', value='Barclays Center')
    dropoff_address = st.text_input('Enter Dropoff Address', value='Madison Square Garden')

    if pickup_address and dropoff_address:
        pickup_latitude, pickup_longitude = coordinates(pickup_address)
        dropoff_latitude, dropoff_longitude = coordinates(dropoff_address)
        st.write(f"Pickup coordinates: {pickup_latitude}, {pickup_longitude}")
        st.write(f"Dropoff coordinates: {dropoff_latitude}, {dropoff_longitude}")

elif input_method == 'Select on Map':
    # Initialize map centered at a default location
    m = folium.Map(location=[40.7128, -74.0060], zoom_start=13)

    # Add markers if coordinates are already selected
    if 'pickup_coords' in st.session_state:
        folium.Marker(st.session_state.pickup_coords, popup="Pickup Location", icon=folium.Icon(color='green')).add_to(m)

    if 'dropoff_coords' in st.session_state:
        folium.Marker(st.session_state.dropoff_coords, popup="Dropoff Location", icon=folium.Icon(color='red')).add_to(m)

    # Select between setting pickup or dropoff
    selection_type = st.radio("Select which location to set:", ('Pickup Location', 'Dropoff Location'))

    # Display the map and allow user interaction
    st.write("Click on the map to select the location.")
    map_data = st_folium(m, width=700, height=450)

    # Capture map clicks
    if map_data and map_data['last_clicked']:
        lat = map_data['last_clicked']['lat']
        lng = map_data['last_clicked']['lng']

        # Update the correct coordinates based on the user's selection
        if selection_type == 'Pickup Location':
            st.session_state.pickup_coords = (lat, lng)
            st.write(f"Pickup coordinates set to: {st.session_state.pickup_coords}")
        else:
            st.session_state.dropoff_coords = (lat, lng)
            st.write(f"Dropoff coordinates set to: {st.session_state.dropoff_coords}")

    # Extract coordinates for API call if both are set
    if 'pickup_coords' in st.session_state:
        pickup_latitude, pickup_longitude = st.session_state.pickup_coords

    if 'dropoff_coords' in st.session_state:
        dropoff_latitude, dropoff_longitude = st.session_state.dropoff_coords

# Only create the route map if both coordinates are available
if pickup_latitude is not None and dropoff_latitude is not None:
    # Create a new map centered between pickup and dropoff locations
    route_map = folium.Map(location=[(pickup_latitude + dropoff_latitude) / 2,
                                     (pickup_longitude + dropoff_longitude) / 2], zoom_start=13)

    # Add markers for the pickup and dropoff locations
    folium.Marker([pickup_latitude, pickup_longitude], popup="Pickup Location", icon=folium.Icon(color='green')).add_to(route_map)
    folium.Marker([dropoff_latitude, dropoff_longitude], popup="Dropoff Location", icon=folium.Icon(color='red')).add_to(route_map)

    # Draw a line between pickup and dropoff
    folium.PolyLine(locations=[(pickup_latitude, pickup_longitude), (dropoff_latitude, dropoff_longitude)], color='blue').add_to(route_map)

    # Display the map
    st.write("Route Preview:")
    st_folium(route_map, width=700, height=450)


# 2. Build the dictionary containing the parameters for the API
params = {
    'pickup_datetime': pickup_datetime,
    'pickup_longitude': pickup_longitude,
    'pickup_latitude': pickup_latitude,
    'dropoff_longitude': dropoff_longitude,
    'dropoff_latitude': dropoff_latitude,
    'passenger_count': passenger_count
}

# 3. Call the API using the `requests` package
if st.button('Predict Fare'):
    response = requests.get('https://taxifare.lewagon.ai/predict', params=params)

    if response.status_code == 200:
        # 4. Retrieve and display the prediction
        prediction = response.json().get('fare', 'Error: No prediction returned')
        st.success(f'The estimated fare is: ${prediction:.2f}')
    else:
        st.error('Error in API call')

st.markdown('''
## You can try with different parameters to see how the fare changes!
''')
