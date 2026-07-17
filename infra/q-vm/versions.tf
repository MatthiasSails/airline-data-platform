# Version pins — same reproducibility idea as pinned image tags in deployment/*.yml.
# The provider is the plugin that translates Terraform resources into AWS API calls.
terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

# Region is fixed (same as prod VM); credentials come from the environment
# (run with AWS_PROFILE=terraform -> credential_process -> macOS Keychain).
provider "aws" {
  region = "eu-central-1"
}
