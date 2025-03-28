// Common variables
variable "REGISTRY" {
  default = "kjanat"
}

variable "IMAGE_NAME" {
  default = "pdf-extract-with-ocr"
}

// Common build settings
group "default" {
  targets = ["ocr-app", "worker"]
}

// Base target with common settings
target "base" {
  context = "."
  platforms = ["linux/amd64", "linux/arm64", "linux/arm/v7"]
}

target "ocr-app" {
  inherits = ["base"]
  dockerfile = "Dockerfile"
  tags = ["${REGISTRY}/${IMAGE_NAME}:latest"]
  output = ["type=registry"]
}

target "worker" {
  inherits = ["base"]
  dockerfile = "Dockerfile"
  tags = ["${REGISTRY}/${IMAGE_NAME}:worker"] 
  output = ["type=registry"]
}
