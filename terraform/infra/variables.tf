variable "tags" {
  description = "(Optional) A mapping of tags to assign to the resource group"
  type        = map(string)
  default = {
    "Environment" = "Production",
    "BuiltBy"     = "Terraform"
  }
}

variable "resource_group_name" {
  description = "(Required) Specifies the name of the resource group"
  type        = string
}

variable "location" {
  description = "(Required) Specifies the location of the resource group"
  type        = string
}

variable "log_analytics_workspace_config" {
  description = "(Required) The log analytics workspace configuration"
  type = object({
    name              = string
    sku               = string
    retention_in_days = number
    solution_plan_map = map(any)
  })
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

variable "storage_account_config" {
  description = "Specifies the storage account configuration"
  type = object({
    name                     = string
    account_tier             = string
    account_replication_type = string
  })
}

variable "storage_container_config" {
  description = "Specifies the storage container configuration"
  type = object({
    name                  = string
    container_access_type = string
  })
}

variable "storage_management_policy_config" {
  description = "Specifies the storage management policy configuration"
  type = object({
    rule = object({
      name    = string
      enabled = bool
      filters = object({
        prefix_match = list(string)
        blob_types   = list(string)
      })
      actions = object({
        base_blob = object({
          tier_to_cool_after_days_since_modification_greater_than    = number
          tier_to_archive_after_days_since_modification_greater_than = number
          delete_after_days_since_modification_greater_than          = number
        })
      })
    })
  })
}

variable "workload_user_assigned_identity_config" {
  description = "(Required) Specifies the workload user-assigned identity configuration"
  type = object({
    name = string
  })
}

variable "acr_pull_assignment_config" {
  description = "(Required) Specifies the ACR pull role assignment configuration"
  type = object({
    role_definition_name             = string
    skip_service_principal_aad_check = bool
  })
}

variable "container_registry_config" {
  description = "Specifies the container registry configuration"
  type = object({
    name          = string
    admin_enabled = bool
    sku           = string
    identity = object({
      type = string
    })
  })
}

variable "acr_identity_config" {
  description = "Specifies the ACR identity configuration"
  type = object({
    name = string
  })
}

variable "acr_diag_settings_config" {
  description = "Specifies the ACR diagnostic settings configuration"
  type = object({
    name = string
  })
}

variable "container_app_environment_config" {
  description = "(Required) Specifies the name of the container app environment"
  type = object({
    name                           = string
    internal_load_balancer_enabled = bool
  })
}