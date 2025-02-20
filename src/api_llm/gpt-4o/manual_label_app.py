import streamlit as st
import json
import os

# Set page configuration for a wide layout
st.set_page_config(page_title="Labeling App", layout="wide")

# Custom CSS to adjust line spacing, indentation, and widen content
st.markdown("""
    <style>
    /* Reduce the line height */
    .compact {
        line-height: 1.0;
        margin: 0;
        padding: 0;
    }
    /* Add indentation */
    .indent {
        margin-left: 20px;
    }
    /* Add spacing between entries */
    .entry {
        margin-bottom: 20px;
    }
    /* Smaller header for representative names */
    h4.names-header {
        font-size: 18px;
        margin-bottom: 5px;
        margin-top: 10px;
    }
    /* Force container to use full width */
    .stApp {
        max-width: 100%;
        padding: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# File paths
DATA_FILE = "outputs/output_groups.json"
SAVE_FILE = "outputs/human_labelled_data.json"
WEB_RESULTS_FILE = "outputs/web_search_results_stage5.json"

# Load the original JSON data from the new file format (dictionary keyed by group IDs)
with open(DATA_FILE, "r") as file:
    data_dict = json.load(file)

# Convert the dictionary into a list of entries, each including its group_id
data = []
for group_id, group in data_dict.items():
    entry = group.copy()
    entry["group_id"] = group_id
    data.append(entry)

# Load previously saved labels if they exist and are valid JSON; otherwise, create a new list
if os.path.exists(SAVE_FILE) and os.path.getsize(SAVE_FILE) > 0:
    try:
        with open(SAVE_FILE, "r") as file:
            labeled_data = json.load(file)
    except json.JSONDecodeError:
        labeled_data = [{**entry, "label": None} for entry in data]
else:
    labeled_data = [{**entry, "label": None} for entry in data]

# Load web search results if available; otherwise, use an empty dictionary
if os.path.exists(WEB_RESULTS_FILE) and os.path.getsize(WEB_RESULTS_FILE) > 0:
    with open(WEB_RESULTS_FILE, "r") as file:
        web_search_results = json.load(file)
else:
    web_search_results = {}

# Persistent state for labels
if "labels" not in st.session_state:
    st.session_state.labels = [entry["label"] for entry in labeled_data]

# Function to save progress
def save_progress():
    for i, label in enumerate(st.session_state.labels):
        labeled_data[i]["label"] = label
    with open(SAVE_FILE, "w") as file:
        json.dump(labeled_data, file, indent=2)

# Function to render each entry with multi-column layout for candidate metadata and web search results
def render_entry(entry, index):
    st.markdown(f"<div class='entry'>", unsafe_allow_html=True)

    # Entry header with group ID and representative name
    st.markdown(f"<h3>Entry {index + 1} (Group ID: {entry['group_id']})</h3>", unsafe_allow_html=True)
    st.markdown(f"<h4 class='names-header compact'>Representative Name: {entry['name']}</h4>", unsafe_allow_html=True)

    # Group items by candidate org_name
    candidate_items = {}
    for item in entry.get("items", []):
        org_name = item.get('org_name', '')
        candidate_items.setdefault(org_name, []).append(item)
    candidate_names = sorted(candidate_items.keys())

    # Create two columns: left for candidate metadata and right for web search results
    cols = st.columns(2)
    
    # Left column: Candidate names and metadata
    with cols[0]:
        st.markdown("<div class='indent'>", unsafe_allow_html=True)
        st.markdown("<p class='compact'><strong>Candidate Names & Metadata:</strong></p>", unsafe_allow_html=True)
        for candidate in candidate_names:
            st.markdown(f"<p class='compact'><b>{candidate}</b></p>", unsafe_allow_html=True)
            for item in candidate_items[candidate]:
                st.markdown("<div class='indent'>", unsafe_allow_html=True)
                st.markdown(f"<p class='compact'>- Unique ID: {item.get('unique_id', '')}</p>", unsafe_allow_html=True)
                st.markdown(f"<p class='compact'>  Dataset: {item.get('dataset', '')}</p>", unsafe_allow_html=True)
                st.markdown(f"<p class='compact'>  Postcode: {item.get('postcode', '')}</p>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Right column: Web search results for each candidate name
    with cols[1]:
        st.markdown("<div class='indent'>", unsafe_allow_html=True)
        st.markdown("<p class='compact'><strong>Web Search Results:</strong></p>", unsafe_allow_html=True)
        for candidate in candidate_names:
            st.markdown(f"<p class='compact'><b>{candidate}</b></p>", unsafe_allow_html=True)
            results = web_search_results.get(candidate.lower(), [])
            if results:
                for result in results:
                    st.markdown("<div class='indent'>", unsafe_allow_html=True)
                    st.markdown(
                        f"<p class='compact'>- <strong>Title:</strong> <a href='{result.get('url', '')}' target='_blank'>{result.get('title', '')}</a></p>",
                        unsafe_allow_html=True
                    )
                    st.markdown(
                        f"<p class='compact'><strong>URL:</strong> <a href='{result.get('url', '')}' target='_blank'>{result.get('url', '')}</a></p>",
                        unsafe_allow_html=True
                    )
                    st.markdown(f"<p class='compact'><strong>Description:</strong> {result.get('description', '')}</p>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<p class='compact'>No web search results for {candidate}</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Radio buttons for labeling
    label_options = ["Not Labeled", "True", "False"]
    label_index = 0
    if st.session_state.labels[index] is True:
        label_index = 1
    elif st.session_state.labels[index] is False:
        label_index = 2

    label = st.radio(
        f"Label Entry {index + 1}",
        label_options,
        index=label_index,
        key=f"label_{index}",
    )

    # Update the label in session state
    if label == "Not Labeled":
        st.session_state.labels[index] = None
    else:
        st.session_state.labels[index] = (label == "True")

    # Save progress after each change
    save_progress()

    st.markdown("</div>", unsafe_allow_html=True)

# Main loop to display entries
for i, entry in enumerate(data):
    render_entry(entry, i)

st.success("Your progress is saved automatically. You can close the app and return later to pick up where you left off.")
