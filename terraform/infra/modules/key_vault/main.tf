data "azurerm_client_config" "current" {
}

resource "azurerm_key_vault" "arxivchatbot-key-vault" {
  name                = var.key_vault_name
  location            = var.location
  resource_group_name = var.resource_group_name
  sku_name            = var.key_vault_sku
  tenant_id           = data.azurerm_client_config.current.tenant_id
  tags                = var.tags

  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = data.azurerm_client_config.current.object_id

    secret_permissions = [
      "Get",
      "Set",
      "Purge",
      "Recover",
      "Delete",
      "List"
    ]
  }
}

resource "azurerm_key_vault_secret" "kv-openai-api-key" {
  key_vault_id = azurerm_key_vault.arxivchatbot-key-vault.id
  name         = "openai-api-key"
  value        = var.openai_api_key
}

resource "azurerm_key_vault_secret" "kv-google-api-key" {
  key_vault_id = azurerm_key_vault.arxivchatbot-key-vault.id
  name         = "google-api-key"
  value        = var.google_api_key
}

resource "azurerm_key_vault_secret" "kv-google-cse-id" {
  key_vault_id = azurerm_key_vault.arxivchatbot-key-vault.id
  name         = "google-cse-id"
  value        = var.google_cse_id
}
