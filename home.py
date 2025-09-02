import streamlit as st
import pandas as pd
import numpy as np
import difflib
import requests
from sklearn.metrics.pairwise import cosine_similarity
from utils import load_data, load_model
from database import db_manager

TMDB_API_KEY = "3e1bbc5e8d0471945759c35efcbf6967"

def suggest_titles(user_input, titles_list):
    return difflib.get_close_matches(user_input, titles_list, n=5, cutoff=0.3) if user_input else []

def recommend(title, df, k=5, selected_genre=None):
    row = df.loc[df["title"] == title].iloc[0]
    emb, cl = row["text_embedding"], row["cluster"]
    sub = df[df["cluster"] == cl].copy()
    if selected_genre:
        sub = sub[sub["genres"].str.contains(selected_genre, na=False)]
    if sub.empty:
        return pd.DataFrame({"title": [], "similarity_score": []})
    sims = cosine_similarity(emb.reshape(1, -1), np.vstack(sub["text_embedding"].values)).ravel()
    sub["similarity_score"] = sims
    for col, new in [("popularity", "popularity_norm"), ("vote_average", "vote_norm"), ("runtime", "runtime_norm")]:
        m = sub[col].max(skipna=True)
        sub[new] = sub[col] / m if m else 0
    sub["score"] = (0.50 * sub["similarity_score"] + 0.20 * sub["popularity_norm"] +
                    0.20 * sub["vote_norm"] + 0.10 * sub["runtime_norm"])
    sub = sub[sub["title"] != title]
    return sub.sort_values("score", ascending=False).loc[:, ["title", "similarity_score"]].head(k).reset_index(drop=True)

@st.cache_data(show_spinner=False)
def get_movie_details(title):
    url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={title}"
    response = requests.get(url).json()
    if response["results"]:
        movie_id = response["results"][0]["id"]
        details_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&append_to_response=credits"
        details = requests.get(details_url).json()
        actors = [actor["name"] for actor in details.get("credits", {}).get("cast", [])[:5]]
        genres = [genre["name"] for genre in details.get("genres", [])]
        return {
            "title": details.get("title"),
            "poster": f"https://image.tmdb.org/t/p/w500{details.get('poster_path')}" if details.get('poster_path') else None,
            "release_date": details.get("release_date"),
            "vote_average": details.get("vote_average"),
            "overview": details.get("overview"),
            "actors": actors or ["Casting not available"],
            "genres": genres or ["Unknown genre"]
        }
    return None

@st.cache_data(show_spinner=False)
def get_movie_poster(title):
    url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={title}"
    response = requests.get(url).json()
    if response["results"]:
        poster_path = response["results"][0].get("poster_path")
        return f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
    return None

def app():
    st.title("🎥 Movie Recommendation System")
    
    # Initialize session state for recommended_movies if not exists
    if "recommended_movies" not in st.session_state:
        st.session_state["recommended_movies"] = pd.DataFrame()
    elif st.session_state["recommended_movies"] is None:
        st.session_state["recommended_movies"] = pd.DataFrame()
    
    # Load data
    df = load_data()
    kmeans = load_model()
    
    # Extract unique genres
    all_genres_list = sorted(set(g for sublist in df["genres"].dropna().str.split(', ') for g in sublist))
    titles = sorted(df["title"].unique())
    
    # Genre filter
    st.sidebar.markdown("## 🎭 Filter by Genre")
    genre_buttons = st.sidebar.columns(3)
    selected_genre_accueil = None
    all_genres_list_with_all = ["All genres"] + all_genres_list
    
    for i, genre in enumerate(all_genres_list_with_all):
        with genre_buttons[i % 3]:
            if st.button(genre):
                st.session_state["selected_genre_accueil"] = genre if genre != "All genres" else None
    
    selected_genre_filter = st.session_state.get("selected_genre_accueil")
    if selected_genre_filter:
        st.markdown(f"**Selected genre:** {selected_genre_filter}")
    
    # Movie search
    def update_title_suggestions():
        if st.session_state.user_input:
            st.session_state.title_suggestions = suggest_titles(st.session_state.user_input, titles)
        else:
            st.session_state.title_suggestions = []
    
    st.text_input("🔍 Enter a movie title:", key="user_input", on_change=update_title_suggestions)
    
    if st.session_state.title_suggestions:
        selected = st.selectbox("📍 Suggestions:", st.session_state.title_suggestions)
        if selected:
            st.session_state["recommended_movies"] = recommend(selected, df, selected_genre=selected_genre_filter)
            st.session_state["selected_movie"] = selected
            st.session_state["expanded_detail"] = None
    elif st.session_state.user_input:
        st.info("No suggestions found.")
    
    # Display recommendations
    if isinstance(st.session_state["recommended_movies"], pd.DataFrame) and not st.session_state["recommended_movies"].empty:
        st.markdown(f"### 🎯 Recommendations for: **{st.session_state['selected_movie']}**")
        cols = st.columns(len(st.session_state["recommended_movies"]))
        for i, row in st.session_state["recommended_movies"].iterrows():
            with cols[i]:
                st.markdown(f"**{row['title']}**")
                poster = get_movie_poster(row["title"])
                if poster:
                    st.image(poster, use_container_width=True)
                st.markdown(f"🧠 Similarity: `{round(row['similarity_score'] * 100, 1)}%`")
                if st.button("View details", key=f"detail_{i}"):
                    st.session_state["expanded_detail"] = row["title"]
    
    # Display movie details
    if st.session_state.get("expanded_detail"):
        st.markdown("---")
        detail = get_movie_details(st.session_state["expanded_detail"])
        if detail:
            st.subheader(f"🎬 {detail['title']}")
            if detail["poster"]:
                st.image(detail["poster"], use_container_width=True)
            st.markdown(f"📅 Release date: {detail['release_date']}")
            st.markdown(f"⭐ Average rating: {detail['vote_average']}")
            st.markdown(f"🎭 Genres: {', '.join(detail['genres'])}")
            st.markdown(f"🧑 Main actors: {', '.join(detail['actors'])}")
            st.markdown("📝 **Overview:**")
            st.write(detail["overview"])
            
            # Save to history if logged in
            if st.session_state.get('logged_in'):
                user_id = db_manager.get_user_id(st.session_state['username'])
                if user_id:
                    db_manager.save_history(
                        user_id=user_id,
                        movie_title=detail['title'],
                        similarity=st.session_state["recommended_movies"].loc[
                            st.session_state["recommended_movies"]["title"] == detail['title'], 
                            "similarity_score"
                        ].iloc[0]
                    )
