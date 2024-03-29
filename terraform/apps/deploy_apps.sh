#!/bin/bash

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
terraform plan -replace="module.chatbot.azurerm_container_app.chatbot" -out tfplan 
terraform apply -auto-approve tfplan
FQDN="https://$(terraform show -json | jq -r '.values.root_module.child_modules[] |
 select(.address == "module.chatbot") |
  .resources[] |
   select(.address == "module.chatbot.azurerm_container_app.chatbot").values.latest_revision_fqdn' | 
   sed 's/--[a-zA-Z0-9]*//')"

LIGHT_GREEN='\033[92m'
RED='\033[41m'

# Check if the deployment was successful
if [ $? -eq 0 ]; then
    echo -e "\n\n${LIGHT_GREEN}Deployment Complete. FQDN: ${FQDN}"
else
    echo -e "\n\n${RED}Deployment Failed. Please reconfigure"
fi
