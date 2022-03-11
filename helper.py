
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
    municipalities = gp.read_file('./data/geo_df.shp')
    municipalities_sim = pd.read_csv(
        './data/municiplaities_sim.csv', index_col=0)
    municipalities_sim = 1 - municipalities_sim
    municipalities_sim = municipalities_sim.loc[municipalities['PRO_COM'], [
        str(c) for c in municipalities['PRO_COM']]]
    return municipalities, municipalities_sim


def mock_nationalities(dataFrame):
    df = dataFrame.copy()
    df["germans"] = df["arrivi_tot"] * 0.3
    df["italians"] = df["arrivi_tot"] * 0.5
    df["americans"] = df["arrivi_tot"] * 0.1
    df["others"] = df["arrivi_tot"] * 0.1
    return df


def on_run_simulation_btn_click():
    st.session_state['comparable'] = True
    st.session_state.nclick += 1
    st.session_state.executed_simulation = st.session_state.selectbox_symtype
    st.session_state.mode = SIMULATION


def get_view():
    st.session_state.mode = REALITY

# arrival map


def generate_map_diagram(df, target, vmin, vmax, title, isDelta = False):

    if isDelta:
        df['diff'] = df[target] - df['arrivi_tot']
        vmin = df['diff'].min()
        vmax = df['diff'].max() * .5
        target = 'diff'

    fig = px.choropleth(df,
                        geojson=df.geometry,
                        locations=df.index,
                        color= f'{target}',
                        projection='mercator',
                        color_continuous_scale='viridis',
                        range_color=[vmin, vmax],
                        title=title,
                        labels={f'{target}': 'Arrivals'},
                        height=600,
                        hover_data=["COMUNE", f'{target}']
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


def on_reality_bar_chart_setup(df, number_of_municipalities, order_municipalities):
    number_mun = number_of_municipalities if number_of_municipalities else 5
    order_mun = True if order_municipalities == "Ascending" else False
    temp_df = df.copy()
    temp_df.sort_values('arrivi_tot', inplace=True, ascending=order_mun)
    temp_df = temp_df.head(number_mun)
    fig = px.bar(temp_df, title="Arrivals for Municipality by Nationality", x="COMUNE",  y=["germans", "italians", "americans", "others"], color_discrete_sequence=px.colors.sequential.Viridis, labels={
        "COMUNE": "Municipality",
        "value": "Arrivals"
    }, height=600)

    return fig


def generate_simulation_bar_chart(df, comparison_target):

    fig = px.bar(df, y='diff', x='COMUNE', text_auto='.2s',
                 title="Arrival Diff after Simulation",
                 color_continuous_scale='viridis',
                 color='diff',
                 labels={'diff': 'Tourist demand diff.',
                         'arrivi_tot': 'Demand (real)', comparison_target: 'Demand (sim.)', 'COMUNE': "Municipality"},
                 text='diff',
                 hover_data=["COMUNE", "diff",
                             "arrivi_tot", comparison_target],
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
