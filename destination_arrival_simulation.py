import streamlit as st
import numpy as np
import plotly.express as px
import geopandas as gp
import pandas as pd
from collections import Counter
import helper

#
# SETUP STATE
#

helper.setup_state()


#
# SETUP HEADER
#

st.set_page_config(layout='wide')


col1top, col2top = st.columns([5, 1])

with col1top:
    st.title('Tourist Trends in South Tyrol')
with col2top:
    get_reality_view_btn = st.button(
        "Reality view", on_click=helper.get_view, disabled=st.session_state.mode == helper.REALITY)

with st.spinner('Loading data...'):
    municipalities, municipalities_sim, districts, nationality, category, overall, districts_sim = helper.load_data()


with st.expander("Tourism data"):
    """
    The chart shows tourists arrivals in South Tyrol municipalities for the year 2019.
    In total were counted 4,619,064 tourists in the whole region.
    """


#
# SETUP SIDEBAR
#

simulation_type = st.sidebar.selectbox(
    'Which marketing campaign do you want to test?',
    (helper.SIM_TYPE_TOPN, helper.SIM_TYPE_SIMILAR_TOPN),
    key='selectbox_symtype')

if simulation_type == helper.SIM_TYPE_SIMILAR_TOPN:
    option_N = st.sidebar.selectbox(
        'Size of N:',
        (5, 10, 20, 30, 40, 50),
        key='selectbox_N_size')

simulation_mode = st.sidebar.selectbox(
    'How would you like to visualize the map results?',
    (helper.SIM_ONLY_VIEW, helper.SIM_DELTA, helper.SIM_SIDE_BY_SIDE),
    key='selectbox_symtype')

run_simulation_btn = st.sidebar.button(
    "Run", on_click=helper.on_run_simulation_btn_click, disabled=simulation_type is None)



districts_sim = overall.copy()
districts_sim['sim_arrivals'] = np.random.permutation(overall["Arrivals"].values)
districts_sim['sim_present'] = np.random.permutation(overall['Present'].values)
districts_sim['diff'] = districts_sim['Arrivals'] - districts_sim['sim_arrivals']





fig_map_reality = helper.generate_map_diagram(
    overall, 'Arrivals', "Arrival Map (Reality)")

fig_map_sim = helper.generate_map_diagram(
    districts_sim, 'sim_arrivals', "Arrival Map (Simulated)")
p_rec = 0.


#
# ADD REALITY / SIMULATION HEADER
#

if st.session_state.mode == helper.REALITY:
    st.header("Reality")
else:
    st.header("Simulation")

#
# ADD SETTING DROPDOWNS
#

col1, col2 = st.columns(2)
with col1:
    number_of_municipalities = st.selectbox(
        'Number of Districts Visualised:',
        # (5, 10, 15, 20, 25, 30, 35, 40, 45, 50),
        (8, 8),
        key='selectbox_num_municipalities')

with col2:

    order_municipalities = st.selectbox(
        'Order by (Real Arrivals):',
        ("Descending", "Ascending"),
        key='selectbox_order_municipalities')

#
# REALITY LOGIC
#

if st.session_state.mode == helper.REALITY:

    with col1:

        # create REALITY arrival map
        st.plotly_chart(fig_map_reality, use_container_width=True)

    with col2:

        fig_reality_arrival_bar_by_nationality = helper.on_reality_bar_chart_setup(
            nationality, number_of_municipalities, order_municipalities)
        # create REALITY arrival bar by nationality
        st.plotly_chart(fig_reality_arrival_bar_by_nationality,
                        use_container_width=True)

        
        fig_reality_arrival_bar_by_category = helper.on_reality_bar_chart_setup(
            category, number_of_municipalities, order_municipalities, "Category")
        # create REALITY arrival bar by nationality
        st.plotly_chart(fig_reality_arrival_bar_by_category,
                        use_container_width=True)



#
# SIMULATION LOGIC
#

if st.session_state.mode == helper.SIMULATION:

    number_mun = number_of_municipalities if number_of_municipalities else 8 #5
    order_mun = True if order_municipalities == "Ascending" else False

    with col1:

        if simulation_type == helper.SIM_TYPE_TOPN:
            comparison_target = 'sim_arrivals'
            # df_sim = make_choice(top_n_items, p_rec,
            #                      lbl=comparison_target+'__'+str(st.session_state.nclick))
            # df = df_sim[['COMUNE', 'PRO_COM', 'arrivi_tot',
            #              'sim_arrivi_topn', 'letti_nr']].copy()
        else:
            comparison_target = 'sim_arrivals'
            # df_sim = make_choice_topn(
            #     option_N, lbl=comparison_target+'__'+str(st.session_state.nclick))
            # df = df_sim[['COMUNE', 'PRO_COM', 'arrivi_tot',
            #              'sim_arrivi_simtopn', 'letti_nr']].copy()

        # GENERATE MAP DIAGRAM
        if simulation_mode == helper.SIM_ONLY_VIEW:
            fig_map_arrivals_simulated_topn = helper.generate_map_diagram(
                districts_sim, comparison_target,  "Arrival Map (Simulation)")
        elif simulation_mode == helper.SIM_SIDE_BY_SIDE:
            fig_map_arrivals_simulated_topn = fig_map_reality
        else:
            fig_map_arrivals_simulated_topn = helper.generate_map_diagram(
                districts_sim, comparison_target, "Arrival Map (Delta)", isDelta=True)

        st.plotly_chart(fig_map_arrivals_simulated_topn,
                        use_container_width=True)


        districts_sim.sort_values('Arrivals', inplace=True, ascending=order_mun)


        temp = districts_sim.copy()
        districts_sim['type'] = "Reality"
        temp['type'] = "Simulation"
        temp['Arrivals'] = temp[comparison_target]
        df_comparison_real_and_sim = districts_sim.append(temp)


    with col2:

        if simulation_mode == helper.SIM_SIDE_BY_SIDE:
            fig_map_arrivals_simulated_topn = helper.generate_map_diagram(
                districts_sim, comparison_target, "Arrival Map (Simulation)")
            st.plotly_chart(fig_map_arrivals_simulated_topn,
                            use_container_width=True)

        diff_df = districts_sim.head(number_mun)
        fig_simulation_bar_chart = helper.generate_simulation_bar_chart(
            diff_df, comparison_target)
        st.plotly_chart(fig_simulation_bar_chart, use_container_width=True)

        fig_histogram_arrivals_comparison = px.histogram(
            df_comparison_real_and_sim, x="district_i", y="Arrivals", color='type', barmode='group', title="Change in Arrivals for District (Histogram)",
            color_discrete_sequence=['#440154',  '#22938B'], height=600, labels={"district_i": "District",
                                                                                 "Arrivals": "Arrivals"
                                                                                 })
        if simulation_mode != helper.SIM_SIDE_BY_SIDE:
            st.plotly_chart(fig_histogram_arrivals_comparison,
                            use_container_width=True)

    with col1:

        fig_slope_chart = px.line(
            df_comparison_real_and_sim, height=600, title="Change in Arrivals for Municipality (Slope Chart)", x="type", y="Arrivals", color='district_i', symbol="district_i", labels={"district_i": "District",
                                                                                                                                                                                  "Arrivals": "Arrivals", "type": "Reality vs Simulation"})

        st.plotly_chart(fig_slope_chart, use_container_width=True)

    if simulation_mode == helper.SIM_SIDE_BY_SIDE:
        st.plotly_chart(fig_histogram_arrivals_comparison,
                        use_container_width=True)
