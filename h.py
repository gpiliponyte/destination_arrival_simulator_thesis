
import streamlit as st
import geopandas as gp
import pandas as pd
import plotly.express as px
import numpy as np
import math
import random

SIM_TYPE_RANDOMN = 'Random-N'
SIM_TYPE_TOPN = 'Top-N'
SIM_TYPE_BOTTOMN = 'Bottom-N'

REALITY = 'reality'
SIMULATION = 'simulation'

SIM_VIEW = "Simulation View"
SIM_DELTA = "Delta View"
SIM_COMP = "Comparison View"


METRIC_ARRIVALS = "Arrivals"
METRIC_AVG_PRESENT = "AvgPresent"
METRIC_AVG_PRESENT_TO_BEDS = "AvgPresentToBeds"
METRIC_AVG_PRESENT_TO_POP = "AvgPresentToPop"

TYPE_GENERAL = "General"
TYPE_NAT = "By Nationality"
TYPE_ACC = "By Type of Accomodation"

district_code_map = {1: "Bozen", 2: "Burggrafenamt", 3: "Eisacktal", 4: "Pustertal", 5: "Salten-Schlern", 6: "Uberetsch-Unterland", 7: "Vinschgau", 8: "Wipptal"}

months = {"January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
              "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12}

CHOICE_UTILITY = 5
DECAY_RATE = 1.2
similarities = pd.read_csv('data/similarities_indexed.csv', index_col=0)
arrivals2 = pd.DataFrame({})

destinationDF = pd.DataFrame({})


def setup_state():
    if 'comparable' not in st.session_state:
        st.session_state.comparable = False
    if 'nclick' not in st.session_state:
        st.session_state.nclick = 0
    if 'executed_simulation' not in st.session_state:
        st.session_state.executed_simulation = None
    if 'mode' not in st.session_state:
        st.session_state.mode = REALITY


@st.cache(allow_output_mutation=True)
def load_data():  # LOAD SIMULATION AND REAL DATA ON LOAD

    districts = gp.read_file('data/geo_district_df.shp')
    nationality = pd.read_csv('data/nationality_trends.csv')
    category = pd.read_csv('data/category_trends.csv')
    overall = pd.read_csv('data/overall_trends.csv')

    nationality = districts.merge(
        nationality, on='district_c', how="inner", suffixes=('', '_y'))
    category = districts.merge(
        category, on='district_c', how="inner", suffixes=('', '_y'))
    overall = districts.merge(overall, on='district_c',
                              how="inner", suffixes=('', '_y'))

    overall['sim_arrivals'] = np.random.permutation(overall["Arrivals"].values)
    overall['sim_present'] = np.random.permutation(overall['Present'].values)
    overall['diff'] = overall['Arrivals'] - overall['sim_arrivals']

    category['sim_arrivals'] = np.random.permutation(
        category["Arrivals"].values)
    category['sim_present'] = np.random.permutation(category['Present'].values)
    category['diff'] = category['Arrivals'] - category['sim_arrivals']

    nationality['sim_arrivals'] = np.random.permutation(
        nationality["Arrivals"].values)
    nationality['sim_present'] = np.random.permutation(
        nationality['Present'].values)
    nationality['diff'] = nationality['Arrivals'] - nationality['sim_arrivals']

    nationalityDictionary = {
        '2020': nationality[nationality['Year'] == 2020],
        '2019': nationality[nationality['Year'] == 2019],
        '2018': nationality[nationality['Year'] == 2018],
        '2017': nationality[nationality['Year'] == 2017],
        '2016': nationality[nationality['Year'] == 2016],
        '2015': nationality[nationality['Year'] == 2015],
        '2014': nationality[nationality['Year'] == 2014],
        '2013': nationality[nationality['Year'] == 2013],
        '2012': nationality[nationality['Year'] == 2012],
        '2011': nationality[nationality['Year'] == 2011],
        '2010': nationality[nationality['Year'] == 2010],
    }

    overallDictionary = {
        '2020': overall[overall['Year'] == 2020],
        '2019': overall[overall['Year'] == 2019],
        '2018': overall[overall['Year'] == 2018],
        '2017': overall[overall['Year'] == 2017],
        '2016': overall[overall['Year'] == 2016],
        '2015': overall[overall['Year'] == 2015],
        '2014': overall[overall['Year'] == 2014],
        '2013': overall[overall['Year'] == 2013],
        '2012': overall[overall['Year'] == 2012],
        '2011': overall[overall['Year'] == 2011],
        '2010': overall[overall['Year'] == 2010],
    }

    categoryDictionary = {
        '2020': category[category['Year'] == 2020],
        '2019': category[category['Year'] == 2019],
        '2018': category[category['Year'] == 2018],
        '2017': category[category['Year'] == 2017],
        '2016': category[category['Year'] == 2016],
        '2015': category[category['Year'] == 2015],
        '2014': category[category['Year'] == 2014],
        '2013': category[category['Year'] == 2013],
        '2012': category[category['Year'] == 2012],
        '2011': category[category['Year'] == 2011],
        '2010': category[category['Year'] == 2010],
    }

    municipalities = gp.read_file('./data/geo_df.shp')
    municipalities_sim = pd.read_csv(
        './data/municiplaities_sim.csv', index_col=0)
    municipalities_sim = 1 - municipalities_sim
    municipalities_sim = municipalities_sim.loc[municipalities['PRO_COM'], [
        str(c) for c in municipalities['PRO_COM']]]
    return municipalities, municipalities_sim, districts, nationality, category, overall, categoryDictionary, overallDictionary, nationalityDictionary


def nameLoopup(districtCode):
    return  district_code_map[districtCode]


def printAdvertisements(destinations):
    # st.write("Generated Advertisement: \n")
    # for index, el in enumerate(destinations):
    #     st.write('Item', index+1, ": ", district_code_map[el])
    # st.write("\n")

    # st.sidebar.subheader("Generated Advertisement")

    destinationNames = list(map(nameLoopup, destinations))

    destinationDF = pd.DataFrame(destinationNames, columns=['Destination'])
    destinationDF.index = destinationDF.index + 1
    # st.sidebar.table(destinationDF)

def formatProbabilities(probabilities):
    st.write("Selection Probabilities: \n")
    for key in probabilities:
        st.write(district_code_map[key], probabilities[key]*100, "%")

def getUtilities(advertisement, userChoice):

    utilities = {userChoice: CHOICE_UTILITY}

    for index, d in enumerate(advertisement):
        utility = similarities[str(userChoice)].loc[d]*userChoice/(DECAY_RATE**index) 
        if d in utilities:
            utilities[d] = utilities[d] + utility
        else:
            utilities[d] = utility 
        
    return utilities

def getProbabilities(utilities):
    
    elSum = 0
    probabilities = {}
    
    for uKey in utilities:
        elSum = elSum + math.exp(utilities[uKey])
    
    for uKey in utilities:
        probabilities[uKey] = math.exp(utilities[uKey])/elSum
        
    return probabilities

def on_run_simulation_btn_click(year, type, n, conv_rate, seen_rate):


    # run advertisement

    arrivalCounts = pd.read_csv("data/districts_ranked.csv")
    ac = arrivalCounts[arrivalCounts['Year'] == year]
    
    if type == SIM_TYPE_TOPN:
        ad = ac['district_c'].head(n).tolist()
    elif type == SIM_TYPE_BOTTOMN:
        ad = ac.sort_values(by='Rank', ascending=False)['district_c'].head(n).tolist()
    else:
        ad = random.sample(range(1, 9), n)

    printAdvertisements(ad)

    # setup stuff
    arrivals = pd.read_csv('data/nationality_long.csv')
    arrivals = arrivals[arrivals['Year'] == year]

    arrivalsDf = arrivals

    # construct a new dataframe
    df = pd.DataFrame(columns=['Year', 'Month', 'Season', 'Nationality', 'district_c', 'District', 'Arrivals'])
    nationalities = ['Austria', 'Benelux countries', 'Germany', 'Italy', 'Other countries', 'Switzerland and Liechtenstein']


    for i, row in arrivalsDf.iterrows():
    
        utilities = getUtilities(ad, row['district_c'])
        probabilities = getProbabilities(utilities)

        elements = list(probabilities.keys())
        
        choices = random.choices(elements, weights=list(probabilities.values()), k=int(row['Arrivals']))
        
        start = [row['Year'], row['Month'], row['Season']]
        
        for nat in nationalities:
            
            natCount = int(row[nat])
                
            natChoices = choices[0:natCount]
            choices = choices[natCount:]
            
            for dist in range(1, 9):
                df.loc[len(df.index)] = start + [nat] + [dist] + [district_code_map[dist]] + [natChoices.count(dist)]

    simulatedResults = df.groupby(by=['Year', 'Month', 'Season', 'Nationality', 'district_c', 'District']).sum().reset_index()

    simulatedResults.to_csv('data/sim.csv', index=False)

    arrivals2 = pd.read_csv('data/nationality_trends.csv')
    arrivals2 = arrivals2[arrivals2['Year'] == year]

    arrivals2 = arrivals2.merge(simulatedResults, how='inner', on=["Year", "Month", "district_c", "Nationality"], suffixes=("", "_sim"))
    arrivals2 = arrivals2.drop(['Season_sim'], axis = 1)
    arrivals2['Diff'] = arrivals2['Arrivals_sim'] - arrivals2['Arrivals']

    st.session_state['comparable'] = True
    st.session_state.nclick += 1
    st.session_state.arrivals_sim = arrivals2
    st.session_state.executed_simulation = st.session_state.selectbox_symtype
    st.session_state.mode = SIMULATION



def get_view():
    st.session_state.mode = REALITY

# arrival map


def generate_map_diagram_reality(overallDf, categoryDf, nationalityDf, target, isDelta=False, spec='All', year=2020, mode='General', season='', month='January', type=TYPE_GENERAL):


    if type == TYPE_NAT and spec != 'All':
        df = nationalityDf.copy()
        df = df[df['Nationality'] == spec]
    elif type == TYPE_ACC and spec != "All":
        df = categoryDf.copy()
        df = df[df['Category'] == spec]
    else:
        df = overallDf

    districts = gp.read_file('data/geo_district_df.shp')

    if mode == 'Seasons':
        df = df.groupby(['Year', 'Season', 'district_c']).sum()
        df = df.reset_index()
        df = districts.merge(df, on='district_c',
                             how="inner", suffixes=('', '_y'))
        df = df[df['Season'] == season]
        div = 90
    elif mode == 'Month':
        df = df.groupby(['Year', 'Month', 'district_c']).sum()
        df = df.reset_index()
        df = districts.merge(df, on='district_c',
                             how="inner", suffixes=('', '_y'))
        df = df[df['Month'] == months[month]]
        div = 30
    else:
        df = df.groupby(['Year', 'district_c']).sum()
        df = df.reset_index()
        df = districts.merge(df, on='district_c',
                             how="inner", suffixes=('', '_y'))
        div = 365

    df["AvgPresent"] = df["Present"] / div
    if "beds" not in df:
        districts = gp.read_file('data/geo_district_df.shp')
        df = districts.merge(df, on='district_c',
                             how="inner", suffixes=('', '_y'))
    df["AvgPresentToBeds"] = df["AvgPresent"] / df["beds"]
    df["AvgPresentToPop"] = df["AvgPresent"] / df["population"]

    color_scale = 'sunset'

    if isDelta:
        # "RdBu" #["red", "white", "green"]
        color_scale = ['#eb8383', "#ffffff", '#5b5399']
        if target != 'Arrivals':
            df["AvgPresentSim"] = df["sim_present"] / div
            if target == "AvgPresent":
                df["AvgPresentDiff"] = df["AvgPresentSim"] - df["AvgPresent"]
                target = "AvgPresentDiff"
            if target == "AvgPresentToBeds":
                df["AvgPresentToBedsSim"] = df["AvgPresentSim"] / df["beds"]
                df["AvgPresentToBedsDiff"] = df["AvgPresentToBedsSim"] - \
                    df["AvgPresentToBeds"]
                target = "AvgPresentToBedsDiff"
            if target == "AvgPresentToPop":
                df["AvgPresentToPopSim"] = df["AvgPresentSim"] / df["population"]
                df["AvgPresentToPopDiff"] = df["AvgPresentToPopSim"] - \
                    df["AvgPresentToPop"]
                target = "AvgPresentToPopDiff"
        else:
            target = 'diff'

    fig = setupMapDiagram(df, target, color_scale)

    return fig

def generate_map_diagram_simulation(isDelta=False, mode='General', season='', month='January'):

    target = 'Arrivals'

    df = st.session_state.arrivals_sim
    districts = gp.read_file('data/geo_district_df.shp')

    if mode == 'Seasons':
        df = df.groupby(['Season', 'district_c']).sum()
        df = df.reset_index()
        df = districts.merge(df, on='district_c',
                             how="inner", suffixes=('', '_y'))
        df = df[df['Season'] == season]
    elif mode == 'Month':
        df = df.groupby(['Month', 'district_c']).sum()
        df = df.reset_index()
        df = districts.merge(df, on='district_c',
                             how="inner", suffixes=('', '_y'))
        df = df[df['Month'] == months[month]]
    else:
        df = df.groupby(['district_c']).sum()
        df = df.reset_index()
        df = districts.merge(df, on='district_c',
                             how="inner", suffixes=('', '_y'))

    color_scale = 'sunset'

    if isDelta:
        # "RdBu" #["red", "white", "green"]
        color_scale = ['#eb8383', "#ffffff", '#5b5399']
        target = 'Diff'

    fig = setupMapDiagram(df, target, color_scale)

    return fig

def setupMapDiagram(df, target, color_scale):

    df['Rank'] = df[target].rank(ascending=False)

    df['Name'] = df[['district_i', 'district_g']].apply(
        lambda x: ' /\n'.join(x), axis=1)

    df = df.round(2)

    vmin = df[target].min()
    vmax = df[target].max()

    fig = px.choropleth(df,
                        geojson=df.geometry,
                        color=f'{target}',
                        projection='mercator',
                        color_continuous_scale=color_scale,
                        range_color=[vmin, vmax],
                        # title=title,
                        labels={"Rank": "#Rank (asc)"},
                        height=600,
                        hover_name="Name",
                        hover_data={"Rank", f'{target}'},
                        locations=df.index

                        )
    fig.update_geos(fitbounds="locations", visible=False)

    fig.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0, "pad": 400},
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

    fig.update_coloraxes(colorbar_ypad=90, colorbar_xpad=0)

    return fig


def on_reality_bar_chart_setup(df, nationalityBarDf, categoryBarDf, target, type="Nationality", x="district_i"):

    titleDia = f'{target} for {x} by {type} in 2020'
    months = ["January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November", "December"]

    dictionary = {'Distict': 'district_i', 'Season': 'Season', 'Month': 'Month',
                  'Nationality': 'Nationality', 'Accommodation': 'Category'}
    type = dictionary[type]
    x = dictionary[x]

    if type == "Category" or x == "Category":
        df = categoryBarDf

    if type == "Nationality" or x == "Nationality":
        df = nationalityBarDf

    # df['Month'] = dictionary[df['Month'] - 1]

    nbins = len(df[x].unique())

    fig = px.histogram(df, title=f'{target} for District by Nationality', x=x, nbins=nbins, histfunc="sum",  y=target, color=type, color_discrete_sequence=px.colors.sequential.Sunset, labels={
        "district_i": "District"
    }, height=600)

    return fig


def generate_simulation_bar_chart(df, y='Diff', title='title'):
    
    df = df.groupby(["Year", "District"]).sum().reset_index()

    format = '.2s'

    if df[y][0] < 1 and df[y][0] > -1:
        format = '.3f'

    fig = px.bar(df, y=y, x='District', text_auto=format,
                 title=title,
                 color_continuous_scale=['#eb8383', "#ffffff", '#5b5399'],
                 color=y,
                 labels={
                     'arrivi_tot': 'Demand (real)', 'District': "District"},
                 text='Diff',
                 hover_data=["District", y],
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
