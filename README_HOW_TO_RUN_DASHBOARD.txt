# CA2 Online Retail Dashboard Package

## What is inside

- `notebooks/CA2_ML_DV_NOTEBOOK_CORRECTED.ipynb`
- `data/Online Retail.xlsx`
- `dashboard/senior_dashboard_app.py`
- `outputs/` folder, where the notebook will save CSV files
- `requirements.txt`

## Step 1: Install libraries

Open Terminal / Anaconda Prompt in this folder and run:

```bash
pip install -r requirements.txt
```

If you use Jupyter and mlxtend gives an error, run this inside a notebook cell:

```python
%pip install mlxtend
```

## Step 2: Run the notebook

Open:

```bash
jupyter notebook notebooks/CA2_ML_DV_NOTEBOOK_CORRECTED.ipynb
```

Run all cells from top to bottom.

The notebook creates the files used by the dashboard in the `outputs` folder.

## Step 3: Open the dashboard

In Terminal / Anaconda Prompt, stay in the main project folder and run:

```bash
streamlit run dashboard/senior_dashboard_app.py
```

A browser window should open automatically.

If it does not open, copy the local URL shown in the terminal, usually:

```text
http://localhost:8501
```

## What to submit on Moodle

Upload separately:

1. Word report
2. Jupyter notebook
3. Dataset
4. Dashboard file or exported dashboard evidence/screenshots
5. Supporting files
6. GitHub link with at least 5 commits
