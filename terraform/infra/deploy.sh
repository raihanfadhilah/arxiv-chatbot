terraform init
terraform fmt -recursive
terraform validate
terraform plan -out tfplan \
-var "openai_api_key=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" \
-var "google_api_key=AIzaSyC4_47M3njDIco0nL-r0f8IqBhOtNeFy0k" \
-var "google_cse_id=805b71f9cef6d4b64"
terraform apply -auto-approve tfplan