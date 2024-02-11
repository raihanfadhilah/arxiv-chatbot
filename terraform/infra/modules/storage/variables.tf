variable "resource_group_name" {
    description = "Specifies the name of the resource group"
    type        = string
}

variable "location" {
    description = "Specifies the location of the resource group"
    type        = string
}

variable "storage_account_config" {
    description = "Specifies the storage account configuration"
    type        = object({
        name                     = string
        account_tier             = string
        account_replication_type = string
    })
}

variable "storage_container_config" {
    description = "Specifies the storage container configuration"
    type        = object({
        name                 = string
        container_access_type = string
    })
}

variable "storage_management_policy_config" {
    description = "Specifies the storage management policy configuration"
    type        = object({
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

variable "tags"{
    description = "Specifies the tags to assign to the resource group"
    type        = map(string)
    default     = { 
        "Environment" = "Production",
        "BuiltBy"     = "Terraform"
    }
}