import streamlit as st
import json
import os

# Custom CSS to adjust line spacing and indentation
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
    /* Smaller header for names */
    h4.names-header {
        font-size: 18px;
        margin-bottom: 5px;
        margin-top: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# File paths
DATA_FILE = "outputs/final_output_with_context.json"
SAVE_FILE = "labeled_data.json"

# Load the original JSON data
with open(DATA_FILE, "r") as file:
    data = json.load(file)

# Load previously saved labels if they exist
if os.path.exists(SAVE_FILE):
    with open(SAVE_FILE, "r") as file:
        labeled_data = json.load(file)
else:
    labeled_data = [{**entry, "label": None} for entry in data]

# Persistent state for labels
if "labels" not in st.session_state:
    st.session_state.labels = [entry["label"] for entry in labeled_data]

# Function to save progress
def save_progress():
    for i, label in enumerate(st.session_state.labels):
        labeled_data[i]["label"] = label
    with open(SAVE_FILE, "w") as file:
        json.dump(labeled_data, file, indent=2)

# Function to render each entry
def render_entry(entry, index):
    st.markdown(f"<div class='entry'>", unsafe_allow_html=True)

    # Entry header
    st.markdown(f"<h3>Entry {index + 1}</h3>", unsafe_allow_html=True)

    # Names header (smaller than Entry header)
    st.markdown(f"<h4 class='names-header compact'>Names: {', '.join(entry['names'])}</h4>", unsafe_allow_html=True)

    # Organisation Type
    st.markdown(f"<p class='compact'><strong>Organisation Type:</strong> {entry['organisation_type']}</p>", unsafe_allow_html=True)
    
    # Indentation for components
    st.markdown("<div class='indent'>", unsafe_allow_html=True)
    st.markdown(f"<p class='compact'><strong>Names with Search Results:</strong></p>", unsafe_allow_html=True)
    for name_with_results in entry.get("names_with_search_results", []):
        # Name sub-header
        st.markdown(f"<h5 class='compact indent'>- Name: {name_with_results['name']}</h5>", unsafe_allow_html=True)
        st.markdown("<div class='indent'>", unsafe_allow_html=True)
        st.markdown(f"<p class='compact'><strong>Web Search Results:</strong></p>", unsafe_allow_html=True)
        for result in name_with_results.get("web_search_results", []):
            st.markdown("<div class='indent'>", unsafe_allow_html=True)
            st.markdown(
                f"<p class='compact'>- <strong>Title:</strong> "
                f"<a href='{result.get('url', '')}' target='_blank'>{result.get('title', '')}</a></p>",
                unsafe_allow_html=True
            )
            st.markdown(
                f"<p class='compact'><strong>URL:</strong> "
                f"<a href='{result.get('url', '')}' target='_blank'>{result.get('url', '')}</a></p>",
                unsafe_allow_html=True
            )
            st.markdown(f"<p class='compact'><strong>Description:</strong> {result.get('description', '')}</p>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)  # Close inner indent
        st.markdown("</div>", unsafe_allow_html=True)  # Close web search results indent
    st.markdown("</div>", unsafe_allow_html=True)  # Close names with search results indent

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
        st.session_state.labels[index] = label == "True"

    # Save progress after each change
    save_progress()

    st.markdown("</div>", unsafe_allow_html=True)  # Close the entry div

# Main loop to display entries
for i, entry in enumerate(data):
    render_entry(entry, i)

st.success("Your progress is saved automatically. You can close the app and return later to pick up where you left off.")
