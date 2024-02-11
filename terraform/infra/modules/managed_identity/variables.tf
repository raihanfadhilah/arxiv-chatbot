variable "resource_group_name" {
  description = "(Required) Specifies the resource group name"
  type        = string
}

variable "location" {
  description = "(Required) Specifies the location of the log analytics workspace"
  type        = string
}

variable "workload_user_assigned_identity_config" {
  description = "(Required) Specifies the workload user-assigned identity configuration"
  type = object({
    name = string
  })
}

variable "acr_identity_principal_id" {
  description = "(Required) Specifies the principal id of the ACR identity"
  type        = string
}

variable "acr_id" {
  description = "(Required) Specifies the id of the container registry"
  type        = string
}

variable "acr_pull_assignment_config" {
  description = "(Required) Specifies the ACR pull role assignment configuration"
  type = object({
    role_definition_name             = string
    skip_service_principal_aad_check = bool
  })
}

variable "tags" {
  description = "Specifies the tags to assign to the resource group"
  type        = map(string)
  default = {
    "Environment" = "Production"
    "BuiltBy"     = "Terraform"
  }
}