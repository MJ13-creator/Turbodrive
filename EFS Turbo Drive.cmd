@echo off
cd /d %~dp0

call venv\Scripts\activate

python -m pip install streamlit-echarts
python -m streamlit run model.py

pause