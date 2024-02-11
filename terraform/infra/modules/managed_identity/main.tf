resource "azurerm_user_assigned_identity" "arxivchatbot-workload-user-assigned-identity" {
  name                = var.workload_user_assigned_identity_config.name
  resource_group_name = var.resource_group_name
  location            = var.location
  tags                = var.tags

  lifecycle {
    ignore_changes = [
      tags
    ]
  }
}

resource "azurerm_role_assignment" "arxivchatbot-acr-pull-assignment" {
  scope                = var.acr_id
  role_definition_name = var.acr_pull_assignment_config.role_definition_name
  principal_id         = var.acr_identity_principal_id
  skip_service_principal_aad_check = var.acr_pull_assignment_config.skip_service_principal_aad_check
}