variable "resource_group_name" {
  description = "The name of the resource group in which the container app and container registry are located"
  type = string
}

variable "container_app_environment_name" {
  description = "The name of the container app environment"
  type = string
}

variable "container_registry_name" {
  description = "The name of the container registry"
  type = string
}

variable "acr_identity_name" {
    description = "The name of the container registry identity"
    type = string
}

variable "workload_identity_name" {
    description = "The name of the workload identity"
    type = string
}

variable "key_vault_name" {
    description = "The name of the key vault"
    type = string
}

variable "grobid_config" {
    description = "The configuration for the grobid app"
    type = object({
      name = string
      revision_mode = string
      template = object({
        container = object({
          name = string
          image = string
          cpu = number
          memory = string

          env = optional(list(object({
            name = string
            secret_name = optional(string)
            value = optional(string)
          })))

          liveness_probe = optional(object({
            failure_count_threshold = optional(number)
            header = optional(object({
              name  = string
              value = string
              }))

            host             = optional(string)
            initial_delay    = optional(number, 1)
            interval_seconds = optional(number, 10)
            path             = optional(string)
            port             = number
            timeout          = optional(number, 1)
            transport        = string
            }))

          readiness_probe = optional(object({
            failure_count_threshold = optional(number)
            header = optional(object({
              name  = string
              value = string
              }))
            host                    = optional(string)
            interval_seconds        = optional(number, 10)
            path                    = optional(string)
            port                    = number
            success_count_threshold = optional(number, 3)
            timeout                 = optional(number)
            transport               = string
            }))

          startup_probe = optional(object({
            failure_count_threshold = optional(number)
            header = optional(object({
              name  = string
              value = string
              }))
            host             = optional(string)
            interval_seconds = optional(number, 10)
            path             = optional(string)
            port             = number
            timeout          = optional(number)
            transport        = string
          }))   

          volume_mounts = optional(object({
            name = string
            path = string
          }))

        })
        volume = optional(set(object({
          name         = string
          storage_name = optional(string)
          storage_type = optional(string)
        })))

        max_replicas = optional(number)
        min_replicas = optional(number)

      })

      ingress = optional(object({
        allow_insecure_connections = optional(bool, false)
        external_enabled           = optional(bool, false)
        target_port                = number
        transport                  = optional(string)
        traffic_weight = object({
          label           = optional(string)
          latest_revision = optional(string)
          revision_suffix = optional(string)
          percentage      = number
        })
      }))

      identity = optional(object({
        type         = string
        identity_ids = optional(list(string))
      }))

      dapr = optional(object({
        app_id       = string
        app_port     = number
        app_protocol = optional(string)
      }))

      registry = optional(list(object({
        server               = string
        username             = optional(string)
        password_secret_name = optional(string)
        identity             = optional(string)
      })))
  })
  nullable    = false
}

variable "chatbot_config" {
    description = "The configuration for the chatbot app"
    type = object({
      name = string
      revision_mode = string
      template = object({
        container = object({
          name = string
          image = string
          cpu = number
          memory = string

          env = optional(list(object({
            name = string
            secret_name = optional(string)
            value = optional(string)
          })))

          liveness_probe = optional(object({
            failure_count_threshold = optional(number)
            header = optional(object({
              name  = string
              value = string
              }))

            host             = optional(string)
            initial_delay    = optional(number, 1)
            interval_seconds = optional(number, 10)
            path             = optional(string)
            port             = number
            timeout          = optional(number, 1)
            transport        = string
            }))

          readiness_probe = optional(object({
            failure_count_threshold = optional(number)
            header = optional(object({
              name  = string
              value = string
              }))
            host                    = optional(string)
            interval_seconds        = optional(number, 10)
            path                    = optional(string)
            port                    = number
            success_count_threshold = optional(number, 3)
            timeout                 = optional(number)
            transport               = string
            }))

          startup_probe = optional(object({
            failure_count_threshold = optional(number)
            header = optional(object({
              name  = string
              value = string
              }))
            host             = optional(string)
            interval_seconds = optional(number, 10)
            path             = optional(string)
            port             = number
            timeout          = optional(number)
            transport        = string
          }))   

          volume_mounts = optional(object({
            name = string
            path = string
          }))

        })
        volume = optional(set(object({
          name         = string
          storage_name = optional(string)
          storage_type = optional(string)
        })))

        max_replicas = optional(number)
        min_replicas = optional(number)

      })

      ingress = optional(object({
        allow_insecure_connections = optional(bool, false)
        external_enabled           = optional(bool, false)
        target_port                = number
        transport                  = optional(string)
        traffic_weight = object({
          label           = optional(string)
          latest_revision = optional(string)
          revision_suffix = optional(string)
          percentage      = number
        })
      }))

      identity = optional(object({
        type         = string
        identity_ids = optional(list(string))
      }))

      dapr = optional(object({
        app_id       = string
        app_port     = number
        app_protocol = optional(string)
      }))

      registry = optional(list(object({
        server               = string
        username             = optional(string)
        password_secret_name = optional(string)
        identity             = optional(string)
      })))
  })
  nullable    = false
}

variable "tags" {
    description = "A mapping of tags to assign to the resource"
    type = map(string)
    default = {
      Environment = "Production"
      BuiltBy = "Terraform"
    }
}