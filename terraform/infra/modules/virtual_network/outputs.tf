output "name" {
  description = "Specifies the name of the virtual network"
  value       = azurerm_virtual_network.arxivchatbot-vnet.name
}

output "vnet_id" {
  description = "Specifies the resource id of the virtual network"
  value       = azurerm_virtual_network.arxivchatbot-vnet.id
}

output "subnet_id" {
  description = "Contains a list of the the resource id of the subnets"
  value       = azurerm_subnet.arxivchatbot-subnet.id
}