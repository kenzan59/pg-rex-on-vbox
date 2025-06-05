import csv
import argparse
import re

def excel_cell_to_index(cell):
    """
    Convert Excel cell notation (e.g., 'F77') to zero-based (row_index, col_index).
    """
    match = re.fullmatch(r"([A-Z]+)(\d+)", cell.upper())
    if not match:
        raise ValueError(f"Invalid cell format: {cell}")
    col_letters, row_number = match.groups()

    col_index = 0
    for char in col_letters:
        col_index = col_index * 26 + (ord(char) - ord('A') + 1)
    col_index -= 1  # zero-based
    row_index = int(row_number) - 1  # zero-based
    return row_index, col_index

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv', required=True, help='Path to CSV file')
    parser.add_argument('--set', action='append', required=True, help='Cell=Value pairs, e.g., F77=192.168.0.100')
    args = parser.parse_args()

    # Read the entire CSV file
    with open(args.csv, 'r', encoding='cp932') as f:
        rows = list(csv.reader(f))

    # Apply each Cell=Value pair
    for pair in args.set:
        if '=' not in pair:
            raise ValueError(f"Invalid format for --set: {pair}. Expected format CELL=VALUE.")
        cell, value = pair.split('=', 1)
        row_index, col_index = excel_cell_to_index(cell)

        # Ensure enough rows
        while len(rows) <= row_index:
            rows.append([])

        # Ensure enough columns in this row
        while len(rows[row_index]) <= col_index:
            rows[row_index].append("")

        # Set the value
        rows[row_index][col_index] = value

    # Write the updated CSV
    with open(args.csv, 'w', encoding='cp932', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)

if __name__ == "__main__":
    main()
