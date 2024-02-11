resource "azurerm_container_registry" "arxivchatbot-container-registry" {
  name                     = var.container_registry_config.name
  resource_group_name      = var.resource_group_name
  location                 = var.location
  sku                      = var.container_registry_config.sku
  admin_enabled            = var.container_registry_config.admin_enabled
  tags                     = var.tags

  identity {
    type = var.container_registry_config.identity.type
    identity_ids = [
      azurerm_user_assigned_identity.arxivchatbot-acr-identity.id
    ]
  }

  lifecycle {
      ignore_changes = [
          tags
      ]
  }
}

resource "azurerm_user_assigned_identity" "arxivchatbot-acr-identity" {
  resource_group_name = var.resource_group_name
  location            = var.location
  tags                = var.tags

  name = var.acr_identity_config.name

  lifecycle {
    ignore_changes = [
      tags
    ]
  }
}

resource "azurerm_monitor_diagnostic_setting" "arxivchatbot-acr-diag-settings" {
  name                       = var.acr_diag_settings_config.name
  target_resource_id         = azurerm_container_registry.arxivchatbot-container-registry.id
  log_analytics_workspace_id = var.log_analytics_workspace_id
  storage_account_id        = var.storage_account_id

  enabled_log {
    category = "ContainerRegistryRepositoryEvents"
  }

  enabled_log {
    category = "ContainerRegistryLoginEvents"
  }

  metric {
    category = "AllMetrics"
  }
}