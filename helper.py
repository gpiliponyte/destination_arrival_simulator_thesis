
import streamlit as st
import geopandas as gp
import pandas as pd
import plotly.express as px
import numpy as np

SIM_TYPE_TOPN = 'Top highlights'
SIM_TYPE_SIMILAR_TOPN = 'Similar Top-N'

REALITY = 'reality'
SIMULATION = 'simulation'

SIM_SIDE_BY_SIDE = "See Side by Side Comparison"
SIM_ONLY_VIEW = "See only the Simulation"
SIM_DELTA = "See Delta"


def setup_state():
    if 'comparable' not in st.session_state:
        st.session_state.comparable = False
    if 'nclick' not in st.session_state:
        st.session_state.nclick = 0
    if 'executed_simulation' not in st.session_state:
        st.session_state.executed_simulation = None
    if 'mode' not in st.session_state:
        st.session_state.mode = REALITY


@st.cache
def load_data():  # LOAD SIMULATION AND REAL DATA ON LOAD


    districts = gp.read_file('data/geo_district_df.shp')
    nationality = pd.read_csv('data/nationality_trends_yearly.csv')
    category = pd.read_csv('data/category_trends_yearly.csv')
    overall = pd.read_csv('data/trends_yearly.csv') 
    districts_sim = pd.read_csv('data/districts_sim.csv', index_col=1) 

    nationality = nationality[nationality['Year'] == 2020]
    category = category[category['Year'] == 2020]
    overall = overall[overall['Year'] == 2020]

    nationality = districts.merge(nationality, on='district_c', how = "inner")
    category = districts.merge(category, on='district_c', how = "inner")
    overall = districts.merge(overall, on='district_c', how = "inner")

    municipalities = gp.read_file('./data/geo_df.shp')
    municipalities_sim = pd.read_csv(
        './data/municiplaities_sim.csv', index_col=0)
    municipalities_sim = 1 - municipalities_sim
    municipalities_sim = municipalities_sim.loc[municipalities['PRO_COM'], [
        str(c) for c in municipalities['PRO_COM']]]
    return municipalities, municipalities_sim, districts, nationality, category, overall, districts_sim



def on_run_simulation_btn_click():
    st.session_state['comparable'] = True
    st.session_state.nclick += 1
    st.session_state.executed_simulation = st.session_state.selectbox_symtype
    st.session_state.mode = SIMULATION


def get_view():
    st.session_state.mode = REALITY

# arrival map


def generate_map_diagram(df, target, title, isDelta=False):

    # ok = df.dissolve(by='district', aggfunc='sum')


    vmin = df['Arrivals'].min()
    vmax = df['Arrivals'].max()

    color_scale = 'viridis'

    if isDelta:
        df['diff'] = df[target] - df['Arrivals']
        vmin = df['diff'].min()
        vmax = df['diff'].max() * .5
        target = 'diff'
        color_scale = "PRGn"

    fig = px.choropleth(df,
                        geojson=df.geometry,
                        locations=df.index,
                        color=f'{target}',
                        projection='mercator',
                        color_continuous_scale=color_scale,
                        range_color=[vmin, vmax],
                        title=title,
                        labels={f'{target}': 'Arrivals'},
                        height=600,
                        hover_data=["district_i", "district_g", f'{target}']
                        )
    fig.update_geos(fitbounds="locations", visible=False,)

    fig.update_layout(
        margin={"r": 0, "t": 100, "l": 0, "b": 0},
        coloraxis_colorbar_thickness=10,
        coloraxis_colorbar_title_side='right',
        # coloraxis_colorbar_x=0.83
        # disable drag and zoom
        dragmode=False,
        hoverlabel=dict(
            bgcolor="white",
            font_size=14
        )
    )

    fig.update_coloraxes(colorbar_ypad=150, colorbar_xpad=0)
    return fig


def on_reality_bar_chart_setup(df, number_of_municipalities, order_municipalities, type = "Nationality"):

    # number_mun = number_of_municipalities if number_of_municipalities else 5
    # order_mun = True if order_municipalities == "Ascending" else False
    temp_df = df.copy()
    # temp_df = temp_df.head(number_mun)

    fig = px.bar(temp_df, title="Arrivals for District by Nationality", x="district_i",  y="Arrivals", color=type, color_discrete_sequence=px.colors.sequential.Sunset, labels={
        "district_i": "District"
    }, height=600)

    return fig


def generate_simulation_bar_chart(df, comparison_target):

    fig = px.bar(df, y='diff', x='district_i', text_auto='.2s',
                 title="Arrival Diff after Simulation",
                 color_continuous_scale='viridis',
                 color='diff',
                 labels={'diff': 'Tourist demand diff.',
                         'arrivi_tot': 'Demand (real)', comparison_target: 'Demand (sim.)', 'district_i': "District"},
                 text='diff',
                 hover_data=["district_i", "diff",
                             "Arrivals", comparison_target],
                 height=600)

    fig.update_layout(
        margin={"r": 0, "t": 100, "l": 0, "b": 0},
        coloraxis_colorbar_thickness=10,
        coloraxis_colorbar_title='',
        # coloraxis_colorbar_x=0.83
        hoverlabel=dict(
            bgcolor="white",
            font_size=14
        )
    )

    return fig
