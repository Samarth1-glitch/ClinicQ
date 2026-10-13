variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "ap-south-1"
}

variable "project_name" {
  description = "Prefix used for resource names and tags"
  type        = string
  default     = "clinicq"
}

variable "cluster_name" {
  description = "EKS cluster name"
  type        = string
  default     = "clinicq-eks"
}

variable "kubernetes_version" {
  description = "EKS Kubernetes version (use a currently supported one to avoid extended-support fees)"
  type        = string
  default     = "1.34"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "node_instance_types" {
  description = "Instance types for the managed node group"
  type        = list(string)
  default     = ["t3.medium", "t3a.medium"]
}

variable "node_capacity_type" {
  description = "SPOT is much cheaper for a demo; use ON_DEMAND if you need stability"
  type        = string
  default     = "SPOT"
}

variable "node_desired_size" {
  description = "Number of worker nodes"
  type        = number
  default     = 2
}
