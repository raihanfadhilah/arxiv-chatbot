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
    type        = object({
        name                = string
        sku                 = string
        retention_in_days   = number
        solution_plan_map   = map(any)
    })
}

variable "tags"{
  description = "(Optional) A mapping of tags to assign to the resource group"
  type        = map(string)
  default     = { 
      "Environment" = "Production",
      "BuiltBy"     = "Terraform"
  }
}