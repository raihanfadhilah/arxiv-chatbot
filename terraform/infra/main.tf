terraform {
  required_version = ">= 1.3"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.65"
    }
  }

  backend "azurerm" {
    resource_group_name  = "arxivchatbot-rg"
    storage_account_name = "arxivchatbot"
    container_name       = "tfstate"
    key                  = "arxivchatbot/infra.tfstate"
  }
}

provider "azurerm" {
  features {}
}

data "azurerm_client_config" "current" {
}

resource "azurerm_resource_group" "arxivchatbot-rg" {
  name     = var.resource_group_name
  location = var.location
  tags     = var.tags
}

module "log_analytics_workspace" {
  source                         = "./modules/log_analytics_workspace"
  resource_group_name            = var.resource_group_name
  location                       = var.location
  log_analytics_workspace_config = var.log_analytics_workspace_config
  tags                           = var.tags
  depends_on                     = [azurerm_resource_group.arxivchatbot-rg]
}

module "virtual_network" {
  source                     = "./modules/virtual_network"
  resource_group_name        = var.resource_group_name
  location                   = var.location
  virtual_network_config     = var.virtual_network_config
  storage_account_id         = module.storage.storage_account_id
  log_analytics_workspace_id = module.log_analytics_workspace.id
  subnet_config              = var.subnet_config
  vnet_diag_settings         = var.vnet_diag_settings
  tags                       = var.tags
  depends_on                 = [azurerm_resource_group.arxivchatbot-rg]
}

module "storage" {
  source                           = "./modules/storage"
  resource_group_name              = var.resource_group_name
  location                         = var.location
  storage_account_config           = var.storage_account_config
  storage_container_config         = var.storage_container_config
  storage_management_policy_config = var.storage_management_policy_config
  tags                             = var.tags
  depends_on                       = [azurerm_resource_group.arxivchatbot-rg]
}

module "managed_identity" {
  source                                 = "./modules/managed_identity"
  resource_group_name                    = var.resource_group_name
  location                               = var.location
  acr_identity_principal_id              = module.container_registry.acr_identity_principal_id
  acr_id                                 = module.container_registry.id
  workload_user_assigned_identity_config = var.workload_user_assigned_identity_config
  acr_pull_assignment_config             = var.acr_pull_assignment_config
  tags                                   = var.tags
  depends_on                             = [azurerm_resource_group.arxivchatbot-rg]
}

module "container_registry" {
  source                     = "./modules/container_registry"
  resource_group_name        = var.resource_group_name
  location                   = var.location
  container_registry_config  = var.container_registry_config
  acr_identity_config        = var.acr_identity_config
  acr_diag_settings_config   = var.acr_diag_settings_config
  log_analytics_workspace_id = module.log_analytics_workspace.id
  storage_account_id         = module.storage.storage_account_id
  tags                       = var.tags
  depends_on                 = [azurerm_resource_group.arxivchatbot-rg]
}

module "container_apps_environment" {
  source                           = "./modules/container_apps_environment"
  resource_group_name              = var.resource_group_name
  location                         = var.location
  container_app_environment_config = var.container_app_environment_config
  infrastructure_subnet_id         = module.virtual_network.subnet_id
  log_analytics_workspace_id       = module.log_analytics_workspace.id
  tags                             = var.tags
  depends_on                       = [azurerm_resource_group.arxivchatbot-rg]
}

module "key_vault" {
  source              = "./modules/key_vault"
  resource_group_name = var.resource_group_name
  location            = var.location
  key_vault_name      = var.key_vault_name
  tags                = var.tags
  openai_api_key      = var.openai_api_key
  google_api_key      = var.google_api_key
  google_cse_id       = var.google_cse_id
}
