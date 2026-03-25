import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime

st.set_page_config(page_title="Netflix Dashboard", layout="wide")

# simple dark background css
st.markdown("""
<style>
body { background-color: #111; color: white; }
</style>
""", unsafe_allow_html=True)

# load data
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE, "data", "netflix_titles_featured.csv")

@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH)
    return df

df = load_data()

# ---- SIDEBAR FILTERS ----
st.sidebar.title("Filters")

year_min = int(df["release_year"].min())
year_max = int(df["release_year"].max())
year_range = st.sidebar.slider("Release Year", year_min, year_max, (2000, 2020))

content_type = st.sidebar.selectbox("Type", ["All", "Movie", "TV Show"])

genres = sorted(df["primary_genre"].dropna().unique())
genre_pick = st.sidebar.multiselect("Genre", genres)

all_countries = []
for entry in df["countries"].dropna():
    for c in entry.split(","):
        all_countries.append(c.strip())
all_countries = sorted(set(all_countries))
country_pick = st.sidebar.multiselect("Country", all_countries)

ratings = sorted(df["rating_category"].dropna().unique())
rating_pick = st.sidebar.multiselect("Rating", ratings)

# ---- APPLY FILTERS ----
fdf = df.copy()
fdf = fdf[fdf["release_year"] >= year_range[0]]
fdf = fdf[fdf["release_year"] <= year_range[1]]

if content_type != "All":
    fdf = fdf[fdf["type"] == content_type]

if genre_pick:
    fdf = fdf[fdf["primary_genre"].isin(genre_pick)]

if country_pick:
    mask = fdf["countries"].str.contains("|".join(country_pick), case=False, na=False)
    fdf = fdf[mask]

if rating_pick:
    fdf = fdf[fdf["rating_category"].isin(rating_pick)]

# ---- PAGE TITLE ----
st.title("Netflix Dashboard")
st.write(f"Showing {len(fdf)} titles from {year_range[0]} to {year_range[1]}")

# ---- TABS ----
tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Trends & Insights", "What to Watch Now?", "Explore Shows Worldwide"])


# TAB 1 - OVERVIEW

with tab1:
    if fdf.empty:
        st.warning("No results/titles found. Try changing the filters.")
    else:
        # metrics row
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Titles", len(fdf))
        col2.metric("Movies Count", (fdf["type"] == "Movie").sum())
        col3.metric("TV Shows Count", (fdf["type"] == "TV Show").sum())
        col4.metric("Average Release Year", int(fdf["release_year"].mean()))

        st.divider()

        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader("Most Popular Genres")
            top_genres = fdf["primary_genre"].value_counts().head(10)
            fig, ax = plt.subplots()
            ax.barh(top_genres.index[::-1], top_genres.values[::-1], color="red")
            ax.set_xlabel("Count")
            st.pyplot(fig)
            plt.close()

        with col_right:
            st.subheader("Top Producing Countries")
            country_series = fdf["countries"].dropna().str.split(",").explode().str.strip()
            top_countries = country_series.value_counts().head(10)
            fig, ax = plt.subplots()
            ax.barh(top_countries.index[::-1], top_countries.values[::-1], color="gray")
            ax.set_xlabel("Count")
            st.pyplot(fig)
            plt.close()

        st.divider()
        st.subheader("Content Released Over the Year")
        yearly = fdf.groupby(["release_year", "type"]).size().unstack(fill_value=0)
        fig, ax = plt.subplots(figsize=(10, 3))
        for col in yearly.columns:
            color = "red" if col == "Movie" else "gray"
            ax.plot(yearly.index, yearly[col], label=col, color=color, marker="o", markersize=3)
        ax.set_xlabel("Year")
        ax.legend()
        st.pyplot(fig)
        plt.close()



# TAB 2 - INSIGHTS

with tab2:
    if fdf.empty:
        st.warning("No data available for current filters.")
    else:
        st.subheader("Top Genre Per Year")
        # find the most common genre each year
        top_genre_yearly = (
            fdf.groupby(["release_year", "primary_genre"])
            .size()
            .reset_index(name="count")
            .sort_values("count", ascending=False)
            .groupby("release_year")
            .first()
            .reset_index()
        )
        fig, ax = plt.subplots(figsize=(12, 4))
        bars = ax.bar(top_genre_yearly["release_year"], top_genre_yearly["count"], color="red")
        for bar, genre in zip(bars, top_genre_yearly["primary_genre"]):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                    genre, ha="center", fontsize=7, rotation=90, color="white")
        ax.set_xlabel("Year")
        ax.set_ylabel("Titles")
        st.pyplot(fig)
        plt.close()

        st.divider()

        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader("Audience Ratings Distribution")
            rating_counts = fdf["rating_category"].value_counts()
            fig, ax = plt.subplots()
            ax.pie(rating_counts, labels=rating_counts.index, autopct="%1.0f%%", startangle=140)
            st.pyplot(fig)
            plt.close()

            # table showing breakdown
            rating_table = fdf.groupby("rating_category").agg(
                Total=("title", "count"),
                Movies=("type", lambda x: (x == "Movie").sum()),
                TV_Shows=("type", lambda x: (x == "TV Show").sum())
            ).reset_index()
            st.dataframe(rating_table, hide_index=True)

        with col_right:
            st.subheader("Production Type")
            if "production_type" in fdf.columns:
                prod_counts = fdf["production_type"].value_counts()
                fig, ax = plt.subplots()
                ax.barh(prod_counts.index[::-1], prod_counts.values[::-1], color="gray")
                ax.set_xlabel("Count")
                st.pyplot(fig)
                plt.close()
            else:
                st.info("Production type data is not available in this dataset.")

        st.divider()
        st.subheader("Genre Trends Over Time")
        top8_genres = fdf["primary_genre"].value_counts().head(8).index
        genre_yearly = fdf.groupby(["release_year", "primary_genre"]).size().unstack(fill_value=0)
        genre_yearly = genre_yearly[[g for g in top8_genres if g in genre_yearly.columns]]
        fig, ax = plt.subplots(figsize=(12, 4))
        genre_yearly.plot(kind="area", ax=ax, stacked=True, alpha=0.7, colormap="Reds")
        ax.set_xlabel("Year")
        ax.set_ylabel("Titles")
        ax.legend(loc="upper left", fontsize=9)
        st.pyplot(fig)
        plt.close()



# TAB 3 - COGNITIVE LOAD ADVISOR

with tab3:
    st.title("What Should I Watch Right Now?")
    st.write("This tab suggests what to watch based on the time of day and your mental energy level.")

    # define time-based profiles
    profiles = {
        "Peak Focus": {
            "hours": list(range(8, 12)),
            "genres": ["Documentary", "Drama", "Crime", "History", "Thriller"],
            "description": "Morning focus time — your brain can handle complex and heavy content.",
            "emoji": "🔥"
        },
        "Post-Lunch Dip": {
            "hours": list(range(13, 16)),
            "genres": ["Comedy", "Animation", "Reality-TV"],
            "description": "After lunch slump — keep it light and easy.",
            "emoji": "😌"
        },
        "Afternoon Recharge": {
            "hours": list(range(16, 19)),
            "genres": ["Action", "Adventure", "Sci-Fi", "Fantasy"],
            "description": "Energy picks up again — good time for fast-paced content.",
            "emoji": "⚡"
        },
        "Evening Unwind": {
            "hours": list(range(19, 22)),
            "genres": ["Romantic", "Drama", "Music"],
            "description": "Time to relax a bit. Pick something calm, emotional, or feel-good.",
            "emoji": "🌇"
        },
        "Wind-Down": {
            "hours": list(range(22, 24)),
            "genres": ["Documentary", "Animation", "Comedy"],
            "description": "Close to bedtime — avoid thrillers, keep it calm.",
            "emoji": "🌙"
        },
        "Late Night": {
            "hours": list(range(0, 8)),
            "genres": ["Comedy", "Animation", "Reality-TV"],
            "description": "Late night mode — easy breezy content only.",
            "emoji": "🌃"
        },
    }

    def get_profile(hour):
        for name, p in profiles.items():
            if hour in p["hours"]:
                return name
        return "Evening Unwind"

    current_hour = datetime.now().hour
    detected_profile = get_profile(current_hour)

    current_time_str = datetime.now().strftime("%I:%M %p")
    st.write(f"Current time: {current_time_str}")
    st.write(f"**Detected profile:** {profiles[detected_profile]['emoji']} {detected_profile}")

    # allow manual override
    override = st.checkbox("Change time manually")
    if override:
        manual_hour = st.slider("Hour of day", 0, 23, current_hour)
        active_profile = get_profile(manual_hour)
    else:
        active_profile = detected_profile

    p = profiles[active_profile]
    st.info(f"{p['emoji']} **{active_profile}** — {p['description']}")
    st.write("**Recommended genres:**", ", ".join(p["genres"]))

    st.divider()
    st.subheader("Recommended Titles")

    # get matching titles
    recs = df[df["primary_genre"].str.contains("|".join(p["genres"]), case=False, na=False)]
    recs = recs.sort_values("release_year", ascending=False).head(8)

    if recs.empty:
        st.warning("No recommendations found for this mood.")
    else:
        cols = st.columns(4)
        for i, (_, row) in enumerate(recs.iterrows()):
            with cols[i % 4]:
                st.write(f"**{row['title']}**")
                st.caption(f"{row['type']} · {int(row['release_year'])}")
                st.caption(row.get("primary_genre", ""))

    st.divider()
    st.subheader("Better to avoid Now")
    all_rec_genres = set(p["genres"])
    all_genres_list = list({g for pr in profiles.values() for g in pr["genres"]})
    avoid = [g for g in all_genres_list if g not in all_rec_genres]
    st.write(", ".join(avoid[:8]))



# TAB 4 - Watch Around the World

with tab4:
    st.title("Watch Around the World")
    st.write("Explore shows from different countries and track what you've watched.")

    country_flags = {
        "United States": "🇺🇸", "India": "🇮🇳", "United Kingdom": "🇬🇧",
        "Japan": "🇯🇵", "South Korea": "🇰🇷", "France": "🇫🇷",
        "Canada": "🇨🇦", "Spain": "🇪🇸", "Germany": "🇩🇪", "Mexico": "🇲🇽",
        "Brazil": "🇧🇷", "Australia": "🇦🇺", "Italy": "🇮🇹",
    }

    @st.cache_data
    def build_passport(source):
        exploded = source.assign(country=source["countries"].str.split(",")).explode("country")
        exploded["country"] = exploded["country"].str.strip()
        exploded = exploded[exploded["country"].notna() & (exploded["country"] != "")]

        rows = []
        for country, group in exploded.groupby("country"):
            # pick up to 3 titles per country
            picked = []
            for ctype in ["Movie", "TV Show"]:
                sub = group[group["type"] == ctype].sort_values("release_year", ascending=False)
                if not sub.empty:
                    picked.append(sub.iloc[0])
                if len(picked) >= 2:
                    break
            if len(picked) < 3:
                seen_idx = [r.name for r in picked]
                rest = group[~group.index.isin(seen_idx)].sort_values("release_year", ascending=False)
                if not rest.empty:
                    picked.append(rest.iloc[0])

            for r in picked:
                rows.append({
                    "country": country,
                    "flag": country_flags.get(country, "🌐"),
                    "title": r["title"],
                    "type": r["type"],
                    "genre": r.get("primary_genre", "—"),
                    "year": int(r["release_year"]),
                    "rating": r.get("rating_category", "—"),
                })

        return pd.DataFrame(rows).sort_values("country").reset_index(drop=True)

    # init session state
    if "passport_df" not in st.session_state:
        st.session_state.passport_df = build_passport(df)
    if "watched" not in st.session_state:
        st.session_state.watched = set()

    passport = st.session_state.passport_df
    watched = st.session_state.watched

    # progress stats
    total_titles = len(passport)
    watched_count = sum(1 for _, r in passport.iterrows() if f"{r['country']}||{r['title']}" in watched)
    total_countries = passport["country"].nunique()
    watched_countries = len({r["country"] for _, r in passport.iterrows() if f"{r['country']}||{r['title']}" in watched})
    pct = int((watched_count / total_titles) * 100) if total_titles > 0 else 0

    st.write(f"**Progress:** {watched_count} / {total_titles} titles · {watched_countries} / {total_countries} countries · {pct}% done")
    st.progress(pct / 100)

    st.divider()

    # search and filter controls
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search = st.text_input("Search by country or title", placeholder="e.g. 'Japan' or 'Dark'")
    with col2:
        show_filter = st.selectbox("Show", ["All", "Not Watched", "Watched"])
    with col3:
        if st.button(" Start New Challenge 🔄"):
            build_passport.clear()
            st.session_state.passport_df = build_passport(df)
            st.rerun()

    # filter the list
    view = passport.copy()
    if search:
        q = search.lower()
        view = view[
            view["country"].str.lower().str.contains(q, na=False) |
            view["title"].str.lower().str.contains(q, na=False)
        ]

    def is_watched(row):
        return f"{row['country']}||{row['title']}" in watched

    if show_filter == "Unwatched":
        view = view[~view.apply(is_watched, axis=1)]
    elif show_filter == "Watched":
        view = view[view.apply(is_watched, axis=1)]

    st.divider()

    if view.empty:
        st.info("No matches found. Try a different search.")
    else:
        changed = False
        current_country = None

        for _, row in view.iterrows():
            uid = f"{row['country']}||{row['title']}"
            already_watched = uid in watched

            # show country header when it changes
            if row["country"] != current_country:
                current_country = row["country"]
                st.markdown(f"**{row['flag']} {row['country']}**")

            checked = st.checkbox(
                f"{row['title']} · {row['type']} · {row['genre']} · {row['year']}",
                value=already_watched,
                key=uid
            )

            if checked and uid not in watched:
                watched.add(uid)
                changed = True
            elif not checked and uid in watched:
                watched.discard(uid)
                changed = True

        if changed:
            st.session_state.watched = watched
            st.rerun()