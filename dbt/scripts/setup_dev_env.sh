#!/bin/bash

# Script to setup dbt for local development

echo "Checking for BIGQUERY_USER environment variable..."
echo

# Function to generate BIGQUERY_USER from name
generate_bigquery_user() {
    read -p "Enter your first name: " first_name
    read -p "Enter your last name: " last_name
    echo "${first_name:0:3}${last_name:0:3}" | tr '[:upper:]' '[:lower:]'
}

# Check if BIGQUERY_USER is set
if [ -z "$BIGQUERY_USER" ]; then
    echo "BIGQUERY_USER environment variable is not set."
    echo

    # Generate a default BIGQUERY_USER
    default_bigquery_user=$(generate_bigquery_user)
    echo "Using the default BIGQUERY_USER: $default_bigquery_user"
    echo

    echo "To set this variable for future sessions:"
    echo

    echo "1. Temporarily for a single session in the terminal run:"
    echo "   export BIGQUERY_USER=$default_bigquery_user"
    echo

    echo "2. Temporarily for a single command, preface the dbt command like so:"
    echo "   BIGQUERY_USER=$default_bigquery_user dbt run"
    echo

    echo "3. Permanently, by adding it to your shell's configuration file (.bashrc, .zshrc, etc.):"
    echo "   echo 'export BIGQUERY_USER=$default_bigquery_user' >> ~/.zshrc"
    echo "   and then source the file: source ~/.zshrc"
    echo
else
    echo "BIGQUERY_USER is set to $BIGQUERY_USER."
    echo
fi

# Downloads prod manifest.json file for --defer --state dbt commands
read -p "Do you want to download dbt prod artifacts? (Y/n): " download_confirm
echo
download_confirm=$(echo "$download_confirm" | tr '[:upper:]' '[:lower:]')

# Assume 'yes' if the user just presses enter
if [ -z "$download_confirm" ]; then
    download_confirm="y"
fi

if [[ "$download_confirm" == "y" ]]; then
    # Get dir of where the setup_dev_env.sh script resides
    script_dir=$(dirname "$0")
    # Define the directory and file path
    artifacts_dir="$script_dir/../prod-run-artifacts"
    # Ensure the directory exists
    if [ ! -d "$artifacts_dir" ]; then
        mkdir -p "$artifacts_dir"
        echo "Created directory $artifacts_dir"
    fi

    rsync -az --delete github@pypacktrends-prod:/srv/www/dbtdocs/ $artifacts_dir

    if [ $? -eq 0 ]; then
        echo "Download successful: $manifest_file"
        echo
    else
        echo "Failed to download manifest.json"
        echo
    fi
else
    echo "Download skipped."
    echo
fi

# Ask if user wants to run dbt deps
read -p "Do you want to run dbt deps? (Y/n): " deps_confirm
echo
deps_confirm=$(echo "$deps_confirm" | tr '[:upper:]' '[:lower:]')

# Assume 'yes' if the user just presses enter
if [ -z "$deps_confirm" ]; then
    deps_confirm="y"
fi
if [[ "$deps_confirm" == "y" ]]; then
    echo "Running dbt deps..."
    dbt deps
    if [ $? -eq 0 ]; then
        echo "dbt deps executed successfully."
        echo
    else
        echo "Failed to run dbt deps."
        echo
    fi
else
    echo "dbt deps skipped."
    echo
fi
