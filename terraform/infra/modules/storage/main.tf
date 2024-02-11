resource "azurerm_storage_account" "arxivchatbot-storage-account" {
  name                     = var.storage_account_config.name
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = var.storage_account_config.account_tier
  account_replication_type = var.storage_account_config.account_replication_type
}

# Create a blob container in the storage account
resource "azurerm_storage_container" "arxivchatbot-storage-container" {
  name                  = var.storage_container_config.name
  storage_account_name  = azurerm_storage_account.arxivchatbot-storage-account.name
  container_access_type = var.storage_container_config.container_access_type
  depends_on            = [azurerm_storage_account.arxivchatbot-storage-account]
}

# Create a storage management policy to define log retention
resource "azurerm_storage_management_policy" "arxivchatbot-storage-management-policy" {
  storage_account_id = azurerm_storage_account.arxivchatbot-storage-account.id

  rule {
    name    = var.storage_management_policy_config.rule.name
    enabled = var.storage_management_policy_config.rule.enabled
    filters {
      prefix_match = var.storage_management_policy_config.rule.filters.prefix_match
      blob_types   = var.storage_management_policy_config.rule.filters.blob_types
    }
    actions {
      base_blob {
        tier_to_cool_after_days_since_modification_greater_than    = var.storage_management_policy_config.rule.actions.base_blob.tier_to_cool_after_days_since_modification_greater_than
        tier_to_archive_after_days_since_modification_greater_than = var.storage_management_policy_config.rule.actions.base_blob.tier_to_archive_after_days_since_modification_greater_than
        delete_after_days_since_modification_greater_than          = var.storage_management_policy_config.rule.actions.base_blob.delete_after_days_since_modification_greater_than
      }
    }
  }
  depends_on = [azurerm_storage_account.arxivchatbot-storage-account]
}
