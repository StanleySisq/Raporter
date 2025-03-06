
import copy
from datetime import datetime, timedelta
import math
import queue
import threading
from time import sleep

import requests
import db_funcs
import settings
from take_from import get_assigned_users_from_ticket, get_customs, get_ticket_details, get_user_details, init_session, newest_ticket


def get_prepered_ticket(session_token, ticket_id):

    ticket_details = get_ticket_details(session_token, ticket_id)
    
    if ticket_details == None or ticket_details.get('actiontime') == 0:
        return "Skip"

    if ticket_details.get('status') not in [5,6]:
        return "Skip"
    
    solvedate_str = ticket_details.get('solvedate')
    if solvedate_str == None:
        return "Skip"
    
    
    now = datetime.now()

    nowday = now.strftime("%d")
    if int(nowday) > 25:
        current_month_25th = now + timedelta(days=1)
        previous_month_25th = now.replace(day=settings.first_day)
    else:
        current_month_25th = now.replace(day=settings.last_day)
        last_day_of_previous_month = now.replace(day=1) - timedelta(days=1)
        previous_month_25th = last_day_of_previous_month.replace(day=settings.first_day)

    if solvedate_str:
        solvedate = datetime.strptime(solvedate_str, "%Y-%m-%d %H:%M:%S")
    else:
        solvedate = None

    if solvedate and previous_month_25th <= solvedate < current_month_25th:
        print(f"Ticket id: {ticket_id}, Solve Date: {solvedate}")
    else:
        return "Skip"
    
    user_id, technic_id = get_assigned_users_from_ticket(session_token, ticket_id)

    user_details = get_user_details(session_token, user_id)

    uprawnienie, wydatek, dodatek = get_customs(session_token, ticket_id)
    technics = settings.our_technics

    if str(technic_id) not in technics:
        if uprawnienie != "None" or wydatek != "None" or dodatek != "None":
            print(f'Risky ticket: {ticket_id}')
            if uprawnienie == "None":
                uprawnienie = "Helpdesk"
            if wydatek == "None":
                wydatek = "Własne"
            if dodatek == "None":
                dodatek = "Nie"
        else:
            return "Skip"


    entities_map = settings.entities_map


    gido = user_details.get('name')
    firstname = user_details.get('firstname')
    surename = user_details.get('realname')
    full_name =  firstname + " " + surename

    try:
        if gido.endswith('-NN'):
            gido = gido[0:6]
    except Exception as e:
        print('Error cuting GID')

    if ticket_details.get('entities_id') == 0:
        if user_details.get('entities_id') != 0:
            entity_id = user_details.get('entities_id')
        else:
            entity_id = 1
    else:
        entity_id = ticket_details.get('entities_id')

    
    if int(ticket_details.get('id')) <= 9999:
        idek = "HLP#000"+str(ticket_details.get('id'))
    else:
        idek = "HLP#00"+str(ticket_details.get('id'))

    merged_details = {
        'id': idek,
        'user_name': full_name,
        'firma': str(entities_map.get(entity_id)),
        'tytul': ticket_details.get('name'),
        'gid': gido,
        'solve_date': ticket_details.get('solvedate'),
        'time_spend': (int(ticket_details.get('actiontime'))/60),
        'uprawnienie': uprawnienie,
        'kategoria_wydatku': wydatek
    }

    return merged_details

def get_report_data(session_token):

    newest_ticket_id = newest_ticket(session_token)

    records_set = {
        "Numer": "",
        "Data": "",
        "Tytul": "",
        "Beneficjent": "",
        "GID": "",
        "Czas": 0,
        "Kategoria": "",
        "Uprawnienie": "",
        "Pakiet": 0
    }

    # FILL DATA WITH SAME COMPANY FULL NAMES
    report_data = {
        "": [],
        "": [],
        "": [],
        "": [],
        "": [],
        "": [],
        "": []
    }    
    copy.deepcopy(records_set)
    req_json = {
        "time": "Tak"
    }

    response = requests.get(settings.link, params=req_json) #API number of workdays
 
    entitlements = settings.get_entitlements(response)


    for ticket_id in range(newest_ticket_id):
        if not db_funcs.is_ticket(ticket_id):
            prepared_ticket = get_prepered_ticket(session_token, ticket_id)

            if prepared_ticket == "Skip":
                continue

            records_set["Numer"] = prepared_ticket.get('id')
            records_set["Tytul"] = prepared_ticket.get('tytul')
            records_set["Kategoria"] = prepared_ticket.get('wydatek') 
            records_set["Beneficjent"] = prepared_ticket.get('user_name')
            records_set["Czas"] = prepared_ticket.get('time_spend')/60
            records_set["GID"] = prepared_ticket.get('gid')
            records_set["Uprawnienie"] = prepared_ticket.get('uprawnienie')
            records_set["Data"] = str(prepared_ticket.get('solve_date'))
            records_set["Pakiet"] = (int(entitlements.get(prepared_ticket.get('firma')).get('Helpdesk'))/60)+(int(entitlements.get(prepared_ticket.get('firma')).get('Administracja'))/60)
            
            report_data[prepared_ticket.get('firma')].append(copy.deepcopy(records_set))
    
    return report_data


def send_live_data():

    #for every company
    session_token = init_session()

    data = get_report_data(session_token)


    for company, data_set in data.items():
        for i in range(10):
            try:
                print("-" * 40)

                payload = {
                    "company" : company,
                    "data": data_set
                }
                headers = {'Content-Type': 'application/json'}

                print(payload)
                
                response = requests.post(settings.upload_link_live, json=payload, headers=headers)
                #response.raise_for_status()  
                print("Live Raport sent")
                sleep(10)
            except Exception as e:
                print(f'Error sending live data: {e}')
                continue
            else:
                break    