#!/bin/bash

# Script to delete empty files with specified extensions
# Usage: ./delete_empty_files.sh [options] [directory]
# 
# Options:
#   -d, --depth DEPTH       Maximum recursion depth (default: unlimited)
#   -e, --extensions EXTS   Additional extensions (comma-separated, e.g., "txt,log")
#   -h, --help             Show this help message
#
# Protected files (never deleted even if empty):
#   __init__.py, __main__.py, py.typed, .gitkeep, .keep, requirements.txt, setup.py
#   conftest.py, readme.md, changelog.md, license.md, contributing.md, etc.
#
# Excluded directories (never searched):
#   .venv/, __pycache__/ (and all subdirectories)
#
# Examples:
#   ./delete_empty_files.sh                          # Current dir, unlimited depth, .py and .md files
#   ./delete_empty_files.sh -d 2                     # Current dir, max 2 levels deep
#   ./delete_empty_files.sh -e "txt,log" /path/dir   # Add .txt and .log extensions
#   ./delete_empty_files.sh -d 1 -e "json,yaml" .    # Depth 1, additional extensions

# Default values
TARGET_DIR="."
MAX_DEPTH=""
ADDITIONAL_EXTS=""
DEFAULT_EXTS=("py" "md" "txt" "log")

# Files that should never be deleted even if empty (case-insensitive)
PROTECTED_FILES=(
    "__init__.py"
    "__main__.py" 
    "py.typed"
    ".gitkeep"
    ".keep"
    "requirements.txt"
    "setup.py"
    "conftest.py"
    "readme.md"
    "README.md"
    "changelog.md"
    "CHANGELOG.md"
    "license.md"
    "LICENSE.md"
    "contributing.md"
    "CONTRIBUTING.md"
    "security.md"
    "SECURITY.md"
    "code_of_conduct.md"
)

# Function to show help
show_help() {
    echo "Script to delete empty files with specified extensions"
    echo
    echo "Usage: $0 [options] [directory]"
    echo
    echo "Options:"
    echo "  -d, --depth DEPTH       Maximum recursion depth (default: unlimited)"
    echo "  -e, --extensions EXTS   Additional extensions (comma-separated, e.g., 'txt,log')"
    echo "  -h, --help             Show this help message"
    echo
    echo "Protected files (never deleted even if empty):"
    echo "  __init__.py, __main__.py, py.typed, .gitkeep, .keep, requirements.txt"
    echo "  setup.py, conftest.py, readme.md, changelog.md, license.md, etc."
    echo
    echo "Excluded directories (never searched):"
    echo "  .venv/, __pycache__/ (and all subdirectories)"
    echo
    echo "Examples:"
    echo "  $0                          # Current dir, unlimited depth, .py and .md files"
    echo "  $0 -d 2                     # Current dir, max 2 levels deep"
    echo "  $0 -e 'txt,log' /path/dir   # Add .txt and .log extensions"
    echo "  $0 -d 1 -e 'json,yaml' .    # Depth 1, additional extensions"
    exit 0
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--depth)
            MAX_DEPTH="$2"
            shift 2
            ;;
        -e|--extensions)
            ADDITIONAL_EXTS="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            ;;
        -*)
            echo "Unknown option $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
        *)
            TARGET_DIR="$1"
            shift
            ;;
    esac
done

# Validate depth parameter
if [ -n "$MAX_DEPTH" ] && ! [[ "$MAX_DEPTH" =~ ^[0-9]+$ ]]; then
    echo "Error: Depth must be a positive integer."
    exit 1
fi

# Check if the target directory exists
if [ ! -d "$TARGET_DIR" ]; then
    echo "Error: Directory '$TARGET_DIR' does not exist."
    exit 1
fi

# Build the list of extensions to search for
EXTENSIONS=("${DEFAULT_EXTS[@]}")
if [ -n "$ADDITIONAL_EXTS" ]; then
    IFS=',' read -ra EXTRA_EXTS <<< "$ADDITIONAL_EXTS"
    for ext in "${EXTRA_EXTS[@]}"; do
        # Remove leading/trailing whitespace and dots
        ext=$(echo "$ext" | sed 's/^[[:space:]]*\.*//' | sed 's/[[:space:]]*$//')
        if [ -n "$ext" ]; then
            EXTENSIONS+=("$ext")
        fi
    done
fi

# Build find command depth option
DEPTH_OPTION=""
if [ -n "$MAX_DEPTH" ]; then
    DEPTH_OPTION="-maxdepth $MAX_DEPTH"
fi

echo "Searching for empty files in: $TARGET_DIR"
if [ -n "$MAX_DEPTH" ]; then
    echo "Maximum depth: $MAX_DEPTH levels"
else
    echo "Maximum depth: unlimited"
fi
echo "File extensions: ${EXTENSIONS[*]}"
echo "================================================="

# Function to check if a file should be protected from deletion
is_protected_file() {
    local filepath="$1"
    local filename=$(basename "$filepath")
    local filename_lower=$(echo "$filename" | tr '[:upper:]' '[:lower:]')
    
    for protected in "${PROTECTED_FILES[@]}"; do
        local protected_lower=$(echo "$protected" | tr '[:upper:]' '[:lower:]')
        if [ "$filename_lower" = "$protected_lower" ]; then
            return 0  # File is protected
        fi
    done
    return 1  # File is not protected
}

# Function to find and handle empty files for a given extension
process_extension() {
    local ext="$1"
    local ext_upper=$(echo "$ext" | tr '[:lower:]' '[:upper:]')
    
    echo "Looking for empty .$ext files..."
    
    # Build and execute find command (exclude .venv and __pycache__ directories)
    local find_cmd="find \"$TARGET_DIR\" $DEPTH_OPTION -name \"*.$ext\" -type f -empty -not -path \"*/.venv/*\" -not -path \"*/__pycache__/*\""
    local all_empty_files
    all_empty_files=$(eval "$find_cmd")
    
    # Filter out protected files
    local empty_files=""
    if [ -n "$all_empty_files" ]; then
        while IFS= read -r file; do
            if ! is_protected_file "$file"; then
                if [ -n "$empty_files" ]; then
                    empty_files="$empty_files"$'\n'"$file"
                else
                    empty_files="$file"
                fi
            fi
        done <<< "$all_empty_files"
    fi
    
    # Show protected files that were skipped
    local protected_count=0
    if [ -n "$all_empty_files" ]; then
        while IFS= read -r file; do
            if is_protected_file "$file"; then
                if [ $protected_count -eq 0 ]; then
                    echo "Skipping protected files:"
                fi
                echo "  $file (protected)"
                ((protected_count++))
            fi
        done <<< "$all_empty_files"
    fi
    
    if [ $protected_count -gt 0 ]; then
        echo
    fi
    
    if [ -n "$empty_files" ]; then
        echo "Found deletable empty .$ext files:"
        echo "$empty_files"
        echo
        read -p "Delete these empty .$ext files? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            # Delete each file individually to maintain the filtering
            while IFS= read -r file; do
                rm "$file" && echo "Deleted: $file"
            done <<< "$empty_files"
            echo "Empty .$ext files deleted."
        else
            echo "Skipped deleting .$ext files."
        fi
    else
        echo "No deletable empty .$ext files found."
    fi
    echo
}

# Process each extension
for ext in "${EXTENSIONS[@]}"; do
    process_extension "$ext"
done

echo
echo "Script completed."
