variable "resource_group_name" {
  description = "The name of the resource group which the key vault is located"
  type        = string
}

variable "location" {
  description = "The location/region where the key vault is located"
  type        = string
}

variable "tags" {
  description = "A mapping of tags to assign to the resource"
  type        = map(string)
}

variable "key_vault_name" {
  description = "The name of the key vault"
  type        = string
}

variable "key_vault_sku" {
  description = "The SKU of the key vault"
  type        = string
  default     = "standard"
}

variable "openai_api_key" {
  description = "The OpenAI API key"
  type        = string
  default     = ""
  sensitive   = true
}

variable "google_api_key" {
  description = "The Google API key"
  type        = string
  default     = ""
  sensitive   = true
}

variable "google_cse_id" {
  description = "The Google CSE ID"
  type        = string
  default     = ""
  sensitive   = true
}




