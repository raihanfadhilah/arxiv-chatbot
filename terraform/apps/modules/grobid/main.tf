data "azurerm_container_app_environment" "arxivchatbot-container-app-environment" {
  name                = var.container_app_environment_name
  resource_group_name = var.resource_group_name
}

data "azurerm_container_registry" "arxivchatbotregistry" {
  name                = var.container_registry_name
  resource_group_name = var.resource_group_name
}

data "azurerm_user_assigned_identity" "acr_identity" {
  name                = var.acr_identity_name
  resource_group_name = var.resource_group_name
}

data "azurerm_user_assigned_identity" "workload_identity" {
  name                = var.workload_identity_name
  resource_group_name = var.resource_group_name
}

resource "azurerm_container_app" "grobid" {
  name                         = var.container_app_config.name
  resource_group_name          = var.resource_group_name
  container_app_environment_id = data.azurerm_container_app_environment.arxivchatbot-container-app-environment.id
  revision_mode                = var.container_app_config.revision_mode
  tags                         = var.tags

  template {
    container {
      name   = var.container_app_config.template.container.name
      image  = "${data.azurerm_container_registry.arxivchatbotregistry.login_server}/${var.container_app_config.template.container.image}"
      cpu    = var.container_app_config.template.container.cpu
      memory = var.container_app_config.template.container.memory

      liveness_probe {
        failure_count_threshold = var.container_app_config.template.container.liveness_probe.failure_count_threshold
        host                    = var.container_app_config.template.container.liveness_probe.host
        initial_delay           = var.container_app_config.template.container.liveness_probe.initial_delay
        interval_seconds        = var.container_app_config.template.container.liveness_probe.interval_seconds
        path                    = var.container_app_config.template.container.liveness_probe.path
        port                    = var.container_app_config.template.container.liveness_probe.port
        timeout                 = var.container_app_config.template.container.liveness_probe.timeout
        transport               = var.container_app_config.template.container.liveness_probe.transport
      }

      readiness_probe {
        failure_count_threshold = var.container_app_config.template.container.readiness_probe.failure_count_threshold
        host                    = var.container_app_config.template.container.readiness_probe.host
        interval_seconds        = var.container_app_config.template.container.readiness_probe.interval_seconds
        path                    = var.container_app_config.template.container.readiness_probe.path
        port                    = var.container_app_config.template.container.readiness_probe.port
        success_count_threshold = var.container_app_config.template.container.readiness_probe.success_count_threshold
        transport               = var.container_app_config.template.container.readiness_probe.transport
      }

      startup_probe {
        failure_count_threshold = var.container_app_config.template.container.startup_probe.failure_count_threshold
        host                    = var.container_app_config.template.container.startup_probe.host
        interval_seconds        = var.container_app_config.template.container.startup_probe.interval_seconds
        path                    = var.container_app_config.template.container.startup_probe.path
        port                    = var.container_app_config.template.container.startup_probe.port
        transport               = var.container_app_config.template.container.startup_probe.transport
      }
    }

    max_replicas = var.container_app_config.template.max_replicas
    min_replicas = var.container_app_config.template.min_replicas

  }

  ingress {
    allow_insecure_connections = var.container_app_config.ingress.allow_insecure_connections
    external_enabled           = var.container_app_config.ingress.external_enabled
    target_port                = var.container_app_config.ingress.target_port
    transport                  = var.container_app_config.ingress.transport
    traffic_weight {
      label           = var.container_app_config.ingress.traffic_weight.label
      latest_revision = var.container_app_config.ingress.traffic_weight.latest_revision
      percentage      = var.container_app_config.ingress.traffic_weight.percentage
    }
  }

  identity {
    type         = var.container_app_config.identity.type
    identity_ids = [data.azurerm_user_assigned_identity.acr_identity.id, data.azurerm_user_assigned_identity.workload_identity.id]
  }

  registry {
    server   = data.azurerm_container_registry.arxivchatbotregistry.login_server
    identity = data.azurerm_user_assigned_identity.acr_identity.id
  }
}