import pandas as pd
import streamlit as st
import config
from src import db, predict


st.set_page_config(page_title="Arbetsmarknad och handel")

page = st.sidebar.radio("Meny", ["Prediktera", "Historik", "Modell", "Data", "Om projektet"])

st.title("Arbetsmarknad och handel")

if page == "Prediktera":
    st.header("Prediktera")
    bundle = predict.load_model()
    features = db.read_table(config.FEATURES_TABLE)
    senaste = features.iloc[-1]

    beskrivningar = {
        "export_varor_t1": "Export av varor för 1 månad sedan (mnkr)",
        "export_varor_t3": "Export av varor för 3 månader sedan (mnkr)",
        "export_varor_t6": "Export av varor för 6 månader sedan (mnkr)",
        "import_varor_t1": "Import av varor för 1 månad sedan (mnkr)",
        "import_varor_t3": "Import av varor för 3 månader sedan (mnkr)",
        "import_varor_t6": "Import av varor för 6 månader sedan (mnkr)",
        "export_tjanster_t1": "Export av tjänster för 1 månad sedan (mnkr per kvartal)",
        "export_tjanster_t3": "Export av tjänster för 3 månader sedan (mnkr per kvartal)",
        "export_tjanster_t6": "Export av tjänster för 6 månader sedan (mnkr per kvartal)",
        "import_tjanster_t1": "Import av tjänster för 1 månad sedan (mnkr per kvartal)",
        "import_tjanster_t3": "Import av tjänster för 3 månader sedan (mnkr per kvartal)",
        "import_tjanster_t6": "Import av tjänster för 6 månader sedan (mnkr per kvartal)",
        "arbetsloshet_t1": "Arbetslöshet förra månaden (%)",
    }

    st.write("Välj värden och tryck på Prediktera. Modellen förutsäger arbetslösheten den här månaden utifrån handeln de senaste månaderna och arbetslösheten förra månaden.")
    st.write("Startvärdena kommer från " + senaste["period"] + ". Tjänstehandeln finns bara per kvartal och avser det senast avslutade kvartalet.")

    with st.form("test"):
        indata = {}
        for kolumn in bundle["numeric_cols"]:
            if kolumn == config.TARGET_SERIES + "_t1":
                indata[kolumn] = st.slider(
                    beskrivningar[kolumn],
                    min_value=float(features[kolumn].min()),
                    max_value=float(features[kolumn].max()),
                    value=float(senaste[kolumn]),
                    step=0.1
                )
            else:
                minsta = int(features[kolumn].min() / 10000) * 10000
                storsta = int(features[kolumn].max() / 10000) * 10000 + 10000
                varde = round(senaste[kolumn] / 10000) * 10000
                indata[kolumn] = st.slider(
                    beskrivningar[kolumn],
                    min_value=minsta,
                    max_value=storsta,
                    value=varde,
                    step=10000
                )

        manader = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]
        indata[config.SEASON_FEATURE] = st.selectbox(
            "Månad som ska förutsägas (01 = januari, 12 = december)",
            manader,
            index=manader.index(senaste[config.SEASON_FEATURE])
        )

        skicka = st.form_submit_button("Prediktera")

    if skicka:
        prediktion = predict.predict_one(bundle, indata)
        st.write("Predikterad arbetslöshet: " + str(round(prediktion, 2)) + " %")


elif page == "Data":
    st.header("Data")
    tabell = st.selectbox("Välj tabell", db.list_tables())
    st.dataframe(db.read_table(tabell), hide_index=True)

elif page == "Historik":
    st.header("Historik")
    merged = db.read_table(config.MERGED_TABLE)

    st.subheader("Export och import av varor (mnkr)")
    st.line_chart(merged, x="period", y=["export_varor", "import_varor"])

    st.subheader("Arbetslöshet (%)")
    st.line_chart(merged, x="period", y="arbetsloshet")

elif page == "Modell":
    st.header("Modell")
    metrics = predict.load_metrics()
    bundle = predict.load_model()

    st.write("Bästa modell: " + bundle["model_name"])

    rader = []
    for namn in metrics:
        rader.append({
            "Modell": namn,
            "MAE": round(metrics[namn]["mae"], 3),
            "RMSE": round(metrics[namn]["rmse"], 3),
            "R²": round(metrics[namn]["r2"], 3),
        })
    st.dataframe(pd.DataFrame(rader), hide_index=True)

    st.subheader("Faktisk arbetslöshet och prediktion")
    test = db.read_table(config.TEST_PREDICTIONS_TABLE)
    test = test[test["modell"] == bundle["model_name"]]
    st.line_chart(test, x="period", y=["faktiskt", "prediktion"])


elif page == "Om projektet":
    st.header("Om projektet")
    st.write("Kan förändringar i Sveriges export och import av varor och tjänster prediktera arbetslösheten några månader senare?")
    st.write("Data från SCB: utrikeshandel med varor (TAB1644), utrikeshandel med tjänster (TAB5147) och arbetskraftsundersökningen (TAB6387), från 2005 och framåt.")
    st.write("Handelns värden 1, 3 och 6 månader tidigare används som features. Modellen tränas på data till och med 2022 och testas på perioden därefter.")
    st.write("Källa: SCB")
