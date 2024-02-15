resource_group_name = "arxivchatbot-rg"
container_app_environment_name = "arxivchatbot-app-environment"
container_registry_name = "arxivchatbotregistry"
acr_identity_name = "arxivchatbot-acr-identity"
workload_identity_name = "arxivchatbot-workload-identity"
key_vault_name = "arxivchatbot-key-vault"
grobid_config = {
    name = "grobid"
    revision_mode = "Single"
    template = {
        container = {
            name = "grobid"
            image = "grobid:0.8.0"
            cpu = 2
            memory = "4Gi"
            liveness_probe            = {
              failure_count_threshold = 3
              initial_delay           = 30
              interval_seconds        = 60
              path                    = "/"
              port                    = 8070
              timeout                 = 30
              transport               = "HTTP"
            }
            readiness_probe = {
              failure_count_threshold = 3
              interval_seconds        = 60
              path                    = "/"
              port                    = 8070
              success_count_threshold = 3
              timeout                 = 30
              transport               = "HTTP"
            }
            startup_probe = {
              failure_count_threshold = 3
              interval_seconds        = 60
              path                    = "/"
              port                    = 8070
              timeout                 = 30
              transport               = "HTTP"
          }
        }
        min_replicas = 1
        max_replicas = 3

    }

    ingress = {
        allow_insecure_connections = true
        external_enabled = true
        target_port = 8070
        transport = "http"
        traffic_weight = {
            label = "default"
            latest_revision = true
            percentage = 100
        }
    }

    identity = {
        type = "UserAssigned"
    }
}

chatbot_config = {
    name = "chatbot"
    revision_mode = "Single"
    template = {
        container = {
            name = "chatbot"
            image = "chatbot:latest"
            cpu = 1
            memory = "2Gi"

            env = [
              {
                name = "INIT_LLM"
                value = "gpt-3.5-turbo-1106"
              },
              {
                name = "INIT_EMBEDDING"
                value = "text-embedding-ada-002"
              }
            ]

            liveness_probe            = {
              failure_count_threshold = 3
              initial_delay           = 30
              interval_seconds        = 60
              path                    = "/"
              port                    = 8000
              timeout                 = 30
              transport               = "HTTP"
            }

            readiness_probe = {
              failure_count_threshold = 3
              interval_seconds        = 60
              path                    = "/"
              port                    = 8000
              success_count_threshold = 3
              timeout                 = 30
              transport               = "HTTP"
            }
            startup_probe = {
              failure_count_threshold = 3
              interval_seconds        = 60
              path                    = "/"
              port                    = 8000
              timeout                 = 30
              transport               = "HTTP"
          }
        }
        min_replicas = 1
        max_replicas = 3

    }

    ingress = {
        allow_insecure_connections = false
        external_enabled = true
        target_port = 8000
        transport = "http"
        traffic_weight = {
            label = "default"
            latest_revision = true
            percentage = 100
        }
    }

    identity = {
        type = "UserAssigned"
    }
}
