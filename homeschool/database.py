import supabase
from config import SUPABASE_URL, SUPABASE_KEY

client = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)

def get_user(custom_id, password, role):
    response = client.table('users').select('*').eq('custom_id', custom_id).eq('role', role).execute()
    if response.data and response.data[0]['password'] == password:
        return response.data[0]
    return None

# Add more database functions as needed