import streamlit as st
import pandas as pd
from database import db_manager
from datetime import datetime
import struct

def app():
    st.title("📚 Movie History Archive")
    
    if not st.session_state.get('logged_in'):
        st.warning("Please log in to view your movie history.")
        return
    
    # Get user ID
    user_id = db_manager.get_user_id(st.session_state['username'])
    if not user_id:
        st.error("Error retrieving user data.")
        return
    
    # Get user's movie history
    history = db_manager.get_user_history(user_id)
    if not history:
        st.info("No movie history found. Start exploring movies to build your history!")
        return
    
    # Convert history to DataFrame
    df = pd.DataFrame(history, columns=['movie_title', 'similarity_score', 'timestamp'])
    
    # Convert timestamp to datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Convert binary similarity scores to float
    try:
        def convert_similarity(x):
            if isinstance(x, bytes):
                # Convert binary data to float using struct
                return struct.unpack('f', x)[0]
            elif isinstance(x, (int, float)):
                return float(x)
            else:
                return 0.0
        
        df['similarity_score'] = df['similarity_score'].apply(convert_similarity)
    except Exception as e:
        st.error(f"Error processing similarity scores: {str(e)}")
        return
    
    # Add filters
    st.sidebar.subheader("🔍 Filter History")
    
    # Date range filter
    min_date = df['timestamp'].min().date()
    max_date = df['timestamp'].max().date()
    date_range = st.sidebar.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    # Similarity score filter
    min_similarity = float(df['similarity_score'].min())
    max_similarity = float(df['similarity_score'].max())
    
    # Handle case where all similarity scores are the same
    if min_similarity == max_similarity:
        # Create a range around the single value
        min_similarity = max(0.0, min_similarity - 0.1)
        max_similarity = min(1.0, max_similarity + 0.1)
    
    similarity_range = st.sidebar.slider(
        "Similarity Score Range",
        min_value=min_similarity,
        max_value=max_similarity,
        value=(min_similarity, max_similarity)
    )
    
    # Apply filters
    filtered_df = df[
        (df['timestamp'].dt.date >= date_range[0]) &
        (df['timestamp'].dt.date <= date_range[1]) &
        (df['similarity_score'] >= similarity_range[0]) &
        (df['similarity_score'] <= similarity_range[1])
    ]
    
    # Display filtered history
    st.subheader("🎬 Your Movie History")
    
    # Sort options
    sort_by = st.selectbox(
        "Sort by",
        ["Most Recent", "Highest Similarity", "Movie Title"]
    )
    
    if sort_by == "Most Recent":
        filtered_df = filtered_df.sort_values('timestamp', ascending=False)
    elif sort_by == "Highest Similarity":
        filtered_df = filtered_df.sort_values('similarity_score', ascending=False)
    else:  # Movie Title
        filtered_df = filtered_df.sort_values('movie_title')
    
    # Display movies in a grid
    cols = st.columns(3)
    for i, (_, row) in enumerate(filtered_df.iterrows()):
        with cols[i % 3]:
            st.markdown(f"**{row['movie_title']}**")
            st.markdown(f"📅 {row['timestamp'].strftime('%Y-%m-%d %H:%M')}")
            st.markdown(f"🎯 Similarity: `{row['similarity_score']:.2%}`")
            st.markdown("---")
    
    # Export option
    if st.button("📥 Export History"):
        # Convert similarity scores to percentages for export
        export_df = filtered_df.copy()
        export_df['similarity_score'] = export_df['similarity_score'].apply(lambda x: f"{x:.2%}")
        csv = export_df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"movie_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
