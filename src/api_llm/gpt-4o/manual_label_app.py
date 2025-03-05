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
DATA_FILE = "outputs/final_groups_stage11.json" # "outputs/output_groups.json"
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

# Initialize session state for labels if not present
if "labels" not in st.session_state:
    st.session_state.labels = [entry["label"] for entry in labeled_data]

# Initialize session state for pagination
if "page" not in st.session_state:
    st.session_state.page = 0

chunk_size = 50
start_index = st.session_state.page * chunk_size
end_index = start_index + chunk_size
current_data = data[start_index:end_index]

def save_current_chunk():
    # Update labels only for the current chunk and save the entire labeled_data
    for i in range(start_index, min(end_index, len(st.session_state.labels))):
        labeled_data[i]["label"] = st.session_state.labels[i]
    with open(SAVE_FILE, "w") as file:
        json.dump(labeled_data, file, indent=2)
    st.success("Current chunk saved!")

def render_entry(entry, global_index):
    st.markdown("<div class='entry'>", unsafe_allow_html=True)
    st.markdown(f"<h3>Entry {global_index + 1} (Group ID: {entry['group_id']})</h3>", unsafe_allow_html=True)
    st.markdown(f"<h4 class='names-header compact'>Representative Name: {entry['name']}</h4>", unsafe_allow_html=True)

    # Group items by candidate org_name
    candidate_items = {}
    for item in entry.get("items", []):
        org_name = item.get('org_name', '')
        candidate_items.setdefault(org_name, []).append(item)
    candidate_names = sorted(candidate_items.keys())

    # Create two columns: left for candidate metadata and right for web search results
    cols = st.columns(2)
    
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
    if st.session_state.labels[global_index] is True:
        label_index = 1
    elif st.session_state.labels[global_index] is False:
        label_index = 2

    label = st.radio(
        f"Label Entry {global_index + 1}",
        label_options,
        index=label_index,
        key=f"label_{global_index}",
    )

    # Update the label in session state
    if label == "Not Labeled":
        st.session_state.labels[global_index] = None
    else:
        st.session_state.labels[global_index] = (label == "True")

    st.markdown("</div>", unsafe_allow_html=True)

# Render only the current chunk (50 entries)
for i, entry in enumerate(current_data):
    global_index = start_index + i
    render_entry(entry, global_index)

st.markdown("---")
# Button to save the current chunk's labels
if st.button("Save Current Chunk"):
    save_current_chunk()

# Navigation buttons for pagination
col1, col2, col3 = st.columns(3)
if col1.button("Previous 50"):
    if st.session_state.page > 0:
        st.session_state.page -= 1
if col3.button("Next 50"):
    if end_index < len(data):
        st.session_state.page += 1

st.success("Changes are saved when you click the save button. Use the navigation buttons to load more datapoints.")
