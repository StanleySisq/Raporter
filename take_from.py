import requests
import settings, db_funcs

def init_session():

    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'user_token ' + settings.user_token,
        'App-Token': settings.app_token
    }
    
    response = requests.get(f"{settings.glpi_url}/initSession", headers=headers)
    
    if response.status_code == 200:
        session_token = response.json()['session_token']
        return session_token
    else:
        print(f"Cannot initialize sesion: {response.status_code}")
        print(response.text)
        return None
    
def header(session_token):
    headers = {
        'Content-Type': 'application/json',
        'Session-Token': session_token,
        'App-Token': settings.app_token
    }
    return headers

def newest_ticket(session_token):
    ranga=f'0-100000'
    
    params = {
        'range': ranga, 
        'sort': 2,        # Sort by ID ,by 'data' set 15
        'order': 'DESC'   
    }
    
    response = requests.get(f"{settings.glpi_url}/search/Ticket", headers=header(session_token), params=params)
    
    if response.status_code == 200:
        tickets = response.json()
        if 'data' in tickets and tickets['data']:
            latest_ticket = tickets['data'][0]  # Download newest ticket
            latest_ticket_id = latest_ticket.get('2')  # Download ID ticket (pole '2')
            return latest_ticket_id
        else:
            print("No avaible tickets.")
            return None
    else:
        print(f"Error searching tickets : {response.status_code}")
        #print(response.text)
        return None

def get_ticket_details(session_token, ticket_id):
    
    response = requests.get(f"{settings.glpi_url}/Ticket/{ticket_id}", headers=header(session_token))
    
    if response.status_code == 200:
        ticket_details = response.json()
        return ticket_details
    else:
        print(f"Error extracting tickets details: {response.status_code}")
        db_funcs.add_ticket_id(ticket_id)
        print(f"Ticked id: {ticket_id} added to forgotten list")
        #print(response.text)
        return None
    
def get_user_details(session_token, user_id):
    
    response = requests.get(f"{settings.glpi_url}/User/{user_id}", headers=header(session_token))
    
    if response.status_code == 200:
        user_details = response.json()
        return user_details
    else:
        print(f"Error downloading user details: {response.status_code}")
        #print(response.text)
        return None

def get_assigned_users_from_ticket(session_token, ticket_id):

    url = f"{settings.glpi_url}/Ticket/{ticket_id}/Ticket_User"

    response = requests.get(url, headers=header(session_token))

    if response.status_code == 200:
        result = response.json() 

        if result:
            requester = "None"
            technician = "None"

            for user in result:
                user_type = user.get('type')  

                if str(user_type) == "1":
                    requester = user.get('users_id')
                
                if str(user_type) == "2" and technician == "None":
                    if requester == "None" or str(user.get('user_id')) in settings.our_technics:
                        technician = user.get('users_id')

            #print(technician)
            #print(requester)
            return requester, technician
        else:
            print(f"No users found for ticket ID {ticket_id}.")
            return "None", "None"
    else:
        print(f"Error fetching assigned users: {response.status_code} - {response.text}")
        return "None", "None"

def get_customs(session_token, ticket_id):

    endpoint = f"{settings.glpi_url}/{settings.resource}?criteria[0][field]=items_id&criteria[0][searchtype]=equals&criteria[0][value]={ticket_id}"

    response = requests.get(endpoint, headers=header(session_token))
    uprawnienie = "None"
    wydatek = "None"
    dodatek = "None"

    if response.status_code == 200:
        datas = response.json()
        if datas:
            for data in datas:
                if data.get('items_id') == ticket_id:
                    uprawnienie = data.get("plugin_fields_uprawnieniefielddropdowns_id", "None")
                    wydatek = data.get("plugin_fields_kategoriawydatkufielddropdowns_id", "None")
                    dodatek = data.get("czydodatkowefield", "None")
                    break

        else:
            print("Brak danych dla podanego zgłoszenia.")
    else:
        print(f"Błąd {response.status_code}: {response.text}")
    
    if uprawnienie == 1: uprawnienie = "Helpdesk" 
    elif uprawnienie == 2: uprawnienie = "Administracyjne"
    else: uprawnienie = "None"

    if wydatek == 1: wydatek = "Własne"
    elif wydatek == 2: wydatek = "Korporacyjne"
    else: wydatek = "None"

    if dodatek == 1: dodatek = "Tak"
    elif dodatek == 0: dodatek = "Nie"
    else: dodatek = "None"
    
    return uprawnienie, wydatek, dodatek