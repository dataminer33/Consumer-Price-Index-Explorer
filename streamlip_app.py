import streamlit as st
import pandas as pd
import plotly.express as px
import base64, os



color_scheme = {
    'primary': '#1e3d59',    # Dark blue
    'secondary': '#f5f0e1',  # Off-white
    'accent1': '#ff6e40',    # Orange
    'accent2': '#ffc13b',    # Yellow
    'text': '#ffffff',       # White
    'background': 'rgba(30, 61, 89, 0.8)'  # Semi-transparent dark blue
}

# Load data
@st.cache_data
def load_data():
    # Placeholder for the actual data loading code
    # Replace this with the code to load your CPI data
    data = pd.read_csv('data/processed/data_v1.csv')  # Adjust this line to your actual data source
    return data

# App Title
st.markdown('<div class="header-style"><h1>Global CPI Analysis: Food and General Consumer Price Index</h1></div>', unsafe_allow_html=True)



# Function to encode the image
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()


background_image_path = get_base64_of_bin_file('static/images/background_2.png')


   
page_bg_img = f'''
<style>
[data-testid="stAppViewContainer"] > .main {{
    background-image: url("data:image/png;base64,{background_image_path}");
    background-position: center;
    background-repeat: no-repeat;
    background-attachment: fixed;
    background-size: cover;
}}
.stApp {{
        background-color: {color_scheme['background']};
        color: {color_scheme['text']};
}}
.stButton>button {{
    color: {color_scheme['primary']};
    background-color: {color_scheme['secondary']};
}}
.stSidebar>div {{
    color: {color_scheme['primary']};
}}
.stTab {{
    background-color: {color_scheme['secondary']};
    color: {color_scheme['primary']};
}}
.stApp header {{
        background-color: rgba(0,0,0,0);
}}
.stApp > header {{
    height: 0px;
}}
.header-style {{
    background-color: rgba(0, 0, 0, 0.6);
    padding: 10px;
    border-radius: 5px;
    margin-bottom: 20px;
}}
</style>
''' 
st.markdown(page_bg_img, unsafe_allow_html=True)


# Load data
data = load_data()

# Sidebar for year range selection
st.sidebar.header('Select Year Range')
years = data['Year'].unique()
start_year, end_year = st.sidebar.select_slider(
    'Select the range of years:',
    options=years,
    value=(min(years), max(years))
)

# Filter data based on year range
filtered_data = data[(data['Year'] >= start_year) & (data['Year'] <= end_year)]

# Sidebar for continent or country selection
st.sidebar.header('Select Region')
region_type = st.sidebar.radio('Compare by:', ('Continent', 'Country'))

if region_type == 'Continent':
    regions = filtered_data['Continent'].unique()
    selected_region = st.sidebar.multiselect('Select Continents:', regions, default=regions)
else:
    countries = filtered_data['Country'].unique()
    selected_region = st.sidebar.multiselect('Select Countries:', countries, default= ['Switzerland', 'Portugal', 'Germany', 'France'])

# Filter data based on region
filtered_data = filtered_data[filtered_data[region_type].isin(selected_region)]

# CPI Comparison Plot
st.markdown(f'<div class="header-style"><h2>CPI Comparison ({region_type})</h2></div>', unsafe_allow_html=True)
cpi_type = st.selectbox('Select CPI Type:', ['Consumer Prices, Food Indices (2015 = 100)', 'Consumer Prices, General Indices (2015 = 100)', 'Food price inflation'])
filtered_data = filtered_data[filtered_data['Item'] == cpi_type]
treemap_data = filtered_data.groupby(['Continent', 'Country', 'Year'])['Value'].mean().reset_index()
filtered_data = filtered_data.groupby([region_type, 'Year'])['Value'].mean().reset_index()

fig = px.line(filtered_data, x='Year', y='Value', color=region_type, height=600, width=1200)
fig.update_xaxes(tickfont=dict(color='white', size=16))
fig.update_yaxes(tickfont=dict(color='white', size=14))
fig.update_layout(
    title=dict(text=f'{cpi_type} Trends', font=dict(size=20)),
    xaxis_tickangle=45
)
st.plotly_chart(fig)

# Identify largest increases and decreases
st.markdown(f'<div class="header-style"><h2>Largest CPI Changes from {start_year} to {end_year}</h2></div>', unsafe_allow_html=True)

# Calculate the percentage change over the selected period
cpi_changes = filtered_data.groupby(region_type)['Value'].agg(['first', 'last']).reset_index()
cpi_changes['Change in %'] = ((cpi_changes['last'] - cpi_changes['first']) / cpi_changes['first']) * 100
cpi_changes = cpi_changes.rename(columns={'first': f'Index from {start_year}', 'last': f'Index from {end_year}'})

if region_type == 'Country':
    # Bar chart for country-level changes
    cpi_changes_sorted = cpi_changes.sort_values('Change in %', ascending=False)
    fig_bar = px.bar(cpi_changes_sorted, x=region_type, y='Change in %', 
                     color='Change in %', height=600, width=1200,
                     color_continuous_scale=px.colors.sequential.Viridis,
                     hover_data={region_type: True, 'Change in %': ':.2f'})
    fig_bar.update_layout(title=f'CPI Changes by Country ({start_year} to {end_year})',
                          xaxis_title='Country', yaxis_title='Change in %')
    st.plotly_chart(fig_bar)
else:
    
    # Calculate mean values for each country
    country_means = treemap_data.groupby(['Continent', 'Country'])['Value'].mean().reset_index()
    
    # Sort countries within each continent by mean value
    country_means = country_means.sort_values(['Continent', 'Value'], ascending=[True, False])
    
    # Calculate continent totals (sum of country means)
    #continent_totals = country_means.groupby('Continent')['Value'].sum().reset_index()
    #continent_totals['Country'] = continent_totals['Continent']  # This ensures continents appear in the hierarchy
    
    # Combine country and continent data
    # treemap_data = pd.concat([country_means, continent_totals])
    
    # Create the treemap
    fig_treemap = px.treemap(country_means, 
                             path=[px.Constant("World"),'Continent', 'Country'], 
                             values='Value', 
                             color='Value', 
                             height=600, 
                             width=1200,
                             color_continuous_scale=px.colors.sequential.Viridis
                             )
    fig_treemap.update_traces(hovertemplate='%{label}<br>Value: %{value:.2f}')
    fig_treemap.update_layout(title=f'Mean CPI Values by Continent and Country ({start_year} to {end_year})')
    st.plotly_chart(fig_treemap)

# Display the regions with the biggest rises
largest_rise = cpi_changes.nlargest(10, 'Change in %')
largest_rise = largest_rise.style.format({
    "Change in %": "{:.2f}".format, 
    f'Index from {start_year}': "{:.2f}".format, 
    f'Index from {end_year}': "{:.2f}".format
})

st.dataframe(largest_rise, use_container_width=True)

# Add footer and professional touch
st.markdown(
    '''
    <div style="text-align: center; margin-top: 50px;">
        <h4>Global CPI Analysis Dashboard</h4>
        <p>Powered by Streamlit and Plotly</p>
    </div>
    ''',
    unsafe_allow_html=True
)