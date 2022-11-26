from sec_api import QueryApi, RenderApi
import pandas as pd
import regex as re
import os

def download_text_file(url, file_name):
    renderApi = RenderApi(api_key="API Key")
    save_path = "filings/"
    filing_content = renderApi.get_filing(url)
    file_path = os.path.join(save_path, file_name)

    with open(file_path, 'w') as f:
        f.write(filing_content)

def download_filings():
    company_names = []
    with open("company_names.txt", "r") as f:
        company_names = f.read().splitlines()

    queryApi = QueryApi(api_key="API Key")

    company_filings = pd.DataFrame(columns=['Company', 'Text', 'URL'])
    missing_annual_reports = []

    for company in company_names:
        query = {
            "query": { "query_string": { 
                "query": f"companyName:\"{company}\" AND formType:\"10-K\"",
                "time_zone": "America/New_York"
            } },
            "from": "0",
            "size": "1",
            "sort": [{ "filedAt": { "order": "desc" } }]
        }

        response = queryApi.get_filings(query)

        if len(response['filings']) == 0:
            missing_annual_reports.append(company)
            continue

        if response["filings"][0]["formType"] == "10-K/A":
            query = {
                "query": { "query_string": { 
                    "query": f"companyName:\"{company}\" AND formType:\"10-K\"",
                    "time_zone": "America/New_York"
                } },
                "from": "1",
                "size": "1",
                "sort": [{ "filedAt": { "order": "desc" } }]
            }

            response = queryApi.get_filings(query)

        text_url = response["filings"][0]['linkToTxt']
        file_name = re.search(r"[^/\\&\?]+\.\w{3,4}(?=([\?&].*$|$))", text_url).group()

        company_filings.loc[len(company_filings.index)] = [company, file_name, text_url]
        download_text_file(text_url, file_name)

    company_filings.to_csv("filings/company_filings.csv")

    return missing_annual_reports

if __name__ == "__main__":
    # For testing purpose
    missing_annual_reports = download_filings()

    with open("missing_annual_reports_list.txt", "w") as f:
        f.write("\n".join(missing_annual_reports))