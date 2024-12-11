import json

# Load JSON data
with open("outputs/final_output_with_context.json", "r") as file:
    data = json.load(file)

# Generate Markdown
output = []
for i, item in enumerate(data):
    output.append(f"## Entry {i+1}")
    output.append(f"**Names:** {', '.join(item['names'])}")
    output.append(f"**Organisation Type:** {item['organisation_type']}")
    output.append(f"### Web Search Results")
    for name in item["names_with_search_results"]:
        output.append(f"- **Name:** {name['name']}")
        for result in name.get("web_search_results", []):
            output.append(f"  - **Title:** {result['title']}")
            output.append(f"    **URL:** {result['url']}")
            output.append(f"    **Description:** {result['description']}")
    output.append(f"- [ ] True")
    output.append(f"- [ ] False")
    output.append("\n---\n")

# Save Markdown to file
with open("output.md", "w") as md_file:
    md_file.write("\n".join(output))
