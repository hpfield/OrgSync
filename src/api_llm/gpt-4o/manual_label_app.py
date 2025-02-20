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
    /* Smaller header for representative names */
    h4.names-header {
        font-size: 18px;
        margin-bottom: 5px;
        margin-top: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# File paths
DATA_FILE = "outputs/output_groups.json"
SAVE_FILE = "outputs/human_labelled_data.json"

# Load the original JSON data from the new file format (dictionary keyed by group IDs)
with open(DATA_FILE, "r") as file:
    data_dict = json.load(file)

# Convert the dictionary into a list of entries, each including its group_id
data = []
for group_id, group in data_dict.items():
    entry = group.copy()
    entry["group_id"] = group_id
    data.append(entry)

# Load previously saved labels if they exist, else create new entries with a label field
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

    # Entry header with group ID
    st.markdown(f"<h3>Entry {index + 1} (Group ID: {entry['group_id']})</h3>", unsafe_allow_html=True)

    # Representative Name header
    st.markdown(f"<h4 class='names-header compact'>Representative Name: {entry['name']}</h4>", unsafe_allow_html=True)

    # Display number of items
    num_items = len(entry.get("items", []))
    st.markdown(f"<p class='compact'><strong>Number of Items:</strong> {num_items}</p>", unsafe_allow_html=True)

    # List out each item in the group
    st.markdown("<div class='indent'>", unsafe_allow_html=True)
    st.markdown("<p class='compact'><strong>Items:</strong></p>", unsafe_allow_html=True)
    for item in entry.get("items", []):
        st.markdown("<div class='indent'>", unsafe_allow_html=True)
        st.markdown(f"<p class='compact'>- Org Name: {item.get('org_name', '')}</p>", unsafe_allow_html=True)
        st.markdown(f"<p class='compact'>  Unique ID: {item.get('unique_id', '')}</p>", unsafe_allow_html=True)
        st.markdown(f"<p class='compact'>  Dataset: {item.get('dataset', '')}</p>", unsafe_allow_html=True)
        st.markdown(f"<p class='compact'>  Postcode: {item.get('postcode', '')}</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
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
