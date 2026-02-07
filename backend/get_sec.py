import json
from typing import Any

import requests


def get_company_cik(company_name: str) -> str | None:
    """
    Search for a company's CIK (Central Index Key) number.

    Args:
        company_name: Name or ticker symbol of the company

    Returns:
        10-digit CIK number or None if not found
    """
    try:
        # Use SEC's company tickers JSON file for reliable lookup
        url = "https://www.sec.gov/files/company_tickers.json"
        headers = {"User-Agent": "SEC Filings Agent contact@example.com"}

        response = requests.get(url, headers=headers)
        companies = response.json()

        # Search for company by ticker or name (case-insensitive)
        search_term = company_name.upper().strip()

        for company in companies.values():
            ticker = company.get("ticker", "").upper()
            title = company.get("title", "").upper()

            # Match by ticker or company name
            if search_term in ticker or search_term in title or ticker == search_term:
                cik = str(company["cik_str"]).zfill(10)
                print(f"Found: {company['title']} (Ticker: {company['ticker']}, CIK: {cik})")
                return cik

        print(f"No company found matching: {company_name}")
        return None

    except Exception as e:
        print(f"Error fetching CIK: {e}")
        return None


def get_sec_filings(company_name: str, filing_type: str | None = None, count: int = 10) -> dict[str, Any]:
    """
    Get recent SEC filings for a company.

    Args:
        company_name: Name or ticker symbol of the company
        filing_type: Optional filter for filing type (e.g., '10-K', '10-Q', '8-K')
        count: Number of filings to retrieve (default: 10, max: 50)

    Returns:
        Dictionary containing company info and list of filings
    """
    try:
        # Get the company's CIK
        cik = get_company_cik(company_name)

        if not cik:
            return {"error": f"Could not find CIK for company: {company_name}"}

        # Fetch recent filings from SEC API
        url = f"https://data.sec.gov/submissions/CIK{cik}.json"
        headers = {"User-Agent": "SEC Filings Agent contact@example.com"}

        response = requests.get(url, headers=headers)
        data = response.json()

        recent_filings = data["filings"]["recent"]
        print(recent_filings)
        # Filter and format filings
        filings = []
        for i in range(min(len(recent_filings["form"]), 50)):
            form = recent_filings["form"][i]

            # Apply filing type filter if specified
            if filing_type and form != filing_type.upper():
                continue

            accession_number = recent_filings["accessionNumber"][i]
            primary_document = recent_filings["primaryDocument"][i]

            # Construct URLs
            # Format: https://www.sec.gov/Archives/edgar/data/{cik_no_leading_zeros}/{accession_no_dashes}/{primary_document}
            cik_no_zeros = cik.lstrip("0")
            accession_no_dashes = accession_number.replace("-", "")

            # The index page shows ALL documents in the filing (exhibits, press releases, etc.)
            filing_index_url = f"https://www.sec.gov/cgi-bin/viewer?action=view&cik={cik_no_zeros}&accession_number={accession_no_dashes}&xbrl_type=v"

            # Direct link to the primary document
            document_url = (
                f"https://www.sec.gov/Archives/edgar/data/{cik_no_zeros}/{accession_no_dashes}/{primary_document}"
            )

            filing_info = {
                "form": form,
                "filing_date": recent_filings["filingDate"][i],
                "report_date": recent_filings["reportDate"][i],
                "accession_number": accession_number,
                "file_number": recent_filings["fileNumber"][i],
                "primary_document": primary_document,
                "filing_url": filing_index_url,  # Full filing package with all exhibits
                "document_url": document_url,  # Direct link to primary document
            }

            filings.append(filing_info)

            if len(filings) >= count:
                break

        return {"company": data["name"], "cik": cik, "filings": filings}

    except Exception as e:
        return {"error": f"Error fetching SEC filings: {e!s}"}


if __name__ == "__main__":
    company_name = "AAPL"  # Apple Inc. - You can change this to any company name or ticker

    print("=" * 80)
    print("Fetching 10-K Filings (Annual Reports)")
    print("=" * 80)
    filings_10k = get_sec_filings(company_name, filing_type="10-K", count=5)
    print(json.dumps(filings_10k, indent=2))

    print("\n" + "=" * 80)
    print("Fetching 8-K Filings (Material Events - may include earnings announcements)")
    print("=" * 80)
    filings_8k = get_sec_filings(company_name, filing_type="8-K", count=10)
    print(json.dumps(filings_8k, indent=2))

    print("\n" + "=" * 80)
    print("NOTE: Earnings call transcripts are not directly available through SEC EDGAR.")
    print("For earnings call transcripts, you would need to use services like:")
    print("  - Seeking Alpha API")
    print("  - AlphaSense")
    print("  - Company investor relations websites")
    print("  - Bloomberg Terminal")
    print("=" * 80)
