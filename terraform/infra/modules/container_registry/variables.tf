variable "resource_group_name" {
  description = "(Required) The name of the resource group in which to create the Container Registry. Changing this forces a new resource to be created."
  type        = string
}

variable "location" {
  description = "(Required) Specifies the supported Azure location where the resource exists. Changing this forces a new resource to be created."
  type        = string
}

variable "tags" {
  description = "(Optional) A mapping of tags to assign to the resource."
  type        = map(any)
  default     = {}
}

variable "container_registry_config" {
  description = "Specifies the container registry configuration"
  type        = object({
    name                     = string
    admin_enabled            = bool
    sku                      = string
    identity                 = object({
      type         = string
    })
  })
}

variable "acr_identity_config" {
  description = "Specifies the ACR identity configuration"
  type        = object({
    name = string
  })
}

variable "log_analytics_workspace_id" {
  description = "Specifies the log analytics workspace id"
  type        = string
}

variable "storage_account_id" {
    description = "Specifies the storage account id"
    type        = string
}

variable "acr_diag_settings_config" {
  description = "Specifies the ACR diagnostic settings configuration"
  type        = object({
    name      = string
  })
}
