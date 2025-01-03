# App_Token from GLPI
app_token = ""
# User Api Token from GLPI, access to read and solv all tickets
user_token = ""
# URL to GLPI "https://your-glpi.pl/apirest.php/"
glpi_url = "https://your-glip.com/apirest.php/"
# Link to API with workdays in billing period
link = ""
# Link where post results of full raport
upload_link = ""
# Link where post results of small raport
little_upload_link = ""
# Name of custom fields group
resource = ""
# Our technics GLPI ID list
our_technics = []
# First day (in previous month) of billing period
first_day = 25
# Last day (in current month) of billing period
last_day = 25
#ip
host = '172.17.17.78'
#port
port = 5000

entities_map = {
                1: "",
                2: "",
                3: "",
                4: "",
                5: "",
                6: "",
                7: ""
            }

# Entitlements of companies
def get_entitlements(response):
    entitlements = {
            "": {
                "Helpdesk": int(response.json().get('date'))*60, # czas w minutach
                "Administracja": 40*60,
                "StawkaPakiet": 100, 
                "StawkaHelpdeskDod": 100,
                "StawkaAdminiDod": 100
            },
            "":{
                "Helpdesk": 167*60,
                "Administracja": 46*60,
                "StawkaPakiet": 100,
                "StawkaHelpdeskDod": 100,
                "StawkaAdminiDod": 100
            },
            "": {
                "Helpdesk": 0,
                "Administracja": 0,
                "StawkaPakiet": 100,
                "StawkaHelpdeskDod": 100,
                "StawkaAdminiDod": 100
            },
            "": {
                "Helpdesk": 0,
                "Administracja": 0,
                "StawkaPakiet": 100,
                "StawkaHelpdeskDod": 100,
                "StawkaAdminiDod": 100
            },
            "": {
                "Helpdesk": 0,
                "Administracja": 0,
                "StawkaPakiet": 100,
                "StawkaHelpdeskDod": 100,
                "StawkaAdminiDod": 100
            },
            "": {
                "Helpdesk": 0,
                "Administracja": 0,
                "StawkaPakiet": 100,
                "StawkaHelpdeskDod": 100,
                "StawkaAdminiDod": 100
            },
            "": {
                "Helpdesk": 0,
                "Administracja": 0,
                "StawkaPakiet": 100,
                "StawkaHelpdeskDod": 100,
                "StawkaAdminiDod": 100
            }
        }
    return entitlements