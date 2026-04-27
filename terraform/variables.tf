variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-south-1"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "threatvision"
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

variable "internal_jwt_secret" {
  description = "Internal JWT Secret"
  type        = string
  sensitive   = true
}

variable "bff_service_key" {
  description = "BFF Service Key"
  type        = string
  sensitive   = true
}

variable "api_key_pepper" {
  description = "API Key Pepper for hashing"
  type        = string
  sensitive   = true
}

variable "superadmin_email" {
  description = "Superadmin Email for the initial admin account"
  type        = string
  default     = "admin@threatvision.dev"
}
