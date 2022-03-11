import streamlit as st
import numpy as np
import plotly.express as px
import geopandas as gp
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
    municipalities, municipalities_sim = helper.load_data()


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


geo_df = municipalities.copy()
geo_df['arrivi_tot_log'] = np.log(geo_df['arrivi_tot'])
geo_df['arrivi_prob'] = geo_df['arrivi_tot'] / \
    municipalities['arrivi_tot'].sum()
geo_df = geo_df.sort_values('arrivi_prob', ascending=False)

# Mock nationality and other data
geo_df = helper.mock_nationalities(geo_df)

# Min-Max values to be used for plotting
vmin = geo_df['arrivi_tot'].min()
vmax = geo_df['arrivi_tot'].max() * .5


#
# Simulation recommend top-n
#

pop_size = int(geo_df['arrivi_tot'].sum())
top_n = 30
top_n_items = geo_df['PRO_COM'][:top_n]


@st.cache(allow_output_mutation=True)
def make_choice(recs, p_recs, lbl):
    lbl = lbl.split('__')[0]
    df = geo_df.copy()
    choices_decay = 1/(np.log(np.arange(top_n)+1)+1)
    choices_p = choices_decay/choices_decay.sum()

    choices_alone = np.random.choice(df['PRO_COM'], int(
        pop_size * (1-p_recs)), p=df['arrivi_prob'])
    choices_system = np.random.choice(
        recs, int(pop_size * p_recs), p=choices_p)

    simulation_topn = Counter(np.hstack([choices_alone, choices_system]))
    df[f'{lbl}'] = 0
    df[f'{lbl}'] = df['PRO_COM'].map(lambda x: simulation_topn.get(x))
    return df


@st.cache(allow_output_mutation=True)
def make_choice_topn(n, lbl):

    lbl = lbl.split('__')[0]
    df = geo_df.copy()
    list_size = df.shape[0]

    choices_decay = 1/(np.log(np.arange(1, list_size+1))+1)
    choices_p = choices_decay/choices_decay.sum()

    top_n_items = df['PRO_COM'][:n]

    municipalities_sim_topn = municipalities_sim.loc[top_n_items]
    candidates = [int(c) for c in municipalities_sim_topn.mean(axis=0).sort_values(
        ascending=False).index.to_list()]

    choices_system = np.random.choice(candidates, int(pop_size), p=choices_p)
    simulation_topn = Counter(choices_system)
    df[f'{lbl}'] = 0
    df[f'{lbl}'] = df['PRO_COM'].map(lambda x: simulation_topn.get(x, 1))
    return df


fig_map_reality = helper.generate_map_diagram(
    geo_df, 'arrivi_tot', vmin, vmax, "Arrival Map (Reality)")
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
        'Number of Municipalities Visualised:',
        (5, 10, 15, 20, 25, 30, 35, 40, 45, 50),
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

        df = geo_df[['COMUNE', 'PRO_COM', 'arrivi_tot',
                     'germans', 'italians', 'americans', 'others']].copy()

        fig_reality_arrival_bar_by_nationality = helper.on_reality_bar_chart_setup(
            df, number_of_municipalities, order_municipalities)
        # create REALITY arrival bar by nationality
        st.plotly_chart(fig_reality_arrival_bar_by_nationality,
                        use_container_width=True)


#
# SIMULATION LOGIC
#

if st.session_state.mode == helper.SIMULATION:

    number_mun = number_of_municipalities if number_of_municipalities else 5
    order_mun = True if order_municipalities == "Ascending" else False

    with col1:

        if simulation_type == helper.SIM_TYPE_TOPN:
            comparison_target = 'sim_arrivi_topn'
            df_sim = make_choice(top_n_items, p_rec,
                                 lbl=comparison_target+'__'+str(st.session_state.nclick))
            df = df_sim[['COMUNE', 'PRO_COM', 'arrivi_tot',
                         'sim_arrivi_topn', 'letti_nr']].copy()
        else:
            comparison_target = 'sim_arrivi_simtopn'
            df_sim = make_choice_topn(
                option_N, lbl=comparison_target+'__'+str(st.session_state.nclick))
            df = df_sim[['COMUNE', 'PRO_COM', 'arrivi_tot',
                         'sim_arrivi_simtopn', 'letti_nr']].copy()

        # GENERATE MAP DIAGRAM
        if simulation_mode == helper.SIM_ONLY_VIEW:
            fig_map_arrivals_simulated_topn = helper.generate_map_diagram(
                df_sim, comparison_target,  vmin, vmax, "Arrival Map (Simulation)")
        elif simulation_mode == helper.SIM_SIDE_BY_SIDE:
            fig_map_arrivals_simulated_topn = fig_map_reality
        else:
            fig_map_arrivals_simulated_topn = helper.generate_map_diagram(
                df_sim, comparison_target,  vmin, vmax, "Arrival Map (Delta)", isDelta=True)

        st.plotly_chart(fig_map_arrivals_simulated_topn,
                        use_container_width=True)

        df['diff'] = df[comparison_target] - df['arrivi_tot']
        df.sort_values('arrivi_tot', inplace=True, ascending=order_mun)

        df_comparison_real_and_sim = df.copy()
        df_comparison_real_and_sim = df_comparison_real_and_sim.head(
            number_mun)

        df_comparison_real_and_sim = helper.mock_nationalities(
            df_comparison_real_and_sim)

        temp = df_comparison_real_and_sim.copy()
        df_comparison_real_and_sim['type'] = "Reality"
        temp['type'] = "Simulation"
        temp['arrivi_tot'] = temp[comparison_target]
        df_comparison_real_and_sim = df_comparison_real_and_sim.append(temp)
        df_comparison_real_and_sim['density'] = df_comparison_real_and_sim['arrivi_tot'] / \
            df_comparison_real_and_sim['letti_nr']

    with col2:

        if simulation_mode == helper.SIM_SIDE_BY_SIDE:
            fig_map_arrivals_simulated_topn = helper.generate_map_diagram(
                df_sim, comparison_target,  vmin, vmax, "Arrival Map (Simulation)")
            st.plotly_chart(fig_map_arrivals_simulated_topn,
                            use_container_width=True)

        diff_df = df.head(number_mun)
        fig_simulation_bar_chart = helper.generate_simulation_bar_chart(
            diff_df, comparison_target)
        st.plotly_chart(fig_simulation_bar_chart, use_container_width=True)

        fig_histogram_arrivals_comparison = px.histogram(
            df_comparison_real_and_sim, x="COMUNE", y="arrivi_tot", color='type', barmode='group', title="Change in Arrivals for Municipality (Histogram)",
            color_discrete_sequence=px.colors.sequential.Viridis, height=600, labels={"COMUNE": "Municipality",
                                                                                      "arrivi_tot": "Arrivals"
                                                                                      })
        if simulation_mode != helper.SIM_SIDE_BY_SIDE:
            st.plotly_chart(fig_histogram_arrivals_comparison,
                            use_container_width=True)

    with col1:

        fig_slope_chart = px.line(
            df_comparison_real_and_sim, height=600, title="Change in Arrivals for Municipality (Slope Chart)", x="type", y="arrivi_tot", color='COMUNE', symbol="COMUNE", labels={"COMUNE": "Municipality",
                                                                                                                                                                                  "arrivi_tot": "Arrivals", "type": "Reality vs Simulation"})

        st.plotly_chart(fig_slope_chart, use_container_width=True)

    if simulation_mode == helper.SIM_SIDE_BY_SIDE:
        st.plotly_chart(fig_histogram_arrivals_comparison,
                        use_container_width=True)
