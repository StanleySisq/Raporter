import requests
import settings
from take_from import header, init_session, get_user_details

def get_users(session_token):

    response = requests.get(
        f"{settings.glpi_url}/User?&sort=id&order=DESC&range=0-3999",
        headers=header(session_token)
    )

    if response.status_code == 200 or response.status_code == 206:
        users = response.json()
        return users
    else:
        print(f"Error downloading group users: {response.status_code}")
        return None

def get_group_users(session_token, group_id):

    response = requests.get(
        f"{settings.glpi_url}/Group/{group_id}/Group_User?&sort=id&order=DESC&range=0-999",
        headers=header(session_token)
    )

    if response.status_code == 200 or response.status_code == 206:
        users = response.json()
        return users
    else:
        print(f"Error downloading group users: {response.status_code}")
        return None

def put_group_user(session_token, group_id, user_id):

    payload = {
        "input": [
            {
        "groups_id": group_id,
        "users_id": user_id,
        "is_dynamic": 0,
        "is_manager": 0,
        "is_userdelegate": 0
            }
        ]
    }

    response = requests.post(
        f"{settings.glpi_url}/Group_User",
        headers=header(session_token),
        json=payload
    )

    if response.status_code == 201:
        print("User added to group successfully")
        return response.json()
    else:
        print(f"Error adding user to group: {response.status_code}")
        return None
    
def put_new_user_in_groups():

    session_token = init_session()

    all_users = get_users(session_token)
    groups_id = [8, 9, 10, 11, 12, 13]
    all_users_id = []
    ignore = [3857, 3856, 3809, 3808, 3807, 3793, 3471, 6, 5, 4, 3, 2]

    inside = ["OU=GLI","OU=SLU", "OU=ZLO", "OU=ENGI", "OU=SAR", "OU=ES"]
    inside_id = {"OU=GLI":12,"OU=SLU":11, "OU=ZLO":13, "OU=ENGI":10, "OU=SAR":8, "OU=ES":9}

    for user in all_users:
        all_users_id.append(user.get('id'))
    
    for iger in ignore:
        all_users_id.remove(iger)

    for group in groups_id:
        all_group_users = get_group_users(session_token, group)

        for user in all_group_users:
            if user.get('users_id') in all_users_id:
                all_users_id.remove(user.get('users_id'))

    print(all_users_id)

    for user_id in all_users_id:
        details = get_user_details(session_token, user_id)
        
        for inis in inside:
            if inis in details.get('user_dn'):
                put_group_user(session_token, inside_id.get(inis), user_id)