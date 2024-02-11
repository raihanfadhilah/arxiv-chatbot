resource "azurerm_log_analytics_workspace" "arxivchatbot-log-analytics" {
  name                = var.log_analytics_workspace_config.name
  location            = var.location
  resource_group_name = var.resource_group_name
  sku                 = var.log_analytics_workspace_config.sku
  retention_in_days   = var.log_analytics_workspace_config.retention_in_days
  tags                = var.tags

  lifecycle {
    ignore_changes = [
      tags
    ]
  }
}

resource "azurerm_log_analytics_solution" "arxivchatbot-log-analytics-solution" {
  for_each = var.log_analytics_workspace_config.solution_plan_map

  solution_name         = each.key
  location              = var.location
  resource_group_name   = var.resource_group_name
  workspace_resource_id = azurerm_log_analytics_workspace.arxivchatbot-log-analytics.id
  workspace_name        = azurerm_log_analytics_workspace.arxivchatbot-log-analytics.name

  plan {
    product   = each.value.product
    publisher = each.value.publisher
  }

  lifecycle {
    ignore_changes = [
      tags
    ]
  }
}