\# 🩺 Clinical Trial Adverse Event Safety Monitor



\[!\[Python 3.8+](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)

\[!\[Streamlit](https://img.shields.io/badge/Streamlit-1.35+-red.svg)](https://streamlit.io/)

\[!\[Snowflake](https://img.shields.io/badge/Snowflake-Cloud-blue.svg)](https://www.snowflake.com/)

\[!\[Apache Spark](https://img.shields.io/badge/Spark-3.5+-orange.svg)](https://spark.apache.org/)

\[!\[License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)



\## 📊 Real-time Pharmacovigilance Platform for Cancer Clinical Trials



An enterprise-grade adverse event monitoring system that fetches real data from ClinicalTrials.gov API, processes it with Apache Spark, stores it in Snowflake, and provides an interactive safety dashboard.



!\[Dashboard Preview](https://img.icons8.com/color/96/clinical-trial.png)



\## ✨ Features



\- \*\*📊 Real-time Dashboard\*\* - Interactive safety metrics and visualizations

\- \*\*🔬 Signal Detection\*\* - Statistical disproportionality analysis for safety signals

\- \*\*🏥 Cross-Trial Comparison\*\* - Compare AE profiles across multiple trials

\- \*\*📋 Data Explorer\*\* - Search, filter, and export adverse event data

\- \*\*📄 Automated Reports\*\* - Generate regulatory-ready safety reports

\- \*\*☁️ Snowflake Integration\*\* - Enterprise-grade data warehouse

\- \*\*⚡ Apache Spark\*\* - Distributed processing for large-scale AE data



\## 🚀 Live Demo



\[Coming Soon] - Deploying to Streamlit Cloud



\## 🏗️ Architecture

ClinicalTrials.gov API → Python Fetcher → Apache Spark → Snowflake → Streamlit Dashboard





\## 📁 Project Structure

clinical\_trial\_pipeline/

├── safety\_monitor\_app.py # Main Streamlit application (5 tabs)

├── fetch\_ae\_data.py # Fetch real AE data from API

├── spark\_processor.py # Distributed processing with Spark

├── load\_to\_snowflake.py # Load processed data to Snowflake

├── snowflake\_config.py # Snowflake connection config (gitignored)

├── requirements.txt # Python dependencies

└── README.md # This file





\## 🛠️ Installation



\### Prerequisites



\- Python 3.8+

\- Snowflake account (free trial available)

\- Git



\### Step 1: Clone the repository



```bash

git clone https://github.com/IndraniChar/clinical\_trial\_safety\_monitor.git

cd clinical\_trial\_safety\_monitor

