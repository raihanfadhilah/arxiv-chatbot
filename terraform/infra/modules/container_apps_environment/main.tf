resource "azurerm_container_app_environment" "arxivchatbot-container-app-environment" {
  name                           = var.container_app_environment_config.name
  location                       = var.location
  resource_group_name            = var.resource_group_name
  log_analytics_workspace_id     = var.log_analytics_workspace_id
  infrastructure_subnet_id       = var.infrastructure_subnet_id
  internal_load_balancer_enabled = var.container_app_environment_config.internal_load_balancer_enabled
  tags                           = var.tags
  
  lifecycle {
    ignore_changes = [
      tags
    ]
  }
}