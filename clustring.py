import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from sklearn.metrics.pairwise import cosine_similarity
from utils import load_data, load_model

def app():
    st.title("📊 Movie Cluster Analysis")
    
    # Load data
    df = load_data()
    
    # Cluster statistics
    st.subheader("🎯 Cluster Overview")
    
    # Calculate cluster sizes
    cluster_sizes = df["cluster"].value_counts().sort_index()
    
    # Create cluster size visualization
    fig = px.bar(
        x=cluster_sizes.index,
        y=cluster_sizes.values,
        labels={"x": "Cluster ID", "y": "Number of Movies"},
        title="Number of Movies per Cluster"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Cluster characteristics
    st.subheader("🎭 Cluster Characteristics")
    
    # Calculate average metrics per cluster
    cluster_stats = df.groupby("cluster").agg({
        "popularity": "mean",
        "vote_average": "mean",
        "runtime": "mean"
    }).round(2)
    
    # Display cluster statistics
    st.dataframe(
        cluster_stats.style.background_gradient(cmap="RdYlGn"),
        use_container_width=True
    )
    
    # Genre distribution in clusters
    st.subheader("🎬 Genre Distribution by Cluster")
    
    # Get all unique genres
    all_genres = set()
    for genres in df["genres"].dropna():
        all_genres.update(genre.strip() for genre in genres.split(","))
    
    # Calculate genre distribution per cluster
    genre_dist = pd.DataFrame(index=cluster_sizes.index, columns=sorted(all_genres))
    for cluster in cluster_sizes.index:
        cluster_movies = df[df["cluster"] == cluster]
        for genre in all_genres:
            count = cluster_movies["genres"].str.contains(genre, na=False).sum()
            genre_dist.loc[cluster, genre] = count
    
    # Create heatmap
    fig = px.imshow(
        genre_dist,
        labels=dict(x="Genre", y="Cluster", color="Count"),
        title="Genre Distribution Across Clusters",
        aspect="auto"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Cluster exploration
    st.subheader("🔍 Explore Clusters")
    
    selected_cluster = st.selectbox(
        "Select a cluster to explore:",
        options=sorted(df["cluster"].unique())
    )
    
    cluster_movies = df[df["cluster"] == selected_cluster]
    
    # Display top movies in cluster
    st.markdown(f"### Top Movies in Cluster {selected_cluster}")
    
    # Sort by popularity and vote average
    top_movies = cluster_movies.sort_values(
        by=["popularity", "vote_average"],
        ascending=[False, False]
    ).head(10)
    
    # Display movies in columns
    cols = st.columns(min(5, len(top_movies)))
    for i, (_, movie) in enumerate(top_movies.iterrows()):
        with cols[i % 5]:
            st.markdown(f"**{movie['title']}**")
            st.markdown(f"⭐ Rating: `{movie['vote_average']:.1f}`")
            st.markdown(f"📊 Popularity: `{movie['popularity']:.1f}`")
            st.markdown(f"⏱️ Runtime: `{movie['runtime']} min`")
            st.markdown(f"🎭 Genres: {movie['genres']}")
            st.markdown("---")
    
    # Cluster similarity analysis
    st.subheader("🔄 Cluster Similarity Analysis")
    
    # Calculate cluster centroids
    centroids = []
    for cluster in sorted(df["cluster"].unique()):
        cluster_embeddings = np.vstack(
            df[df["cluster"] == cluster]["text_embedding"].values
        )
        centroid = np.mean(cluster_embeddings, axis=0)
        centroids.append(centroid)
    
    # Calculate similarity between clusters
    similarity_matrix = cosine_similarity(centroids)
    
    # Create similarity heatmap
    fig = px.imshow(
        similarity_matrix,
        labels=dict(x="Cluster", y="Cluster", color="Similarity"),
        title="Cluster Similarity Matrix",
        aspect="auto"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Most similar clusters
    st.markdown("### Most Similar Clusters")
    for i in range(len(similarity_matrix)):
        # Get top 3 most similar clusters (excluding self)
        similar_clusters = np.argsort(similarity_matrix[i])[-4:-1][::-1]
        st.markdown(f"**Cluster {i}** is most similar to:")
        for j, sim in zip(similar_clusters, similarity_matrix[i][similar_clusters]):
            st.markdown(f"- Cluster {j} (similarity: {sim:.2f})")
        st.markdown("---")