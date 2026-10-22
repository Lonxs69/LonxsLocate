variable "region" {
  description = "Región de AWS"
  type        = string
  default     = "us-east-1"
}

variable "entorno" {
  description = "Nombre del entorno (dev, prod)"
  type        = string
  default     = "dev"
}

variable "github_repo" {
  description = "Repositorio autorizado a desplegar por OIDC (owner/repo)"
  type        = string
  default     = "Lonxs69/LonxsLocate"
}

variable "crear_proveedor_oidc" {
  description = "Crear el proveedor OIDC de GitHub (false si ya existe en la cuenta)"
  type        = bool
  default     = true
}

variable "lambda_memoria_mb" {
  description = "Memoria de la Lambda. 1769 MB equivale a 1 vCPU completa"
  type        = number
  default     = 1769
}

variable "concurrencia_maxima" {
  description = "Configuraciones evaluadas a la vez por Step Functions"
  type        = number
  default     = 100
}

variable "cobertura_objetivo" {
  description = "Cobertura mínima (%) para el ranking final en Athena"
  type        = number
  default     = 99.9
}
