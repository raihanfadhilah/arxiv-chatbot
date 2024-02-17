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

pip freeze > requirements.txt

## dir: .
echo -e "######################### Login to Azure Container Registry #########################"
docker login arxivchatbotregistry.azurecr.io

echo -e "\n\n######################### Push lfoppiano/grobid:0.8.0 to ACR #########################"
docker-compose pull
docker tag lfoppiano/grobid:0.8.0 arxivchatbotregistry.azurecr.io/grobid:0.8.0
docker push arxivchatbotregistry.azurecr.io/grobid:0.8.0

echo -e "\n\n######################### Push app:latest #########################"
docker build -t arxivchatbotregistry.azurecr.io/app:latest .
docker push arxivchatbotregistry.azurecr.io/app:latest
cd terraform/infra

# dir: terraform/infra
echo -e "\n\n######################### Deploying Infrastructure #########################"
chmod +x deploy_infra.sh
./deploy_infra.sh --openai-api-key $openai_api_key --google-api-key $google_api_key --google-cse-id $google_cse_id
cd ../apps

# dir: terraform/apps
echo -e "\n\n######################### Deploying Apps #########################"
chmod +x deploy_apps.sh
./deploy_apps.sh
