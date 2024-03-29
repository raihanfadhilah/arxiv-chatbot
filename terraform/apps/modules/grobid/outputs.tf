output "fqdn" {
  description = "The fully qualified domain name of the grobid container app"
  value       = "http://${azurerm_container_app.grobid.latest_revision_fqdn}"
  sensitive   = true
}