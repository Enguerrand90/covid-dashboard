#Step 1: Install prerequisites
#Make sure you have the following installed on your computer:

#Python 3.8 or higher (recommended Python 3.11)
#Download here: https://www.python.org/downloads/

#Git (for cloning the project)
#Download here: https://git-scm.com/downloads



#Step 2: Clone the project repository
#Open a terminal (PowerShell, Command Prompt, or macOS/Linux terminal) and run:

#git clone https://github.com/Enguerrand90/covid-dashboard.git
#cd covid-dashboard
#This downloads the project files and moves into the project directory.



#Step 3: Install required Python packages
#Run this command to install all necessary dependencies:

#pip install -r requirements.py



#Step 4: Start the French COVID-19 REST API server
#The app needs a local API server to fetch French COVID data. You must start this server before running the app.

#Make sure you have the API code (api.py) in your project folder.

#Install the API dependencies if you haven't yet:

#pip install fastapi uvicorn
#uvicorn api:app --reload

#This will start the API server at: http://127.0.0.1:8000


#Step 5: Run the Streamlit application
#With the API server running, open another terminal window and launch the Streamlit app by running:

#streamlit run app.py

#Your default browser should automatically open the app at: http://localhost:8501



#"Troubleshooting tips
#If streamlit is not recognized, try running:

#python -m streamlit run app.py


#Make sure the API server (Step 4) is running before launching the app to avoid data errors for France.

#If ports 8501 (Streamlit) or 8000 (API) are busy, use different ports:


#streamlit run app.py --server.port 8502
#uvicorn api:app --reload --port 8001

