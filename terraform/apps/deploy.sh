terraform init
terraform fmt -recursive
terraform validate
terraform plan -out tfplan 
terraform apply -auto-approve tfplan
echo "Deployed successfully!"