#!/bin/bash
# Downloads all .zip and .tgz files from a Google Drive folder and extracts them
# into separate subdirectories based on their names.

# --- Configuration ---
set -e  # Exit immediately if a command fails

OUTPUT_DIR="nuscenes_data"

# Google Drive Folder ID - REPLACE THIS with your actual Google Drive folder ID
# To get the folder ID: Open the folder in Google Drive, copy the URL
# The link will look like: https://drive.google.com/drive/folders/FOLDER_ID_HERE
# Extract the FOLDER_ID_HERE part and paste it below

GDRIVE_FOLDER_ID="1-3pgeENOXzrD0HeMnH8z9GOHVBBhHgfu"

# --- Step 1: Check if gdown is installed ---
echo "--- Checking for gdown (Google Drive downloader) ---"
if ! command -v gdown &> /dev/null; then
    echo "gdown is not installed. Installing gdown..."
    pip install gdown --break-system-packages
fi

echo ""
echo "--- Starting nuScenes dataset download from Google Drive folder ---"
echo "NOTE: If the folder is set to 'Restricted', you will receive an email request."
echo "      Please approve the access request and re-run this script."
echo ""

# --- Step 2: Create Directory Structure ---
echo "--> Creating output directory structure..."
rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR/downloads"

# --- Step 3: Download entire folder from Google Drive ---
echo ""
echo "--> Downloading all files from Google Drive folder..."
gdown --folder "https://drive.google.com/drive/folders/${GDRIVE_FOLDER_ID}" -O "$OUTPUT_DIR/downloads" --remaining-ok

# --- Step 4: Find all .zip and .tgz files ---
echo ""
echo "--> Searching for .zip and .tgz files in downloads..."

# Find all .tgz files
TGZ_FILES=$(find "$OUTPUT_DIR/downloads" -type f -name "*.tgz")
# Find all .zip files
ZIP_FILES=$(find "$OUTPUT_DIR/downloads" -type f -name "*.zip")

# Check if any files were found
if [[ -z "$TGZ_FILES" ]] && [[ -z "$ZIP_FILES" ]]; then
    echo "ERROR: No .zip or .tgz files found in the downloaded folder."
    exit 1
fi

echo "--> Found the following archive files:"
for file in $TGZ_FILES $ZIP_FILES; do
    echo "    - $(basename "$file")"
done

# --- Step 5: Extract files based on their names ---
echo ""
echo "--> Extracting archives into organized subdirectories..."

# Process .tgz files
for tgz_file in $TGZ_FILES; do
    filename=$(basename "$tgz_file")
    echo ""
    echo "--> Processing: $filename"
    
    # Determine destination based on filename
    if [[ "$filename" == *"mini"* ]]; then
        dest_dir="$OUTPUT_DIR/mini"
        echo "    Extracting to: mini/"
    elif [[ "$filename" == *"trainval"* ]]; then
        dest_dir="$OUTPUT_DIR/trainval"
        echo "    Extracting to: trainval/"
    elif [[ "$filename" == *"test"* ]]; then
        dest_dir="$OUTPUT_DIR/test"
        echo "    Extracting to: test/"
    else
        # Generic extraction based on filename (remove extension)
        dest_name=$(echo "$filename" | sed 's/.tgz$//' | sed 's/.tar.gz$//')
        dest_dir="$OUTPUT_DIR/$dest_name"
        echo "    Extracting to: $dest_name/"
    fi
    
    mkdir -p "$dest_dir"
    tar -xzf "$tgz_file" -C "$dest_dir"
    echo "    ✓ Extracted successfully"
done

# Process .zip files
for zip_file in $ZIP_FILES; do
    filename=$(basename "$zip_file")
    echo ""
    echo "--> Processing: $filename"
    
    # Determine destination based on filename
    if [[ "$filename" == *"can"* ]] || [[ "$filename" == *"CAN"* ]]; then
        dest_dir="$OUTPUT_DIR/can_bus"
        echo "    Extracting to: can_bus/"
    elif [[ "$filename" == *"map"* ]] || [[ "$filename" == *"MAP"* ]]; then
        dest_dir="$OUTPUT_DIR/maps"
        echo "    Extracting to: maps/"
    else
        # Generic extraction based on filename (remove extension)
        dest_name=$(echo "$filename" | sed 's/.zip$//')
        dest_dir="$OUTPUT_DIR/$dest_name"
        echo "    Extracting to: $dest_name/"
    fi
    
    mkdir -p "$dest_dir"
    unzip -q "$zip_file" -d "$dest_dir"
    echo "    ✓ Extracted successfully"
done

# --- Step 6: Optional - Remove downloaded archives to save space ---
echo ""
read -p "Do you want to remove the downloaded archive files to save space? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "--> Removing downloaded archives..."
    rm -rf "$OUTPUT_DIR/downloads"
    echo "Archives removed."
else
    echo "Downloaded archives kept in: $OUTPUT_DIR/downloads/"
fi

echo ""
echo "--- SUCCESS! ---"
echo "Your nuScenes dataset is ready in the '$OUTPUT_DIR' directory:"
echo ""
ls -d "$OUTPUT_DIR"/*/ 2>/dev/null | while read dir; do
    echo "  - $(basename "$dir")"
done
echo ""
echo "Total size:"
du -sh "$OUTPUT_DIR"