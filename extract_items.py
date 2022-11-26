from sec_api import ExtractorApi

def extract_items(filing_url, text_file):
    extract_api = ExtractorApi("API-KEY")

    items = ["1", "1A", "7"]

    for item in items:
        section_text = extract_api.get_section(filing_url, item, "text")

        with open("items/" + text_file.split(".")[0] + "_" + item, "w") as f:
            f.write(section_text)

if __name__ == "__main__":
    extract_items()