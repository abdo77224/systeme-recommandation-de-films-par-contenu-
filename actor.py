import streamlit as st
import requests
from database import db_manager

TMDB_API_KEY = "3e1bbc5e8d0471945759c35efcbf6967"

def search_actor_suggestions(query):
    """Search for actor suggestions using TMDB API."""
    if not query:
        return []
    url = f"https://api.themoviedb.org/3/search/person?api_key={TMDB_API_KEY}&query={query}"
    response = requests.get(url).json()
    return [result["name"] for result in response.get("results", [])]

def get_movies_by_actor(actor_id):
    """Get movies for a specific actor using TMDB API."""
    credits_url = f"https://api.themoviedb.org/3/person/{actor_id}/movie_credits?api_key={TMDB_API_KEY}"
    credits = requests.get(credits_url).json()
    return credits.get("cast", [])

def app():
    st.title("🎭 Movies by Actor")
    
    def update_actor_suggestions():
        if st.session_state.actor_input:
            st.session_state.actor_suggestions = search_actor_suggestions(st.session_state.actor_input)
        else:
            st.session_state.actor_suggestions = []
    
    # Actor search
    st.text_input("🔎 Enter an actor's name:", key="actor_input", on_change=update_actor_suggestions)
    
    if st.session_state.actor_suggestions:
        selected_actor = st.selectbox("🎯 Actor suggestions:", st.session_state.actor_suggestions)
        if selected_actor:
            # Get actor details
            search_url = f"https://api.themoviedb.org/3/search/person?api_key={TMDB_API_KEY}&query={selected_actor}"
            response = requests.get(search_url).json()
            
            if response["results"]:
                actor_id = response["results"][0]["id"]
                actor_name_corrected = response["results"][0]["name"]
                movies = get_movies_by_actor(actor_id)
                
                # Get genre mapping
                genre_response = requests.get(
                    f"https://api.themoviedb.org/3/genre/movie/list?api_key={TMDB_API_KEY}"
                ).json()
                genre_name_map = {
                    item['id']: item['name'] 
                    for item in genre_response.get('genres', [])
                }
                
                # Extract unique genres and years for filters
                actor_genres = sorted(set(
                    genre_name_map.get(g) 
                    for movie in movies 
                    for g in movie.get("genre_ids", [])
                    if genre_name_map.get(g)
                ))
                
                available_years = sorted(list(set(
                    str(movie.get("release_date", "")[:4]) 
                    for movie in movies 
                    if movie.get("release_date")
                )))
                
                # Filters
                col1, col2 = st.columns(2)
                with col1:
                    selected_genres = st.multiselect(
                        "🎭 Filter by genre:",
                        actor_genres
                    )
                with col2:
                    selected_year = st.selectbox(
                        "🗓️ Filter by year:",
                        ["All years"] + available_years
                    )
                
                # Apply filters
                filtered_movies = movies
                if selected_genres:
                    filtered_movies = [
                        movie for movie in filtered_movies 
                        if any(genre_name_map.get(g) in selected_genres 
                              for g in movie.get("genre_ids", []))
                    ]
                if selected_year != "All years":
                    filtered_movies = [
                        movie for movie in filtered_movies 
                        if str(movie.get("release_date", "")[:4]) == selected_year
                    ]
                
                # Display results
                if filtered_movies:
                    st.markdown(f"### 🎬 Movies featuring **{actor_name_corrected}**")
                    
                    # Sort movies by popularity
                    filtered_movies.sort(key=lambda x: x.get("popularity", 0), reverse=True)
                    
                    # Display in columns
                    cols = st.columns(min(5, len(filtered_movies)))
                    for i, movie in enumerate(filtered_movies[:5]):
                        with cols[i % min(5, len(filtered_movies))]:
                            st.markdown(f"**{movie.get('title')}**")
                            if movie.get("poster_path"):
                                st.image(
                                    f"https://image.tmdb.org/t/p/w200{movie['poster_path']}", 
                                    use_container_width=True
                                )
                            st.markdown(f"📅 {movie.get('release_date', 'Unknown date')[:4]}")
                            st.markdown(f"⭐ Rating: `{movie.get('vote_average', 'N/A')}`")
                            st.markdown(f"🎭 Role: *{movie.get('character', 'Not specified')}*")
                            
                            # Save to history if logged in
                            if st.session_state.get('logged_in'):
                                user_id = db_manager.get_user_id(st.session_state['username'])
                                if user_id:
                                    db_manager.save_history(
                                        user_id=user_id,
                                        movie_title=movie['title'],
                                        similarity=0.0  # No similarity score for actor search
                                    )
                else:
                    st.info("No movies found with these filters.")
            else:
                st.error("Actor not found.")
    elif st.session_state.actor_input:
        st.info("No suggestions found.")