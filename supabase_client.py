from supabase import create_client, Client

# Your actual Supabase credentials
SUPABASE_URL = "https://dpedazmpshbufsmrnhet.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRwZWRhem1wc2hidWZzbXJuaGV0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDgwOTMyODUsImV4cCI6MjA2MzY2OTI4NX0.ldE4FNtnCHzfNVDBYSqPLVxX0m4OAQFZrS-bE1mEirk"

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Insert a new player projection
def add_projection(data):
    return supabase.table("projections").insert(data).execute()

# Retrieve projections for a specific session
def get_projections(session_id):
    return supabase.table("projections").select("*").eq("session_id", session_id).execute()

# Remove a single projection by its ID and session ID (double-safe)
def remove_projection(projection_id, session_id):
    return supabase.table("projections").delete().eq("id", projection_id).eq("session_id", session_id).execute()

# Delete all projections for a session
def clear_projections(session_id):
    return supabase.table("projections").delete().eq("session_id", session_id).execute()