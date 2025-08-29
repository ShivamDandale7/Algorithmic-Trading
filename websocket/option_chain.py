
import requests
import csv

def getOptionChain(symbol, expiry):
    # Define the URL
    url = "https://www.nseindia.com/api/option-chain-indices?symbol="+symbol

    # Set headers to mimic a browser request
    headers = {
        "User-Agent": "Mozilla/5.0",
    }

    # Send a GET request to the URL with headers
    response = requests.get(url, headers=headers)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the JSON data from the response
        data = response.json()
        #print(data)

        # Extract the relevant data from the JSON response
        records = data['records']['data']
        #print(records)


        target_expiry_date = expiry
        # Create an empty list to store filtered records
        filtered_records = []

        # Iterate through records and filter based on "expiryDate"
        for record in records:
            if record.get("expiryDate") == target_expiry_date:
                filtered_records.append(record)

        # Now, filtered_records contains dictionaries where "expiryDate" is "28-Sep-2023"
        print(filtered_records)


        # Define the CSV file name
        csv_file = "option_chain_data.csv"
        # Define the CSV header fields
        csv_fields = filtered_records[0].keys()
        # Write the filtered data to the CSV file
        with open(csv_file, 'w', newline='') as csvfile:
            csvwriter = csv.DictWriter(csvfile, fieldnames=csv_fields)

            # Write the header
            csvwriter.writeheader()

            # Write the filtered records
            csvwriter.writerows(filtered_records)
        print(f"Filtered data has been saved to '{csv_file}'.")

    else:
        print("Failed to retrieve data. Status code:", response.status_code)

symbol = "NIFTY"
expiry = "03-Jul-2025"  #DD-Mmm-YYYY
getOptionChain(symbol, expiry)