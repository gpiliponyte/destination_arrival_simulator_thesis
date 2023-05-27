from audioop import mul
import streamlit as st
import numpy as np
import plotly.express as px
import geopandas as gp
import pandas as pd
from collections import Counter
import h

#
# SETUP STATE
#

h.setup_state()


#
# SETUP HEADER
#

st.set_page_config(layout='wide')


col1top, col2top = st.columns([5, 1])

with col2top:
    get_reality_view_btn = st.button(
        "Actual Data", on_click=h.get_view, disabled=st.session_state.mode == h.REALITY)

with col1top:
    st.header('Tourist Trends in South Tyrol')  # to be changed to Title

with st.spinner('Loading data...'):
    municipalities, municipalities_sim, districts, nationality, category, overall, categoryDictionary, overallDictionary, nationalityDictionary = h.load_data()


#
# SETUP SIDEBAR
#

if st.session_state.mode == h.SIMULATION and st.session_state.strategy != h.SIM_TYPE_SUSTAINABLE:
    st.sidebar.subheader('Advertisement')
    for i, row in st.session_state.advertisement.iterrows():
        st.sidebar.text(str(i) + ". " + row["Destination"])

st.sidebar.subheader('Simulation Setup')

choicesDestinations = overall['district_g'].unique()

simulation_year = st.sidebar.selectbox(
    'Simulation Year:',
    (2020, 2019, 2018, 2017, 2016, 2015, 2014, 2013, 2012, 2011, 2010),
    index=1,
    key='simulation_year')

# is_nationality_considered = st.sidebar.checkbox('Setup By Campaign', value=False)

# if is_nationality_considered:
filters = [h.ALL_COUNTRIES] + h.nationalities
nationalityFilter = st.sidebar.selectbox(
     'Target Country:',
     tuple(filters))

# else:
#     nationalityFilter = -1

simulation_type = st.sidebar.selectbox(
    'Marketing Campaign:',
    (h.SIM_TYPE_TOPN, h.SIM_TYPE_BOTTOMN, h.SIM_TYPE_RANDOMN, h.SIM_TYPE_SUSTAINABLE, h.SIM_TYPE_CUSTOM),
    key='selectbox_symtype')

if simulation_type != h.SIM_TYPE_CUSTOM and simulation_type != h.SIM_TYPE_SUSTAINABLE:
    option_N = st.sidebar.selectbox(
    'Size of N:',
    (1, 2, 3, 4, 5, 6, 7, 8),
    index=2,
    key='selectbox_N_size')

if simulation_type == h.SIM_TYPE_SUSTAINABLE:
    option_N = st.sidebar.selectbox(
    'Size of N:',
    (1, 2, 3),
    index=1,
    key='selectbox_N_size')

if simulation_type == h.SIM_TYPE_CUSTOM:
    multiselect = st.sidebar.multiselect(
                'Destinations Selected (by Display Order)',
                choicesDestinations,
                [])

is_advanced = st.sidebar.checkbox('Show Advanced Settings', value=False)

if is_advanced:
    decay_rate = st.sidebar.slider('Decay Rate: ', 1.0, 2.0, h.DECAY_RATE, step=0.05)
    seen_rate = st.sidebar.slider('Seen Rate (%): ', 0.0, 100.0, 100.0, step=0.1)
    is_conv_rate_considered = st.sidebar.checkbox('Consider Convertion Rate', value=False)

    if is_conv_rate_considered:
        conversion_rate = st.sidebar.slider('Conversion Rate (%): ', 0.0, 100.0, 37.5, step=0.1)
    else:
        conversion_rate = -1 

else:
    seen_rate = 100
    conversion_rate = -1
    decay_rate = h.DECAY_RATE

def arrangeSimulation():
    with st.spinner('Computing Simulation Results...'):
        if simulation_type == h.SIM_TYPE_SUSTAINABLE:
            h.run_sustainable(simulation_year, conversion_rate, option_N, seen_rate, nationalityFilter, decay_rate)
        elif simulation_type == h.SIM_TYPE_RANDOMN:
            h.run_random(simulation_year, option_N, conversion_rate, seen_rate, nationalityFilter, decay_rate)
        elif simulation_type != h.SIM_TYPE_CUSTOM:
            h.on_run_simulation_btn_click(simulation_year, simulation_type, option_N, conversion_rate, seen_rate, [], nationalityFilter, decay_rate) 
        else:
            h.on_run_simulation_btn_click(simulation_year, simulation_type, 0, conversion_rate, seen_rate, multiselect, nationalityFilter, decay_rate)

run_simulation_btn = st.sidebar.button(
    "Run", on_click=arrangeSimulation, 
    disabled=simulation_type is None or ('multiselect' in globals() and multiselect == []))


if st.session_state.mode == h.REALITY:

    # with col1:

    # create REALITY arrival map

    mapCol1, mapCol2 = st.columns([1, 5])

    with mapCol1:
        st.subheader("Map view")

        spec_map_selectbox = "All"

        metric_map_selectbox = st.selectbox(
            'Select Metric:',
            (h.METRIC_ARRIVALS, h.METRIC_AVG_PRESENT,
             h.METRIC_AVG_PRESENT_TO_BEDS, h.METRIC_AVG_PRESENT_TO_POP),
            key='selectbox_symtype')

        mode_cat_nat_selectbox = st.selectbox(
            'Select Type of Analysis:',
            (h.TYPE_GENERAL, h.TYPE_NAT, h.TYPE_ACC),
            key='selectbox_symtype')

        if mode_cat_nat_selectbox == 'By Nationality':

            nationalities = nationality['Nationality'].unique()
            nationalities = np.insert(nationalities, 0, "All")

            spec_map_selectbox = st.selectbox(
                'Select Nationality',
                nationalities,
                key='selectbox_symtype')

        if mode_cat_nat_selectbox == 'By Type of Accomodation':

            accommodations = category['Category'].unique()
            accommodations = np.insert(accommodations, 0, "All")

            spec_map_selectbox = st.selectbox(
                'Select Accommodation Type',
                accommodations,
                key='selectbox_symtype')

        year_map_selectbox = st.selectbox(
            'Select Year',
            (2020, 2019, 2018, 2017, 2016, 2015, 2014, 2013, 2012, 2011, 2010),
            key='selectbox_symtype')

        mode_map_selectbox = st.selectbox(
            'Select Time Granularity',
            ("All", "Month", "Seasons"),
            key='selectbox_symtype')

        overallDf = overallDictionary['2020'].copy()
        nationalityDf = nationalityDictionary['2020'].copy()
        categoryDf = categoryDictionary['2020'].copy()

    if year_map_selectbox:
        overallDf = overallDictionary[str(year_map_selectbox)]
        nationalityDf = nationalityDictionary[str(year_map_selectbox)]
        categoryDf = categoryDictionary[str(year_map_selectbox)]

    fig_map_reality = h.generate_map_diagram_reality(
        overallDf, categoryDf, nationalityDf, metric_map_selectbox, spec=spec_map_selectbox, year=year_map_selectbox, mode=mode_map_selectbox, type=mode_cat_nat_selectbox)

    if mode_map_selectbox == "Seasons":
        with mapCol1:
            season_map_selectbox = st.selectbox(
                'Select Season',
                ("Winter", "Spring", "Summer", "Autumn"),
                key='selectbox_symtype')

        if season_map_selectbox:
            fig_map_reality = h.generate_map_diagram_reality(
                overallDf, categoryDf, nationalityDf, metric_map_selectbox, spec=spec_map_selectbox, year=year_map_selectbox, mode=mode_map_selectbox, season=season_map_selectbox, type=mode_cat_nat_selectbox)

    if mode_map_selectbox == "Month":
        with mapCol1:
            month_map_selectbox = st.selectbox(
                'Select Month',
                ("January", "February", "March", "April", "May", "June", "July",
                 "August", "September", "October", "November", "December"),
                key='selectbox_symtype')

        if month_map_selectbox:
            fig_map_reality = h.generate_map_diagram_reality(
                overallDf, categoryDf, nationalityDf, metric_map_selectbox, spec=spec_map_selectbox, year=year_map_selectbox, mode=mode_map_selectbox, month=month_map_selectbox, type=mode_cat_nat_selectbox)

        # Update remaining layout properties
        fig_map_reality.update_layout(
            showlegend=False,
        )

    with mapCol2:

        st.plotly_chart(fig_map_reality, use_container_width=True)

    barCol1, barCol2 = st.columns([1, 5])

    with barCol1:
        st.subheader("Bar view")

        year_bar_selectbox = st.selectbox(
            'Select Year',
            (2020, 2019, 2018, 2017, 2016, 2015, 2014, 2013, 2012, 2011, 2010),
            key='selectbox2_symtype')

        optionsColorList = ['Nationality', 'Distict',
                            'Month', 'Season', 'Accommodation']
        colorOptions = optionsColorList

        x_bar_selectbox = st.selectbox(
            'Select X Metric',
            ('Distict', 'Season', 'Month', 'Nationality', 'Accommodation'),
            key='selectbox2_symtype')

        if x_bar_selectbox == 'Nationality':
            colorOptions = optionsColorList
            colorOptions.remove('Accommodation')
        if x_bar_selectbox == 'Accommodation':
            colorOptions = optionsColorList
            colorOptions.remove('Nationality')

        color_bar_selectbox = st.selectbox(
            'Select Color Metric',
            colorOptions,
            key='selectbox3_symtype')

        overallBarDf = overallDictionary['2020'].copy()
        nationalityBarDf = nationalityDictionary['2020'].copy()
        categoryBarDf = categoryDictionary['2020'].copy()

    if year_bar_selectbox:
        overallBarDf = overallDictionary[str(year_bar_selectbox)]
        nationalityBarDf = nationalityDictionary[str(year_bar_selectbox)]
        categoryBarDf = categoryDictionary[str(year_bar_selectbox)]
        fig_bar_reality = h.on_reality_bar_chart_setup(
            overallBarDf, nationalityBarDf, categoryBarDf, "Arrivals", type=color_bar_selectbox, x=x_bar_selectbox)

    with barCol2:

        fig_bar_reality = h.on_reality_bar_chart_setup(
            overallBarDf, nationalityBarDf, categoryBarDf, "Arrivals", type=color_bar_selectbox, x=x_bar_selectbox)

        st.plotly_chart(fig_bar_reality,
                        use_container_width=True)

    timeCol1, timeCol2 = st.columns([1, 5])

    overallTime = overall.copy()
    nationalityTime = nationality.copy()
    categoryTime = category.copy()

    with timeCol1:

        st.subheader("Time view")

        st.markdown(
            """
<style>
span[data-baseweb="tag"] {
  font-size: 10px;
  white-space: wrap;
  text-overflow: ellipsis;
  width: 100px;
}
</style>
""",
            unsafe_allow_html=True,
        )

        mode = st.selectbox(
            'Trends Visualized',
            ('Total', 'District', 'Nationality', 'Accommodation'),
            key='selectbox_symtype')

        # def onCheckboxChange(type, option):
        #     global choices
        #     choices = choices[choices != option]

        if mode != 'Total':

            if mode == 'District':
                choices = overall['district_i'].unique()
            elif mode == 'Nationality':
                choices = nationality['Nationality'].unique()
            else:
                choices = category['Category'].unique()
            filteredItems = st.multiselect(
                'Displayed items',
                choices,
                [])

    with timeCol2:

        if mode == 'Total':
            time = overallTime.copy()
            time['Day'] = 1
            time['Date'] = pd.to_datetime(time[['Year', 'Month', 'Day']])
            time = time.groupby(['Date']).sum()
            time = time.reset_index()

            time_fig = px.line(time, x="Date", y="Arrivals",
                               title='Total Arrivals', height=700)

        if mode == 'District':
            time = overallTime.copy()
            time['Day'] = 1
            time['Date'] = pd.to_datetime(time[['Year', 'Month', 'Day']])
            time = time[time['district_i'].isin(filteredItems)]

            time_fig = px.line(time, x="Date", y="Arrivals",
                               title='Arrivals by District', color='district_i', height=700)

        if mode == 'Nationality':

            time = nationalityTime.copy()
            time['Day'] = 1
            time['Date'] = pd.to_datetime(time[['Year', 'Month', 'Day']])
            time = time.groupby(['Date', 'Nationality']).sum()
            time = time.reset_index()
            time = time[time['Nationality'].isin(filteredItems)]

            time_fig = px.line(time, x="Date", y="Arrivals",
                               title='Arrivals by Nationality', color='Nationality', height=700)

        if mode == 'Accommodation':

            time = categoryTime.copy()
            time['Day'] = 1
            time['Date'] = pd.to_datetime(time[['Year', 'Month', 'Day']])
            time = time.groupby(['Date', 'Category']).sum()
            time = time.reset_index()
            time = time[time['Category'].isin(filteredItems)]

            time_fig = px.line(time, x="Date", y="Arrivals",
                               title='Arrivals by Accommodation', color='Category', height=700)

        time_fig.update_layout(
            xaxis=dict(
                rangeselector=dict(
                    buttons=list([
                        dict(count=1,
                             label="1m",
                             step="month",
                             stepmode="backward"),
                        dict(count=3,
                             label="3m",
                             step="month",
                             stepmode="backward"),
                        dict(count=6,
                             label="6m",
                             step="month",
                             stepmode="backward"),
                        dict(count=1,
                             label="1y",
                             step="year",
                             stepmode="backward"),
                        dict(step="all")
                    ])
                ),
                rangeslider=dict(
                    visible=True
                ),
                type="date"
            )
        )

        st.plotly_chart(time_fig, use_container_width=True)


#
# SIMULATION LOGIC
#

if st.session_state.mode == h.SIMULATION:

    col1SimMap, col2SimMap = st.columns([1, 5])

    with col1SimMap:
        st.subheader('Map View')

        spec_map_selectbox_sim = "All"

        sim_mode = st.radio(
            "",
            (h.SIM_VIEW, h.SIM_DELTA))

        isDelta = True if sim_mode == h.SIM_DELTA else False

        metric_map_selectbox = st.selectbox(
            'Select Metric:',
            (h.METRIC_ARRIVALS, h.METRIC_AVG_PRESENT,
             h.METRIC_AVG_PRESENT_TO_BEDS, h.METRIC_AVG_PRESENT_TO_POP),
            key='selectbox_symtype')

        mode_map_selectbox_sim = st.selectbox(
            'Select Time Granularity',
            ("All", "Month", "Seasons"),
            key='selectbox_symtype')

        fig_map_simulation = h.generate_map_diagram_simulation(
            isDelta, mode=mode_map_selectbox_sim, metric=metric_map_selectbox)

        if mode_map_selectbox_sim == "Seasons":
            with col1SimMap:
                season_map_selectbox_sim = st.selectbox(
                    'Select Season',
                    ("Winter", "Spring", "Summer", "Autumn"),
                    key='selectbox_symtype')

            if season_map_selectbox_sim:
                fig_map_simulation = h.generate_map_diagram_simulation(
                    isDelta, mode=mode_map_selectbox_sim, season=season_map_selectbox_sim, metric=metric_map_selectbox)

        if mode_map_selectbox_sim == "Month":
            with col1SimMap:
                month_map_selectbox_sim = st.selectbox(
                    'Select Month',
                    ("January", "February", "March", "April", "May", "June", "July",
                     "August", "September", "October", "November", "December"),
                    key='selectbox_symtype')

            if month_map_selectbox_sim:
                fig_map_simulation = h.generate_map_diagram_simulation(
                    isDelta, mode=mode_map_selectbox_sim, month=month_map_selectbox_sim, metric=metric_map_selectbox)

            # Update remaining layout properties
            fig_map_simulation.update_layout(
                showlegend=False,
            )

        with col2SimMap:
            st.plotly_chart(fig_map_simulation, use_container_width=True)

    col1SimBar, col2SimBar = st.columns([1, 5])

    with col1SimBar:
        st.subheader('Bar View')

        sim_mode = st.radio(
            "",
            (h.SIM_COMP, h.SIM_DELTA))

    with col2SimBar:

        if sim_mode == "Comparison View":

            df = st.session_state.arrivals_sim
            df['type'] = "Reality"
            temp = df.copy()
            temp['type'] = "Simulation"
            temp['Arrivals'] = temp['Arrivals_sim']
            df_comparison_real_and_sim = temp.append(df)

            fig_histogram_arrivals_comparison = px.histogram(df_comparison_real_and_sim, x="District", y='Arrivals', color='type', barmode='group', title=f"Comparison in Arrivals for District (Reality / Simulation)",
                                                             color_discrete_sequence=['#fac484', '#5b5399'], height=600, labels={"District": "District",
                                                                                                                                 "Arrivals": "Arrivals"
                                                                                                                                 })
            st.plotly_chart(fig_histogram_arrivals_comparison,
                            use_container_width=True)

        if sim_mode == "Delta View":

            df = st.session_state.arrivals_sim.copy()

            figbar = h.generate_simulation_bar_chart(
                df, y='Diff', title=f'Difference in Arrivals for District (After Simulation)')
            st.plotly_chart(figbar, use_container_width=True)

    col1SimTime, col2SimTime = st.columns([1, 5])

    with col1SimTime:
        st.subheader('Time View')

        mode = st.selectbox(
            'Trends Visualized',
            ('Total', 'District'),
            key='selectbox_symtype')

        st.markdown(
            """
<style>
span[data-baseweb="tag"] {
  font-size: 10px;
  white-space: wrap;
  text-overflow: ellipsis;
  width: 100px;
}
</style>
""",
            unsafe_allow_html=True,
        )

        if mode == "District":
            choices = st.session_state.arrivals_sim['District'].unique()
            filteredItems = st.multiselect(
                'Displayed Districts',
                choices,
                [])

        # always two lines : reality and mocked data :D

    with col2SimTime:
        # temp = overall.copy()['district_i']
        time = st.session_state.arrivals_sim.copy()
        st.session_state.arrivals_sim['type'] = "Reality"
        time['type'] = "Simulation"
        time['Arrivals'] = time['Arrivals_sim']
        time = time.append(st.session_state.arrivals_sim)
        time['Day'] = 1
        time['Date'] = pd.to_datetime(time[['Year', 'Month', 'Day']])

        if mode == "Total":
            totaldf = st.session_state.arrivals_sim.copy()
            totaldf['Day'] = 1
            totaldf['Date'] = pd.to_datetime(totaldf[['Year', 'Month', 'Day']])
            totaldf = totaldf.groupby(['Date']).sum()
            totaldf = totaldf.reset_index()

            time_fig = px.line(totaldf, x="Date", y="Arrivals",
                               title='Total Arrivals', height=700)
        if mode == "District":
            time = time[time['District'].isin(filteredItems)]
            time = time.groupby(['Date', 'type', 'District']).sum()
            time = time.reset_index()
            time['district'] = time['type'] + ' ' + time['District']

            time_fig = px.line(time, x="Date", y="Arrivals",
                               title='Arrivals by District', color='district', height=700)
        time_fig.update_layout(
            xaxis=dict(
                rangeselector=dict(
                    buttons=list([
                        dict(count=1,
                                 label="1m",
                                 step="month",
                                 stepmode="backward"),
                        dict(count=3,
                             label="3m",
                             step="month",
                             stepmode="backward"),
                        dict(count=6,
                             label="6m",
                             step="month",
                             stepmode="backward"),
                        dict(step="all")
                    ])
                ),
                rangeslider=dict(
                    visible=True
                ),
                type="date"
            )
        )
        st.plotly_chart(time_fig, use_container_width=True)
