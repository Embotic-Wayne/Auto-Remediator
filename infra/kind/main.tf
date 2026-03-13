terraform {
  required_providers {
    kind = {
      source  = "tehcyx/kind"
      version = "~> 0.2.0"
    }
  }

  required_version = ">= 1.3.0"
}

provider "kind" {}

resource "kind_cluster" "aegis" {
  name           = "aegis-cluster"
  wait_for_ready = true

  kind_config {
    kind        = "Cluster"
    api_version = "kind.x-k8s.io/v1alpha4"

    node {
      role = "control-plane"
    }
  }
}

output "kubeconfig_context" {
  description = "Name of the kubeconfig context to use with kubectl"
  value       = "kind-${kind_cluster.aegis.name}"
}

