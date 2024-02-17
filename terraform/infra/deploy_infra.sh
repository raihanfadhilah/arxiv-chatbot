#!/bin/bash
while [[ $# -gt 0 ]]; do
    case "$1" in
        --openai-api-key)
            openai_api_key=$2
            shift 2
            ;;
        --google-api-key)
            google_api_key=$2
            shift 2
            ;;
        --google-cse-id)
            google_cse_id=$2
            shift 2
            ;;
        *)
            echo "Invalid argument: $1"
            exit 1
            ;;
    esac
done

if [[ -z $openai_api_key || -z $google_api_key || -z $google_cse_id ]]; then
    echo "Usage: $0 --openai_api_key <OpenAI API Key> --google_api_key <Google API Key> --google_cse_id <Google CSE ID>"
    exit 1
fi

# Assign arguments to variables
resourceGroupName="arxivchatbot-rg"
storageAccountName="arxivchatbot"
containerName="tfstate"
location="UAE North"

# Check if the resource group exists
az group show --name $resourceGroupName &>/dev/null
if [ $? -ne 0 ]; then
    echo "Creating resource group: $resourceGroupName"
    az group create --name $resourceGroupName --location $location
else
    echo "Resource group $resourceGroupName already exists."
fi

# Check if the storage account exists
accountCheck=$(az storage account check-name --name $storageAccountName --query 'nameAvailable' -o tsv)

if [ "$accountCheck" == "true" ]; then
    echo "Creating storage account: $storageAccountName"
    az storage account create --name $storageAccountName --resource-group $resourceGroupName --location $location --sku Standard_LRS --encryption-services blob
else
    echo "Storage account $storageAccountName already exists."
fi

# Retrieve the storage account key
accountKey=$(az storage account keys list --resource-group $resourceGroupName --account-name $storageAccountName --query '[0].value' -o tsv)

# Check if the blob container exists
containerCheck=$(az storage container exists --name $containerName --account-name $storageAccountName --account-key $accountKey --query 'exists' -o tsv)

if [ "$containerCheck" == "false" ]; then
    echo "Creating blob container: $containerName"
    az storage container create --name $containerName --account-name $storageAccountName --account-key $accountKey
else
    echo "Blob container $containerName already exists."
fi

terraform init
terraform fmt -recursive
terraform validate
terraform plan -out tfplan \
-var "openai_api_key=$openai_api_key" \
-var "google_api_key=$google_api_key" \
-var "google_cse_id=$google_cse_id"
terraform apply -auto-approve tfplan
echo "Deployment complete."