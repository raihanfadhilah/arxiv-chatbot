variable "resource_group_name" {
  description = "Specifies the name of the resource group"
  type        = string
}

variable "location" {
  description = "Specifies the location of the resource group"
  type        = string
}

variable "storage_account_id" {
  description = "Specifies the id of the storage account"
  type        = string
}

variable "log_analytics_workspace_id" {
  description = "Specifies the id of the log analytics workspace"
  type        = string
}

variable "virtual_network_config" {
  description = "Specifies the virtual network configuration"
  type = object({
    name          = string
    address_space = list(string)
  })
}

variable "subnet_config" {
  description = "Specifies the subnet configuration"
  type = object({
    name                                          = string
    address_prefixes                              = list(string)
    private_endpoint_network_policies_enabled     = bool
    private_link_service_network_policies_enabled = bool
  })
}

variable "vnet_diag_settings" {
  description = "Specifies the diagnostic settings for the virtual network"
  type = object({
    name = string
  })
}

variable "tags" {
  description = "Specifies the tags to assign to the resource group"
  type        = map(string)
  default = {
    "Environment" = "Production",
    "BuiltBy"     = "Terraform"
  }
}