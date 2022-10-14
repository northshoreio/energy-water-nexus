import streamlit as st

st.set_page_config(
    page_title="Home",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "https://github.com/northshoreio",
        "Get help": "mailto:hello@northshore.io"
    }
)

st.sidebar.info('Copyright © 2022 [Northshore IO Inc](https://northshore.io/)')
st.sidebar.image('northshore.png')

st.header("Energy-Water-Nexus")
st.subheader('Exploring interactions between energy- and water-consumption in data centers.')

st.markdown(
    "> *This is a high-level energy- and water-modeling application designed for rapid, iterative feedback in "
    "understanding the impacts of equipment design and operating characteristics on data center sustainability.*"
)
st.markdown("""
    - Use the **🌤️ Weather** page to fetch weather data used for analysis.
    - Input all design and operational characteristics in the **🏢 Design** page.
    - Analyze energy- and water-performance for your model on the **🔌 Performance 💧** page.
""")


st.markdown(
    "> *The following mechanical system archetypes are currently implemented:*"
)
with st.container():

    st.subheader('Water-Cooled-Chiller')
    st.markdown("> *Schematic of a typical chilled-water system.*")
    st.text(' ')
    st.text(' ')
    st.image(
        image='https://www.researchgate.net/profile/John-Seem-2/publication/261281692/figure/fig1/AS:392537647927305'
              '@1470599676604/Schematic-of-a-typical-chilled-water-system.png',
        caption='Li, Xiao & Li, Yaoyu & Seem, John & Li, Pengfei. (2012). '
                'Extremum seeking control of cooling tower for self-optimizing efficient operation of chilled water '
                'systems. Proceedings of the American Control Conference. 3396-3401. 10.1109/ACC.2012.6315202. ',
        width=600
    )
