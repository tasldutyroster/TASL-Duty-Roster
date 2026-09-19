@echo off
start chrome http://localhost:8501
python -m streamlit run app.py --server.headless true
pause