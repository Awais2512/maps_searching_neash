import os
import csv
from pathlib import Path

def merge_profession_csvs(input_dir, output_file):
    # Create output directory if needed
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Get all CSV files in input directory
    csv_files = list(Path(input_dir).glob('*.csv'))
    
    if not csv_files:
        print("No CSV files found in input directory")
        return

    # Get fieldnames from first file (assuming all have same structure)
    with open(csv_files[0], 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames + ['Profession']  # Add new column

    # Process all files
    with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        for csv_file in csv_files:
            # Extract profession name from filename (without extension)
            profession = csv_file.stem.replace('_', ' ').title()
            
            with open(csv_file, 'r', encoding='utf-8') as infile:
                reader = csv.DictReader(infile)
                
                for row in reader:
                    # Add profession column to each row
                    row['Profession'] = profession
                    writer.writerow(row)

            print(f"Processed: {csv_file.name}")

    print(f"\nMerged {len(csv_files)} files into {output_file}")

# Usage
merge_profession_csvs(
    input_dir='processed_csv',
    output_file='merged_data/combined_professions.csv'
)