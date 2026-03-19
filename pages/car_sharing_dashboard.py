import streamlit as st
import pandas as pd
import numpy as np

# ---- LOAD DATA ----
@st.cache_data
def load_data():
    trips = pd.read_csv("/workspaces/my-analytic-project/.venv/datasets/trips.csv")
    cars = pd.read_csv("/workspaces/my-analytic-project/.venv/datasets/cars.csv")
    cities = pd.read_csv("/workspaces/my-analytic-project/.venv/datasets/cities.csv")
    return trips, cars, cities

trips, cars, cities = load_data()

# ---- MERGE DATAFRAMES ----
trips_merged = trips.merge(cars, left_on="car_id", right_on="id", suffixes=("", "_car"))
trips_merged = trips_merged.merge(cities, on="city_id")

# ---- DROP USELESS COLUMNS ----
trips_merged = trips_merged.drop(columns=["id_car", "city_id", "customer_id", "id"])

# ---- CONVERT DATE FORMAT ----
trips_merged['pickup_date'] = pd.to_datetime(trips_merged['pickup_time']).dt.date
trips_merged['duration_hours'] = (pd.to_datetime(trips_merged['dropoff_time']) - pd.to_datetime(trips_merged['pickup_time'])).dt.total_seconds() / 3600

# ---- SIDEBAR FILTERS ----
st.sidebar.header("Filters")

# Filter by Car Brand
cars_brand = st.sidebar.multiselect("Select Car Brand", trips_merged["brand"].unique())
if cars_brand:
    trips_merged = trips_merged[trips_merged["brand"].isin(cars_brand)]

# Filter by Car Model
car_models = st.sidebar.multiselect("Select Car Model", trips_merged["model"].unique())
if car_models:
    trips_merged = trips_merged[trips_merged["model"].isin(car_models)]

# Filter by City
city_filter = st.sidebar.multiselect("Select City", trips_merged["city_name"].unique())
if city_filter:
    trips_merged = trips_merged[trips_merged["city_name"].isin(city_filter)]

# Filter by Date Range
min_date = trips_merged['pickup_date'].min()
max_date = trips_merged['pickup_date'].max()
date_range = st.sidebar.date_input("Select Date Range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
if len(date_range) == 2:
    trips_merged = trips_merged[(trips_merged['pickup_date'] >= date_range[0]) & (trips_merged['pickup_date'] <= date_range[1])]

# Filter by Revenue
min_rev = float(trips_merged["revenue"].min())
max_rev = float(trips_merged["revenue"].max())
revenue_range = st.sidebar.slider("Revenue Range", min_value=min_rev, max_value=max_rev, value=(min_rev, max_rev))
trips_merged = trips_merged[(trips_merged["revenue"] >= revenue_range[0]) & (trips_merged["revenue"] <= revenue_range[1])]

# ---- TITLE ----
st.title("Car Sharing Dashboard")

# ---- BUSINESS METRICS ----
total_trips = len(trips_merged)
total_distance = trips_merged["distance"].sum()

if total_trips > 0:
    top_car = trips_merged.groupby("model")["revenue"].sum().idxmax()
else:
    top_car = "N/A"

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Total Trips", value=total_trips)
with col2:
    st.metric(label="Top Car Model by Revenue", value=top_car)
with col3:
    st.metric(label="Total Distance (km)", value=f"{total_distance:,.2f}")

# ---- PREVIEW DATA ----
st.write(trips_merged.head())

# ---- VISUALIZATIONS ----

# 1. Trips Over Time
st.subheader("Trips Over Time")
trips_over_time = trips_merged.groupby("pickup_date").size().reset_index(name="trips")
st.line_chart(trips_over_time.set_index("pickup_date"))

# 2. Revenue Per Car Model
st.subheader("Revenue Per Car Model")
revenue_per_model = trips_merged.groupby("model")["revenue"].sum().reset_index()
st.bar_chart(revenue_per_model.set_index("model"))

# 3. Cumulative Revenue Growth Over Time
st.subheader("Cumulative Revenue Growth Over Time")
revenue_over_time = trips_merged.groupby("pickup_date")["revenue"].sum().cumsum().reset_index()
revenue_over_time.columns = ["pickup_date", "cumulative_revenue"]
st.area_chart(revenue_over_time.set_index("pickup_date"))

# 4. Revenue by City
st.subheader("Revenue by City")
revenue_by_city = trips_merged.groupby("city_name")["revenue"].sum().reset_index()
st.bar_chart(revenue_by_city.set_index("city_name"))

# 5. Number of Trips Per Car Model
st.subheader("Number of Trips Per Car Model")
trips_per_model = trips_merged.groupby("model").size().reset_index(name="trips")
st.bar_chart(trips_per_model.set_index("model"))

# 6. Average Trip Duration by City
st.subheader("Average Trip Duration by City")
avg_duration_city = trips_merged.groupby("city_name")["duration_hours"].mean().reset_index()
avg_duration_city.columns = ["city_name", "avg_duration_hours"]
st.bar_chart(avg_duration_city.set_index("city_name"))

# 7. Trips Per City
st.subheader("Trips Per City")
trips_per_city = trips_merged.groupby("city_name").size().reset_index(name="trips")
st.bar_chart(trips_per_city.set_index("city_name"))

# 8. Average Revenue Per Brand
st.subheader("Average Revenue Per Brand")
avg_rev_brand = trips_merged.groupby("brand")["revenue"].mean().reset_index()
st.bar_chart(avg_rev_brand.set_index("brand"))

# 9. Distance Distribution
st.subheader("Distance Distribution")
hist_values = np.histogram(trips_merged["distance"], bins=30)
st.bar_chart(pd.DataFrame({"count": hist_values[0]}, index=[f"{edge:.1f}" for edge in hist_values[1][:-1]]))