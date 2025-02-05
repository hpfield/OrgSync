from duckduckgo_search import DDGS

# Define a function to test the text() call
def test_duckduckgo_text_search():
    # Initialize the DDGS instance
    ddgs = DDGS()
    
    # Define the search keywords and parameters
    keywords = "university of oxford department of engineering science"
    region = "uk-en"        # Region for English in the US
    safesearch = "moderate" # Safesearch level
    timelimit = "m"         # Time limit: search for results from the past month
    max_results = 5         # Maximum number of results to return

    # Perform the text search
    results = ddgs.text(
        keywords=keywords,
        region=region,
        safesearch=safesearch,
        timelimit=timelimit,
        max_results=max_results
    )

    # Print out the search results
    print("DuckDuckGo Text Search Results:")
    for result in results:
        print(f"Title: {result.get('title')}")
        print(f"Link: {result.get('href')}")
        print(f"Snippet: {result.get('body')}\n")

# Run the test function
if __name__ == "__main__":
    test_duckduckgo_text_search()
