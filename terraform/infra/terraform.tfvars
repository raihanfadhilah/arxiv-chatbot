resource_group_name = "arxivchatbot-rg"
location            = "UAE North"
log_analytics_workspace_config = {
  name              = "arxivchatbot-log-analytics-workspace"
  sku               = "PerGB2018"
  retention_in_days = 30
  solution_plan_map = {}
}
virtual_network_config = {
  name          = "arxivchatbot-vnet"
  address_space = ["10.0.0.0/16"]
}
subnet_config = {
  name                                          = "arxivchatbot-subnet"
  address_prefixes                              = ["10.0.0.0/20"]
  private_endpoint_network_policies_enabled     = false
  private_link_service_network_policies_enabled = false
}
vnet_diag_settings = {
  name               = "arxivchatbot-vnet-diag"
  target_resource_id = "value"
}
storage_account_config = {
  name                     = "arxivchatbot"
  account_tier             = "Standard"
  account_replication_type = "LRS"
}
storage_container_config = {
  name                  = "arxivchatbot-storage-container"
  container_access_type = "blob"
}
storage_management_policy_config = {
  rule = {
    name    = "arxivchatbot-storage-management-policy"
    enabled = true
    filters = {
      blob_types   = ["blockBlob"]
      prefix_match = ["logs/"]
    }
    actions = {
      base_blob = {
        tier_to_cool_after_days_since_modification_greater_than    = 3
        tier_to_archive_after_days_since_modification_greater_than = 9
        delete_after_days_since_modification_greater_than          = 10
      }
    }
  }
}
workload_user_assigned_identity_config = {
  name = "arxivchatbot-workload-identity"
}
acr_pull_assignment_config = {
  role_definition_name             = "AcrPull"
  skip_service_principal_aad_check = true
}
container_registry_config = {
  name          = "arxivchatbotregistry"
  sku           = "Standard"
  admin_enabled = true
  identity = {
    type = "UserAssigned"
  }
}
acr_identity_config = {
  name = "arxivchatbot-acr-identity"
}
acr_diag_settings_config = {
  name = "arxivchatbot-acr-diag"
}
container_app_environment_config = {
  name                           = "arxivchatbot-app-environment"
  internal_load_balancer_enabled = false
}