import copy
import math
from time import sleep
import requests
from datetime import datetime, timedelta
from take_from import get_assigned_users_from_ticket, get_customs, get_ticket_details, get_user_details, newest_ticket, init_session
import settings    

def get_prepered_ticket(session_token, ticket_id):

    user_id, technic_id = get_assigned_users_from_ticket(session_token, ticket_id)

    ticket_details = get_ticket_details(session_token, ticket_id)
    
    if ticket_details == None or ticket_details.get('actiontime') == 0:
        return "Skip"

    if ticket_details.get('status') not in [5,6]:
        return "Skip"
    
    solvedate_str = ticket_details.get('solvedate')
    if solvedate_str == None:
        return "Skip"
    
    now = datetime.now()
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

    merged_details = {
        'id': ticket_details.get('id'),
        'firma': str(entities_map.get(ticket_details.get('entities_id'))),
        'tytul': ticket_details.get('name'),
        'gid': user_details.get('name'),
        'solve_date': ticket_details.get('solvedate'),
        'time_spend': (int(ticket_details.get('actiontime'))/60),
        'uprawnienie': uprawnienie,
        'wydatek': wydatek,
        'dodatek': dodatek
    }

    return merged_details
    

def get_report_data(session_token, report):

    newest_ticket_id = newest_ticket(session_token)

    all_tickets_to_process = []
    # FILL DATA
    time_sum_helpdesk = {
                "":0,
                "":0,
                "":0,
                "":0,
                "":0,
                "":0,
                "":0
            }
    time_sum_admini = {
                "":0,
                "":0,
                "":0,
                "":0,
                "":0,
                "":0,
                "":0
            }
    records_set_h = {
        "NumerSprawyH": "",
        "TytulSprawyH": "",
        "KosztyH": "",
        "GIDH": "",
        "CzasH": ""
    }
    records_set_a = {
        "NumerSprawyA": "",
        "TytulSprawyA": "",
        "KosztyA": "",
        "GIDA": "",
        "CzasA": ""
    }

    korpo_set = {
        "numer": "",
        "tytul": "",
        "Koszt": "",
        "KosztBruto": "",
        "klient": "E"
    }

    data_set = {
        "SumHelpdeskWlasnePakiet": 0,
        "SumHelpdeskKorpoPakiet": 0,
        "SumAdminiWlasnePakiet": 0,
        "SumAdminiKorpoPakiet": 0,
        "SumHelpdeskWlasneDodatek": 0,
        "SumHelpdeskKorpoDodatek": 0,
        "SumAdminiWlasneDodatek": 0,
        "SumAdminiKorpoDodatek": 0,
        "ListIDHelpdeskDodatek": ' ',
        "ListIDAdminiDodatek": ' ',
        "JsonHelpdeskPakiet": [],
        "JsonAdminiPakiet": [],
        "JsonHelpdeskDodatek": [],
        "JsonAdminiDodatek": [],    
        "KosztyKorpo": [],
        "KosztWlasnePakiet": 0,
        "KosztKorpoPakiet": 0,
        "KosztHelpdeskWlasneDodatek": 0,
        "KosztHelpdeskKorpoDodatek": 0,
        "KosztAdminiWlasneDodatek": 0,
        "KosztAdminiKorpoDodatek": 0
    }
    # FILL DATA
    report_data = {
        "": copy.deepcopy(data_set),
        "": copy.deepcopy(data_set),
        "": copy.deepcopy(data_set),
        "": copy.deepcopy(data_set),
        "": copy.deepcopy(data_set),
        "": copy.deepcopy(data_set),
        "": copy.deepcopy(data_set)
    }    
    
    for ticket_id in range(newest_ticket_id):
        try:
            prepared_ticket = get_prepered_ticket(session_token, ticket_id)
        except Exception as e:
            continue
            
        if prepared_ticket == "Skip":
            continue
            
        if prepared_ticket.get('uprawnienie') == "Helpdesk":
            previous_time_sum = time_sum_helpdesk.get(prepared_ticket.get('firma'), 0)
            time_sum_helpdesk[prepared_ticket.get('firma')] = prepared_ticket.get('time_spend', 0) + previous_time_sum
            all_tickets_to_process.append(ticket_id)

        else:
            previous_time_sum = time_sum_admini.get(prepared_ticket.get('firma'), 0)
            time_sum_admini[prepared_ticket.get('firma')] = prepared_ticket.get('time_spend', 0) + previous_time_sum
            all_tickets_to_process.append(ticket_id)

    if not report:
        return time_sum_helpdesk, time_sum_admini
    
    req_json = {
        "time": "Tak"
    }
    response = requests.get(settings.link, params=req_json) #API number of workdays

    entitlements = settings.get_entitlements(response)
   
    #Wybranie ticketów dodatkowych z tych ze znacznikiem dodatkowe
    #Oraz W przypadku braku/niedoborze ticketów ze znacznikiem DODATKOWE


    for x in range(2):

        for ticket_id in all_tickets_to_process:
            try:
                prepared_ticket = get_prepered_ticket(session_token, ticket_id)
            except Exception as e:
                continue
            
            if prepared_ticket == "Skip":
                continue

            if prepared_ticket.get('dodatek') == "Tak" and x == 1:
                continue

            if prepared_ticket.get('dodatek') == "Tak" or x == 1:                
                if prepared_ticket.get('uprawnienie') == "Helpdesk":
                    if prepared_ticket.get('wydatek') == "Własne":

                        firma = prepared_ticket.get('firma')
                        if firma not in report_data:
                            report_data[firma] = copy.deepcopy(data_set)

                        data_set_out = report_data[firma]

                        sum_time_till = data_set_out.get('SumHelpdeskWlasneDodatek',0) + data_set_out.get('SumHelpdeskKorpoDodatek',0)

                        sum = data_set_out.get("SumHelpdeskWlasneDodatek")

                        entitlement_company = entitlements.get(prepared_ticket.get('firma'), {})
                        
                        if time_sum_helpdesk.get(prepared_ticket.get('firma')) - entitlement_company.get('Helpdesk', 0)  - sum_time_till - int(prepared_ticket.get('time_spend')) < 0:
                            continue

                        sum = sum + int(prepared_ticket.get('time_spend'))

                        data_set_out["SumHelpdeskWlasneDodatek"] = sum

                        data_set_out["KosztHelpdeskWlasneDodatek"] = sum/60*entitlements.get(prepared_ticket.get('firma')).get('StawkaHelpdeskDod')

                        listID = data_set_out.get('ListIDHelpdeskDodatek')
                        listID = listID + ' ' +str(prepared_ticket.get('id'))+','
                        data_set_out['ListIDHelpdeskDodatek'] = listID

                        records_set_h["NumerSprawyH"] = prepared_ticket.get('id')
                        records_set_h["TytulSprawyH"] = prepared_ticket.get('tytul')
                        records_set_h["KosztyH"] = str(prepared_ticket.get('time_spend')/60*entitlements.get(prepared_ticket.get('firma')).get("StawkaHelpdeskDod")) 
                        records_set_h["GIDH"] = prepared_ticket.get('gid')
                        hours = math.floor(prepared_ticket.get('time_spend')/60)
                        if prepared_ticket.get('time_spend')-(hours*60)>0:
                            minutes = "30"
                        else:
                            minutes = "00"
                        records_set_h["CzasH"] = str(hours)+':'+ minutes +":00"

                        data_set_out['JsonHelpdeskDodatek'].append(copy.deepcopy(records_set_h))

                        report_data[prepared_ticket.get('firma')] = data_set_out

                    elif prepared_ticket.get('wydatek') == "Korporacyjne":

                        firma = prepared_ticket.get('firma')
                        if firma not in report_data:
                            report_data[firma] = copy.deepcopy(data_set)

                        data_set_out = report_data[firma]
                        sum_time_till = data_set_out.get('SumHelpdeskWlasneDodatek', 0) + data_set_out.get('SumHelpdeskKorpoDodatek', 0)

                        sum = data_set_out.get("SumHelpdeskKorpoDodatek") 
                        
                        entitlement_company = entitlements.get(prepared_ticket.get('firma'), {})

                        if time_sum_helpdesk.get(prepared_ticket.get('firma'),0) - entitlement_company.get('Helpdesk', 0) - sum_time_till - int(prepared_ticket.get('time_spend',0)) < 0:
                            continue

                        sum = sum + int(prepared_ticket.get('time_spend'))

                        data_set_out["SumHelpdeskKorpoDodatek"] = sum

                        data_set_out["KosztHelpdeskKorpoDodatek"] = sum/60*entitlements.get(prepared_ticket.get('firma')).  get('StawkaHelpdeskDod')

                        listID = data_set_out.get('ListIDHelpdeskDodatek') 
                        listID = listID  + ' ' + str(prepared_ticket.get('id'))+','
                        data_set_out['ListIDHelpdeskDodatek'] = listID 

                        records_set_h["NumerSprawyH"] = prepared_ticket.get('id')
                        records_set_h["TytulSprawyH"] = prepared_ticket.get('tytul')
                        records_set_h["KosztyH"] = str(prepared_ticket.get('time_spend')/60*entitlements.get(prepared_ticket.get('firma')).get("StawkaHelpdeskDod"))
                        records_set_h["GIDH"] = prepared_ticket.get('gid')
                        hours = math.floor(prepared_ticket.get('time_spend')/60)
                        if prepared_ticket.get('time_spend')-(hours*60)>0:
                            minutes = "30"
                        else:
                            minutes = "00"
                        records_set_h["CzasH"] = str(hours)+':'+ minutes +":00"

                        data_set_out['JsonHelpdeskDodatek'].append(copy.deepcopy(records_set_h))

                        korpo_set["numer"] = prepared_ticket.get('id')
                        korpo_set["tytul"] = prepared_ticket.get('tytul')
                        korpo_set["Koszt"] = str(prepared_ticket.get('time_spend')/60*entitlements.get(prepared_ticket.get('firma')).get("StawkaHelpdeskDod"))
                        korpo_set["KosztBruto"] = int(korpo_set.get("KosztyNetto"))*1.23

                        data_set_out["KosztyKorpo"].append(korpo_set)

                        report_data[prepared_ticket.get('firma')] = data_set_out

                elif prepared_ticket.get('uprawnienie') == "Administracyjne":
                    if prepared_ticket.get('wydatek') == "Własne":

                        firma = prepared_ticket.get('firma')
                        if firma not in report_data:
                            report_data[firma] = copy.deepcopy(data_set)

                        data_set_out = report_data[firma]

                        sum_time_till = data_set_out.get('SumAdminiWlasneDodatek',0)+data_set_out.get('SumAdminiKorpoDodatek',0)

                        sum = data_set_out.get("SumAdminiWlasneDodatek")

                        entitlement_company = entitlements.get(prepared_ticket.get('firma'), {})
                        
                        if time_sum_admini.get(prepared_ticket.get('firma')) - entitlement_company.get('Administracja', 0) - sum_time_till - int(prepared_ticket.get('time_spend')) < 0:
                            continue

                        sum = sum + int(prepared_ticket.get('time_spend'))

                        data_set_out["SumAdminiWlasneDodatek"] = sum

                        data_set_out["KosztAdminiWlasneDodatek"] = sum/60*entitlements.get(prepared_ticket.get('firma')).get('StawkaAdminiDod')

                        listID = data_set_out.get('ListIDAdminiDodatek')
                        listID = listID  + ' ' + str(prepared_ticket.get('id'))+','
                        data_set_out['ListIDAdminiDodatek'] = listID 

                        records_set_a["NumerSprawyA"] = prepared_ticket.get('id')
                        records_set_a["TytulSprawyA"] = prepared_ticket.get('tytul')
                        records_set_a["KosztyA"] = str(prepared_ticket.get('time_spend')/60*entitlements.get(prepared_ticket.get('firma')).get("StawkaAdminiDod"))
                        records_set_a["GIDA"] = prepared_ticket.get('gid')
                        hours = math.floor(prepared_ticket.get('time_spend')/60)
                        if prepared_ticket.get('time_spend')-(hours*60)>0:
                            minutes = "30"
                        else:
                            minutes = "00"
                        records_set_a["CzasA"] = str(hours)+':'+ minutes +":00"

                        data_set_out['JsonAdminiDodatek'].append(copy.deepcopy(records_set_a))

                        report_data[prepared_ticket.get('firma')] = data_set_out

                    elif prepared_ticket.get('wydatek') == "Korporacyjne":

                        firma = prepared_ticket.get('firma')
                        if firma not in report_data:
                            report_data[firma] = copy.deepcopy(data_set)

                        data_set_out = report_data[firma]

                        sum_time_till = data_set_out.get('SumAdminiWlasneDodatek',0)+data_set_out.get('SumAdminiKorpoDodatek',0)

                        sum = data_set_out.get("SumAdminiKorpoDodatek") 

                        entitlement_company = entitlements.get(prepared_ticket.get('firma'), {})
                        
                        if time_sum_admini.get(prepared_ticket.get('firma')) - entitlement_company.get('Administracja', 0) - sum_time_till - int(prepared_ticket.get('time_spend')) < 0:
                            continue

                        sum = sum + int(prepared_ticket.get('time_spend'))

                        data_set_out["SumAdminiKorpoDodatek"] = sum

                        data_set_out["KosztAdminiKorpoDodatek"] = sum/60*entitlements.get(prepared_ticket.get('firma')).get('StawkaAdminiDod')

                        listID = data_set_out.get('ListIDAdminiDodatek') 
                        listID = listID  + ' ' + str(prepared_ticket.get('id'))+','
                        data_set_out['ListIDAdminiDodatek'] = listID 

                        records_set_a["NumerSprawyA"] = prepared_ticket.get('id')
                        records_set_a["TytulSprawyA"] = prepared_ticket.get('tytul')
                        records_set_a["KosztyA"] = str(prepared_ticket.get('time_spend')/60*entitlements.get(prepared_ticket.get('firma')).get("StawkaAdminiDod"))
                        records_set_a["GIDA"] = prepared_ticket.get('gid')
                        hours = math.floor(prepared_ticket.get('time_spend')/60)
                        if prepared_ticket.get('time_spend')-(hours*60)>0:
                            minutes = "30"
                        else:
                            minutes = "00"
                        records_set_a["CzasA"] = str(hours)+':'+ minutes +":00"

                        data_set_out['JsonAdminiDodatek'].append(copy.deepcopy(records_set_a))

                        korpo_set["numer"] = prepared_ticket.get('id')
                        korpo_set["tytul"] = prepared_ticket.get('tytul')
                        korpo_set["Koszt"] = str(prepared_ticket.get('time_spend')/60*entitlements.get(prepared_ticket.get('firma')).get("StawkaAdminiDod"))
                        korpo_set["KosztBruto"] = int(korpo_set.get("KosztyNetto"))*1.23

                        data_set_out["KosztyKorpo"].append(korpo_set)

                        report_data[prepared_ticket.get('firma')] = data_set_out
            else:
                continue

    #end for dodatek
    #Tickety z pakietu

    for ticket_id in all_tickets_to_process:
        try:
            prepared_ticket = get_prepered_ticket(session_token, ticket_id)
        except Exception as e:
            continue
        
        if prepared_ticket == "Skip":
            continue

        if prepared_ticket.get('dodatek') == "Tak":
            continue

        if prepared_ticket.get('uprawnienie') == "Helpdesk":
            if prepared_ticket.get('wydatek') == "Własne":

                data_set_out = report_data.get(prepared_ticket.get('firma'))

                list_dodatek = data_set_out.get('ListIDHelpdeskDodatek') 
                if str(" "+str(prepared_ticket.get('id'))+",") in list_dodatek:
                    continue

                sum = data_set_out.get("SumHelpdeskWlasnePakiet") 

                sum = sum + int(prepared_ticket.get('time_spend'))

                data_set_out["SumHelpdeskWlasnePakiet"] = sum
                data_set_out["KosztWlasnePakiet"] = sum/60*entitlements.get(prepared_ticket.get('firma')).get('StawkaPakiet')

                records_set_h["NumerSprawyH"] = prepared_ticket.get('id')
                records_set_h["TytulSprawyH"] = prepared_ticket.get('tytul')
                records_set_h["KosztyH"] = str(prepared_ticket.get('time_spend')/60*entitlements.get(prepared_ticket.get('firma')).get("StawkaPakiet"))
                records_set_h["GIDH"] = prepared_ticket.get('gid')
                hours = math.floor(prepared_ticket.get('time_spend')/60)
                if prepared_ticket.get('time_spend')-(hours*60)>0:
                    minutes = "30"
                else:
                    minutes = "00"
                records_set_h["CzasH"] = str(hours)+':'+ minutes +":00"

                data_set_out['JsonHelpdeskPakiet'].append(copy.deepcopy(records_set_h))

                report_data[prepared_ticket.get('firma')] = data_set_out

            if prepared_ticket.get('wydatek') == "Korporacyjne":

                data_set_out = report_data.get(prepared_ticket.get('firma'))

                list_dodatek = data_set_out.get('ListIDHelpdeskDodatek') 
                if str(" "+str(prepared_ticket.get('id'))+",") in list_dodatek:
                    continue

                sum = data_set_out.get("SumHelpdeskKorpoPakiet") 

                sum = sum + int(prepared_ticket.get('time_spend'))

                data_set_out["SumHelpdeskKorpoPakiet"] = sum

                data_set_out["KosztKorpoPakiet"] = sum/60*entitlements.get(prepared_ticket.get('firma')).get('StawkaPakiet')

                records_set_h["NumerSprawyH"] = prepared_ticket.get('id')
                records_set_h["TytulSprawyH"] = prepared_ticket.get('tytul')
                records_set_h["KosztyH"] = str(prepared_ticket.get('time_spend')/60*entitlements.get(prepared_ticket.get('firma')).get("StawkaPakiet"))
                records_set_h["GIDH"] = prepared_ticket.get('gid')
                hours = math.floor(prepared_ticket.get('time_spend')/60)
                if prepared_ticket.get('time_spend')-(hours*60)>0:
                    minutes = "30"
                else:
                    minutes = "00"
                records_set_h["CzasH"] = str(hours)+':'+ minutes +":00"

                data_set_out['JsonHelpdeskPakiet'].append(copy.deepcopy(records_set_h)) 

                korpo_set["numer"] = prepared_ticket.get('id')
                korpo_set["tytul"] = prepared_ticket.get('tytul')
                korpo_set["Koszt"] = str(prepared_ticket.get('time_spend')/60*entitlements.get(prepared_ticket.get('firma')).get("StawkaPakiet"))
                korpo_set["KosztBruto"] = int(korpo_set.get("KosztyNetto"))*1.23

                data_set_out["KosztyKorpo"].append(korpo_set)

                report_data[prepared_ticket.get('firma')] = data_set_out

        if prepared_ticket.get('uprawnienie') == "Administracyjne":
            if prepared_ticket.get('wydatek') == "Własne":

                data_set_out = report_data.get(prepared_ticket.get('firma'))

                list_dodatek = data_set_out.get('ListIDAdminiDodatek') 
                if str(" "+str(prepared_ticket.get('id'))+",") in list_dodatek:
                    continue

                sum = data_set_out.get("SumAdminiWlasnePakiet") 

                sum = sum + int(prepared_ticket.get('time_spend'))

                data_set_out["SumAdminiWlasnePakiet"] = sum

                data_set_out["KosztWlasnePakiet"] = sum/60*entitlements.get(prepared_ticket.get('firma')).get('StawkaPakiet')

                records_set_a["NumerSprawyA"] = prepared_ticket.get('id')
                records_set_a["TytulSprawyA"] = prepared_ticket.get('tytul')
                records_set_a["KosztyA"] = str(prepared_ticket.get('time_spend')/60*entitlements.get(prepared_ticket.get('firma')).get("StawkaPakiet"))
                records_set_a["GIDA"] = prepared_ticket.get('gid')
                hours = math.floor(prepared_ticket.get('time_spend')/60)
                if prepared_ticket.get('time_spend')-(hours*60)>0:
                    minutes = "30"
                else:
                    minutes = "00"
                records_set_a["CzasA"] = str(hours)+':'+ minutes +":00"

                data_set_out['JsonAdminiPakiet'].append(copy.deepcopy(records_set_a)) 

                report_data[prepared_ticket.get('firma')] = data_set_out

            if prepared_ticket.get('wydatek') == "Korporacyjne":

                data_set_out = report_data.get(prepared_ticket.get('firma'))

                list_dodatek = data_set_out.get('ListIDAdminiDodatek') 
                if str(" "+str(prepared_ticket.get('id'))+",") in list_dodatek:
                    continue

                sum = data_set_out.get("SumAdminiKorpoPakiet")

                sum = sum + int(prepared_ticket.get('time_spend'))

                data_set_out["SumAdminiKorpoPakiet"] = sum

                data_set_out["KosztKorpoPakiet"] = sum/60*entitlements.get(prepared_ticket.get('firma')).get('StawkaPakiet')

                records_set_a["NumerSprawyA"] = prepared_ticket.get('id')
                records_set_a["TytulSprawyA"] = prepared_ticket.get('tytul')
                records_set_a["KosztyA"] = str(prepared_ticket.get('time_spend')/60*entitlements.get(prepared_ticket.get('firma')).get("StawkaPakiet")) 
                records_set_a["GIDA"] = prepared_ticket.get('gid')
                hours = math.floor(prepared_ticket.get('time_spend')/60)
                if prepared_ticket.get('time_spend')-(hours*60)>0:
                    minutes = "30"
                else:
                    minutes = "00"
                records_set_a["CzasA"] = str(hours)+':'+ minutes +":00"

                data_set_out['JsonAdminiPakiet'].append(copy.deepcopy(records_set_a)) 

                korpo_set["numer"] = prepared_ticket.get('id')
                korpo_set["tytul"] = prepared_ticket.get('tytul')
                korpo_set["Koszt"] = str(prepared_ticket.get('time_spend')/60*entitlements.get(prepared_ticket.get('firma')).get("StawkaPakiet"))
                korpo_set["KosztBruto"] = int(korpo_set.get("KosztyNetto"))*1.23

                data_set_out["KosztyKorpo"].append(korpo_set)

                report_data[prepared_ticket.get('firma')] = data_set_out

    return report_data
   
def send_full_data():

    #for every company
    session_token = init_session()

    data = get_report_data(session_token, True)


    for company, data_set in data.items():
        print("-" * 40)

        payload = {
            "company" : company,
            "data": data_set
        }
        headers = {'Content-Type': 'application/json'}

        print(payload)
        
        response = requests.post(settings.upload_link, json=payload, headers=headers)
        response.raise_for_status()  
        print("Raport sent")
        sleep(5)

def send_small_data():

    #for every company
    session_token = init_session()

    time_sum_helpdesk, time_sum_admini = get_report_data(session_token, False)

    for company, timeH in time_sum_helpdesk.items():
        print("-" * 40)
        timeA = time_sum_admini.get(company)

        payload = {
            "company" : company,
            "helpdesk": timeH,
            "admini": timeA
        }
        headers = {'Content-Type': 'application/json'}

        print(payload)
        
        response = requests.post(settings.little_upload_link, json=payload, headers=headers)
        response.raise_for_status()  
        print("mini Raport sent")
        sleep(2)
