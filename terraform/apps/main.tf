terraform {
  required_version = ">= 1.3"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.65"
    }
  }
}

provider "azurerm" {
  features {}
}

data "azurerm_client_config" "current" {
}

module "chatbot" {
    source = "./modules/chatbot"
}

module "grobid" {
    source = "./modules/grobid"
    resource_group_name = var.resource_group_name
    container_app_environment_name = var.container_app_environment_name
    container_registry_name = var.container_registry_name
    acr_identity_name = var.acr_identity_name
    workload_identity_name = var.workload_identity_name
    container_app_config = var.grobid_config
    tags = var.tags
}