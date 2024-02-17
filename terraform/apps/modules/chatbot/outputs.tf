output "fqdn" {
  description = "The fully qualified domain name of the chatbot app"
  value       = azurerm_container_app.chatbot.latest_revision_fqdn
}