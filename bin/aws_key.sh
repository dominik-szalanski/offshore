#!/bin/bash
#
# AWS Key Setup Script
# Sets AWS credentials as environment variables for subsequent AWS CLI commands
#
# Usage:
#   source bin/aws_key.sh <access_key_id> <secret_access_key>
#   OR
#   source bin/aws_key.sh (will prompt for credentials)
#
# Note: This script must be sourced (not executed) to set environment variables
#       in the current shell session.

# Function to display usage
_aws_key_usage() {
    echo "Usage: source bin/aws_key.sh [<access_key_id> <secret_access_key>]"
    echo ""
    echo "Sets AWS credentials as environment variables."
    echo ""
    echo "Arguments:"
    echo "  access_key_id      AWS Access Key ID"
    echo "  secret_access_key  AWS Secret Access Key"
    echo ""
    echo "If no arguments provided, will prompt for credentials."
    echo ""
    echo "Note: This script must be sourced, not executed directly."
    echo "      Use: source bin/aws_key.sh or . bin/aws_key.sh"
}

# Main function to avoid polluting the shell with variables
_aws_key_main() {
    local key_id=""
    local secret_key=""
    
    # Get credentials from arguments or prompt
    if [[ $# -eq 2 ]]; then
        key_id="$1"
        secret_key="$2"
    elif [[ $# -eq 0 ]]; then
        read -p "Enter AWS Access Key ID: " key_id
        read -s -p "Enter AWS Secret Access Key: " secret_key
        echo ""
    else
        _aws_key_usage
        return 1
    fi

    # Validate inputs
    if [[ -z "$key_id" ]]; then
        echo "Error: AWS Access Key ID cannot be empty"
        return 1
    fi

    if [[ -z "$secret_key" ]]; then
        echo "Error: AWS Secret Access Key cannot be empty"
        return 1
    fi

    # Export the environment variables
    export AWS_ACCESS_KEY_ID="$key_id"
    export AWS_SECRET_ACCESS_KEY="$secret_key"

    echo "AWS credentials have been set successfully."
    echo "AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID:0:4}...${AWS_ACCESS_KEY_ID: -4}"
    echo ""
    echo "You can now use AWS CLI commands in this shell session."
    return 0
}

# Check if script is being sourced
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "Error: This script must be sourced, not executed directly."
    echo "Use: source bin/aws_key.sh [<access_key_id> <secret_access_key>]"
    exit 1
fi

# Run main function with all arguments
_aws_key_main "$@"