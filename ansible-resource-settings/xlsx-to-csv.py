import pandas as pd # type: ignore
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--excel', required=True, help='Path to the source Excel file')
    parser.add_argument('--sheet', required=True, help='Name of the sheet to convert')
    parser.add_argument('--csv', required=True, help='Output CSV file path')
    args = parser.parse_args()

    # Load the specified sheet from the Excel file
    df = pd.read_excel(args.excel, sheet_name=args.sheet, dtype=str)

    # Replace blank cells with empty strings to avoid writing 'nan' in CSV
    df.fillna("", inplace=True)

    # Save the DataFrame to CSV with Shift_JIS encoding (cp932) for compatibility with Japanese Excel
    # quoting=1 corresponds to csv.QUOTE_ALL, which puts quotes around all fields
    df.to_csv(args.csv, index=False, encoding='cp932', quoting=1)

if __name__ == "__main__":
    main()
