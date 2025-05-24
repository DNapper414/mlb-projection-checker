from supabase import create_client, Client

# Your actual Supabase project credentials
SUPABASE_URL = "https://dpedazmpshbufsmrnhet.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRwZWRhem1wc2hidWZzbXJuaGV0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDgwOTMyODUsImV4cCI6MjA2MzY2OTI4NX0.ldE4FNtnCHzfNVDBYSqPLVxX0m4OAQFZrS-bE1mEirk"

# Initialize the Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Helper: attach session_id to each request (for RLS filtering)
def with_session(session_id):
    return supabase.with_headers({"session-id": session_id})

# Add a new player projection
def add_projection(data):
    return with_session(data["session_id"]).table("projections").insert(data).execute()

# Get all projections for a session
def get_projections(session_id):
    return with_session(session_id).table("projections").select("*").execute()

# Remove a single projection by ID
def remove_projection(projection_id, session_id):
    return with_session(session_id).table("projections").delete().eq("id", projection_id).execute()

# Clear all projections for a session
def clear_projections(session_id):
    return with_session(session_id).table("projections").delete().execute()