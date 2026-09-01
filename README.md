# Fusion21 Social Need Explorer

Streamlit prototype for comparing public social need across the nine English regions and exploring how recorded Fusion21 contribution measures could be viewed alongside need.

## Important data note

The deprivation and unemployment indicators use public data. All Fusion21 contract, activity and Foundation records in this repository are synthetic demonstration data. They test the pipeline and interface; they do not evaluate Fusion21's real performance or prove social impact.

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
