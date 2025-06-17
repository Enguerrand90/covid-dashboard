import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests

# --- Style ---

def set_theme(dark_mode: bool):
    if dark_mode:
        css = """
        <style>
        body, .main, .block-container {
            background-color: #0e1117;
            color: white;
        }
        a {
            color: #1e90ff;
        }
        .js-plotly-plot .plotly {
            background-color: #0e1117 !important;
        }
        </style>
        """
    else:
        css = """
        <style>
        body, .main, .block-container {
            background-color: white;
            color: black;
        }
        a {
            color: #1e90ff;
        }
        </style>
        """
    st.markdown(css, unsafe_allow_html=True)

def style_fig(fig, dark_mode):
    font_color = "white" if dark_mode else "black"
    bg_color = "#0e1117" if dark_mode else "white"
    fig.update_layout(
        paper_bgcolor=bg_color,
        plot_bgcolor=bg_color,
        font=dict(color=font_color),
        title_font_color=font_color,
        xaxis=dict(color=font_color, showgrid=True, gridcolor='gray'),
        yaxis=dict(color=font_color, showgrid=True, gridcolor='gray'),
        legend=dict(font=dict(color=font_color)),
        margin=dict(l=40, r=40, t=60, b=40)
    )
    if "annotations" in fig.layout:
        for annotation in fig.layout.annotations:
            annotation.font.color = font_color
    return fig

# --- France data loading via API ---
@st.cache_data
def load_france_data(dept="All", start_date=None, end_date=None):
    params = {"dept": dept}
    if start_date:
        params["start_date"] = str(start_date)
    if end_date:
        params["end_date"] = str(end_date)
    try:
        response = requests.get("http://127.0.0.1:8000/data", params=params)
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data)
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
        return df
    except Exception as e:
        st.error(f"API request failed: {e}")
        return pd.DataFrame()

# --- USA data loading ---
@st.cache_data
def load_usa_data():
    url = "https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-states.csv"
    df = pd.read_csv(url, parse_dates=["date"])
    state_abbr = {
        'Alabama':'AL','Alaska':'AK','Arizona':'AZ','Arkansas':'AR','California':'CA','Colorado':'CO',
        'Connecticut':'CT','Delaware':'DE','Florida':'FL','Georgia':'GA','Hawaii':'HI','Idaho':'ID',
        'Illinois':'IL','Indiana':'IN','Iowa':'IA','Kansas':'KS','Kentucky':'KY','Louisiana':'LA',
        'Maine':'ME','Maryland':'MD','Massachusetts':'MA','Michigan':'MI','Minnesota':'MN',
        'Mississippi':'MS','Missouri':'MO','Montana':'MT','Nebraska':'NE','Nevada':'NV',
        'New Hampshire':'NH','New Jersey':'NJ','New Mexico':'NM','New York':'NY','North Carolina':'NC',
        'North Dakota':'ND','Ohio':'OH','Oklahoma':'OK','Oregon':'OR','Pennsylvania':'PA',
        'Rhode Island':'RI','South Carolina':'SC','South Dakota':'SD','Tennessee':'TN','Texas':'TX',
        'Utah':'UT','Vermont':'VT','Virginia':'VA','Washington':'WA','West Virginia':'WV',
        'Wisconsin':'WI','Wyoming':'WY','District of Columbia':'DC'
    }
    df["abbr"] = df["state"].map(state_abbr)
    return df

# --- France Dashboard ---
def france_dashboard(dark_mode):
    st.title("COVID-19 France Interactive Dashboard")

    df_all = load_france_data()
    min_date = df_all['date'].min() if not df_all.empty else pd.to_datetime("2020-01-01")
    max_date = df_all['date'].max() if not df_all.empty else pd.to_datetime("today")

    if "date_range_fr" not in st.session_state:
        st.session_state.date_range_fr = (min_date, max_date)

    if st.sidebar.button("Reset Filters France"):
        st.session_state.date_range_fr = (min_date, max_date)

    date_range = st.sidebar.date_input(
        "Select date range (France)",
        value=st.session_state.date_range_fr,
        min_value=min_date,
        max_value=max_date,
        key="date_range_input_fr"
    )

    st.session_state.date_range_fr = date_range if isinstance(date_range, (tuple, list)) else (date_range, date_range)
    start_date, end_date = st.session_state.date_range_fr

    filtered_df = load_france_data(start_date=start_date, end_date=end_date)

    csv_data = filtered_df.to_csv(index=False).encode('utf-8')
    st.sidebar.markdown("### Export Data (France)")
    st.sidebar.download_button(
        label="Download filtered data as CSV (France)",
        data=csv_data,
        file_name='covid_data_france_filtered.csv',
        mime='text/csv'
    )

    st.markdown(f"### Showing data from **{start_date}** to **{end_date}** (France)")

    if not filtered_df.empty:
        df_agg = filtered_df.groupby("date", as_index=False)["incid_hosp"].sum()
        fig1 = px.line(df_agg, x="date", y="incid_hosp", title="Daily Hospital Admissions (France)", labels={"incid_hosp": "Admissions"})
        if dark_mode:
            fig1 = style_fig(fig1, dark_mode)
        st.plotly_chart(fig1, use_container_width=True)

        # Carte choropleth France par départements
        df_dep = filtered_df.groupby("dep_str", as_index=False).agg({"incid_hosp": "sum"})
        if not df_dep.empty:
            geojson_url = "https://france-geojson.gregoiredavid.fr/repo/departements.geojson"
            geojson = requests.get(geojson_url).json()
            fig_map = px.choropleth(
                df_dep,
                geojson=geojson,
                locations="dep_str",
                color="incid_hosp",
                featureidkey="properties.code",
                scope="europe",
                title="Hospital Admissions by Department (France)"
            )
            fig_map.update_geos(visible=False, fitbounds="locations")
            if dark_mode:
                fig_map = style_fig(fig_map, dark_mode)
            st.plotly_chart(fig_map, use_container_width=True)

        metric_labels = {
            'incid_hosp': 'New Hospital Admissions',
            'incid_rea': 'New ICU Admissions',
            'incid_dc': 'New Deaths'
        }
        df_metrics = filtered_df.groupby("date", as_index=False)[list(metric_labels.keys())].sum()
        df_metrics = df_metrics.rename(columns=metric_labels)
        fig3 = px.line(df_metrics, x='date', y=list(metric_labels.values()), title="Key Metrics Over Time (France)")
        if dark_mode:
            fig3 = style_fig(fig3, dark_mode)
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.warning("No data available for the selected filters.")

# --- USA Dashboard ---
def usa_dashboard(dark_mode):
    st.title("COVID-19 USA Interactive Dashboard")

    df = load_usa_data()

    min_date = df["date"].min()
    max_date = df["date"].max()

    if "date_range_usa" not in st.session_state:
        st.session_state.date_range_usa = (min_date, max_date)

    if st.sidebar.button("Reset Filters USA"):
        st.session_state.date_range_usa = (min_date, max_date)

    date_range = st.sidebar.date_input(
        "Select date range (USA)",
        value=st.session_state.date_range_usa,
        min_value=min_date,
        max_value=max_date,
        key="date_range_input_usa"
    )

    st.session_state.date_range_usa = date_range if isinstance(date_range, (tuple, list)) else (date_range, date_range)

    start_date, end_date = st.session_state.date_range_usa
    start_date = pd.Timestamp(start_date)
    end_date = pd.Timestamp(end_date)

    df_filtered = df[(df["date"] >= start_date) & (df["date"] <= end_date)]

    df_nat = df_filtered.groupby("date", as_index=False).agg({"cases": "sum", "deaths": "sum"})
    df_nat["new_cases"] = df_nat["cases"].diff().fillna(0)
    df_nat["new_deaths"] = df_nat["deaths"].diff().fillna(0)
    df_nat["cases_7d"] = df_nat["new_cases"].rolling(7).mean()
    df_nat["deaths_7d"] = df_nat["new_deaths"].rolling(7).mean()

    csv_data = df_filtered.to_csv(index=False).encode('utf-8')
    st.sidebar.markdown("### Export Data (USA)")
    st.sidebar.download_button(
        label="Download filtered data as CSV (USA)",
        data=csv_data,
        file_name='covid_data_usa_filtered.csv',
        mime='text/csv'
    )

    st.markdown(f"### Showing data from **{start_date.date()}** to **{end_date.date()}** (USA)")

    fig1 = px.line(df_nat, x="date", y="new_cases",
                   title="Daily New COVID-19 Cases in the U.S.",
                   labels={"new_cases": "New Cases", "date": "Date"})
    fig1.update_layout(showlegend=False, title_x=0.02, height=400)
    fig1.update_traces(hovertemplate="%{y:,.0f}")
    if dark_mode:
        fig1 = style_fig(fig1, dark_mode)
    st.plotly_chart(fig1, use_container_width=True)

    latest = df_filtered[df_filtered["date"] == df_filtered["date"].max()]
    fig2 = px.choropleth(
        latest,
        locations="abbr",
        locationmode="USA-states",
        color="cases",
        hover_name="state",
        scope="usa",
        color_continuous_scale="OrRd",
        title="Total COVID-19 Cases by State (Latest)",
        labels={"cases": "Total Cases"}
    )
    fig2.update_layout(title_x=0.02, height=500)
    fig2.update_traces(hovertemplate="<b>%{hovertext}</b><br>Total Cases: %{z:,.0f}")
    if dark_mode:
        fig2 = style_fig(fig2, dark_mode)
    st.plotly_chart(fig2, use_container_width=True)

    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        x=df_nat["date"],
        y=df_nat["cases_7d"],
        name="7-day Avg. New Cases",
        line=dict(color="steelblue", width=2),
        hovertemplate="%{y:,.0f}"
    ))
    fig3.add_trace(go.Scatter(
        x=df_nat["date"],
        y=df_nat["deaths_7d"],
        name="7-day Avg. Deaths",
        line=dict(color="firebrick", width=2),
        yaxis="y2",
        hovertemplate="%{y:,.0f}"
    ))
    fig3.update_layout(
        title="7-Day Average of New Cases and Deaths",
        xaxis=dict(title="Date"),
        yaxis=dict(title="New Cases"),
        yaxis2=dict(title="New Deaths", overlaying="y", side="right"),
        legend=dict(x=0.01, y=0.99),
        height=400,
        title_x=0.02
    )
    if dark_mode:
        fig3 = style_fig(fig3, dark_mode)
    st.plotly_chart(fig3, use_container_width=True)

# --- Info France ---
def info_france():
    st.title("Info & Key Dates (France)")

    st.markdown("""
    ### National Key Dates

    - **March 17, 2020**: First national lockdown in France  
    - **May 11, 2020**: End of first lockdown  
    - **December 27, 2020**: Start of vaccination campaign  
    - **April 3, 2021**: Localized lockdown in Île-de-France  
    - **May 19, 2021**: Gradual lifting of restrictions  
    - **Summer 2021**: Vaccination campaign extended to all adults  
    """)

# --- Info USA ---
def info_usa():
    st.title("Info & Key Dates (USA)")

    st.markdown("""
    ### National Key Dates

    - **March 13, 2020**: National emergency declared  
    - **April 2020**: Peak of first wave in many states  
    - **December 14, 2020**: Vaccination campaign started  
    - **January 2021**: Surge due to variants  
    - **Summer 2021**: Delta variant wave  
    - **Winter 2021/2022**: Omicron variant wave  
    """)

# --- About Us Page ---
def info_page():
    st.title("About Us")
    st.markdown("""
    Here is the application working with a REST API.

    **BORNY Raphael and RENON Enguerrand worked on it together (Neptun IDs: ANDS5M, EKV6BU).**

    We are both Erasmus students here, so we studied all the assignments together and believed that making an app together made sense.

    To accomplish that, we used GitHub as a way to work directly at the same time.

    This app is a combination of our works on the assignment: Interactive Visualization.

    Hope you like it! :)
    """)

# --- Main ---

st.set_page_config(page_title="COVID-19 Dashboard", layout="wide")

dark_mode = st.sidebar.checkbox("Dark Mode", value=True)  # dark mode par défaut
set_theme(dark_mode)

country = st.sidebar.selectbox("Select Country", ["France", "USA"])

page = st.sidebar.radio("Navigation", ["Dashboard", "Info", "About Us"])

if page == "Dashboard":
    if country == "France":
        france_dashboard(dark_mode)
    elif country == "USA":
        usa_dashboard(dark_mode)
elif page == "Info":
    if country == "France":
        info_france()
    elif country == "USA":
        info_usa()
elif page == "About Us":
    info_page()
