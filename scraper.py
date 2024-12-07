from bs4 import BeautifulSoup
import requests
import csv
import os


def fetch_listings(search_keywords, page_number):
    """Fetch listings from eBay based on search keywords and page number."""
    search_query = "+".join(search_keywords)
    url = (
        f"https://www.ebay.com/sch/i.html?_nkw={search_query}&_sacat=0&rt=nc&LH_Sold=1&LH_Complete=1&_pgn={page_number}"
    )
    response = requests.get(url)
    doc = BeautifulSoup(response.text, "html.parser")
    return doc.find(class_="srp-results srp-list clearfix")


def parse_listing(item):
    """Extract title, price, date, link, and condition from a listing."""
    title = item.find(class_="s-item__title").text.lower()
    price = item.find(class_="s-item__price").text
    date = item.find(class_="POSITIVE").string.replace("Sold", "").strip()  # Use raw date
    link = item.find(class_="s-item__link")['href'].split("?")[0]
    condition = item.find(class_="s-item__subtitle").text.lower() if item.find(class_="s-item__subtitle") else "Unknown"
    return title, price, date, link, condition


def is_valid_title(title, search_keywords):
    """Check if the title contains all search keywords as standalone words."""
    title_words = title.split()
    for keyword in search_keywords:
        if keyword not in title_words:
            return False
    return True


def process_price(price):
    """Clean and process the price string into a numeric value."""
    price = price.replace("$", "").replace(",", "")
    if 'to' in price:
        price = sum(float(num) for num in price.split() if num != 'to') / 2
    return round(float(price), 2)


def scrape_ebay_for_term(search_term, month_price_dict):
    """Scrape eBay for the given search term and populate the month-price map."""
    search_keywords = search_term.lower().split()

    for page_number in range(1, 14):
        listings_section = fetch_listings(search_keywords, page_number)
        if not listings_section:
            continue

        listings = listings_section.find_all("li", class_="s-item s-item__pl-on-bottom")
        for item in listings:
            try:
                title, price, date, link, condition = parse_listing(item)
                if is_valid_title(title, search_keywords):
                    price_value = process_price(price)
                    # Only consider prices between $10 and $900
                    if 10 < price_value < 900:
                        if date not in month_price_dict:
                            month_price_dict[date] = []
                        month_price_dict[date].append(price_value)
            except ValueError:
                continue


def main():
    input_file = "search_terms.csv"  # Input file containing search terms
    output_file = "Average_Prices_By_Day.csv"  # Summary output file

    if not os.path.exists(input_file):
        print(f"Error: '{input_file}' not found. Make sure the file exists.")
        return

    # Prepare data structures for summary
    summary_data = {}

    # Process each search term
    with open(input_file, "r", newline="", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if row:  # Ignore empty rows
                search_term = row[0].strip()  # Extract the search term from the first column
                if search_term:
                    print(f"Processing: {search_term}")
                    month_price_dict = {}  # Store prices grouped by date
                    scrape_ebay_for_term(search_term, month_price_dict)

                    # Calculate average prices for each date
                    daily_averages = {
                        date: round(sum(prices) / len(prices), 2)
                        for date, prices in month_price_dict.items()
                    }
                    summary_data[search_term] = daily_averages

    # Write summary data to the output CSV file
    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)

        # Generate a header with all unique dates from all search terms
        all_dates = sorted({date for averages in summary_data.values() for date in averages.keys()})
        header = ["CPU Name"] + all_dates
        writer.writerow(header)

        # Write rows for each search term with corresponding averages
        for search_term, daily_averages in summary_data.items():
            row = [search_term] + [daily_averages.get(date, "") for date in all_dates]
            writer.writerow(row)

    print(f"Summary data written to {output_file}")


if __name__ == "__main__":
    main()