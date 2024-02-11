variable "resource_group_name" {
  description = "(Required) Specifies the name of the resource group"
  type        = string
}

variable "location" {
  description = "(Required) Specifies the location of the log analytics workspace"
  type        = string
}

variable "log_analytics_workspace_id" {
  description = "(Required) Specifies the id of the log analytics workspace"
  type        = string
}

variable "infrastructure_subnet_id" {
  description = "(Required) Specifies the id of the infrastructure subnet"
  type        = string
}

variable "container_app_environment_config" {
  description = "(Required) Specifies the name of the container app environment"
  type = object({
    name                           = string
    internal_load_balancer_enabled = bool
  })
}

variable "tags" {
  description = "Specifies the tags to assign to the resource group"
  type        = map(string)
}