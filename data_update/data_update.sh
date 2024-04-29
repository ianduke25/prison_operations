#!/bin/bash

# Get directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Navigate to the directory containing Python script and CSV file
cd "$SCRIPT_DIR/.."
echo "Changed directory successfully"

git pull
echo "Pulled success"

cd data_update
echo "Changed directory successfully"

python scrape_concatenate.py || exit 1
echo "Scrape done"

file_to_remove="forecast.csv"
rm -f "$file_to_remove"

# Check if the file was successfully removed
if [ $? -eq 0 ]; then
    echo "File '$file_to_remove' removed successfully."
    python future_closure_predictions.py
else
    echo "Failed to remove file '$file_to_remove'. Exiting script."
    exit 1
fi
echo "updated forecast.csv"

cd "$SCRIPT_DIR/.."
echo "Changed directory successfully"

git add *
git commit -m "Update master CSV file and predictions"
git push
echo "File pushed to GitHub"
