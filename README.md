# Fusion21 Social Need Explorer

Streamlit prototype for comparing public social need across the nine English regions and exploring how recorded Fusion21 contribution measures could be viewed alongside need.

## Important data note

The deprivation and unemployment indicators use public data. All Fusion21 contract, activity and Foundation records in this repository are synthetic demonstration data. They test the pipeline and interface; they do not evaluate Fusion21's real performance or prove social impact.

The public need view retains the observed inputs rather than converting nine
regions to a 0-100 Min-Max scale. The exploratory index is calculated as:

```text
(population-weighted mean IMD score + regional unemployment rate) / 2
```

The inputs have different units and numerical ranges. The result is therefore a
simple descriptive index, not a percentage, an official regional statistic or a
claim that the two concepts have equal influence.

## Run locally

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Deploy on Streamlit Community Cloud

1. Connect this GitHub repository to Streamlit Community Cloud.
2. Select `app.py` as the entrypoint.
3. Select Python 3.12.
4. Keep the app private and invite Fusion21 reviewers by email unless public access has been approved.

The repository includes the processed data required at startup, so the application does not need to rebuild the public-data pipeline before loading.
