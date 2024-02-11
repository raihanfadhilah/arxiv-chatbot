terraform {
  required_version = ">= 1.3"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.65"
    }
  }
}

resource "azurerm_virtual_network" "arxivchatbot-vnet" {
  name                = var.virtual_network_config.name
  address_space       = var.virtual_network_config.address_space
  location            = var.location
  resource_group_name = var.resource_group_name
  tags                = var.tags

  lifecycle {
    ignore_changes = [
        tags
    ]
  }
}

resource "azurerm_subnet" "arxivchatbot-subnet" {
  name                                           = var.subnet_config.name
  resource_group_name                            = var.resource_group_name
  virtual_network_name                           = azurerm_virtual_network.arxivchatbot-vnet.name
  address_prefixes                               = var.subnet_config.address_prefixes
  private_endpoint_network_policies_enabled = var.subnet_config.private_endpoint_network_policies_enabled
  private_link_service_network_policies_enabled  = var.subnet_config.private_link_service_network_policies_enabled
}

resource "azurerm_monitor_diagnostic_setting" "arxivchatbot-vnet-diag-settings" {
  name                       = var.vnet_diag_settings.name
  target_resource_id         = azurerm_virtual_network.arxivchatbot-vnet.id
  log_analytics_workspace_id = var.log_analytics_workspace_id
  storage_account_id = var.storage_account_id

  enabled_log {
    category = "VMProtectionAlerts"
  }

  metric {
    category = "AllMetrics"
  }
}