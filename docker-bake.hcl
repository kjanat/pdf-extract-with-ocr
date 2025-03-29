// Common variables
variable "REGISTRY" {
  default = "kjanat"
}

variable "IMAGE_NAME" {
  default = "pdf-extract-with-ocr"
}

// Common build settings
group "default" {
  targets = ["api", "worker"]
}

// Base target with common settings
target "base" {
  context = "."
  platforms = ["linux/amd64", "linux/arm64", "linux/arm/v7"]
  cache-from = ["type=registry,ref=${REGISTRY}/${IMAGE_NAME}:buildcache"]
  cache-to = ["type=registry,ref=${REGISTRY}/${IMAGE_NAME}:buildcache,mode=max"]
}

target "api" {
  inherits = ["base"]
  dockerfile = "Dockerfile"
  tags = ["${REGISTRY}/${IMAGE_NAME}:api-latest"]
  output = ["type=registry"]
}

target "worker" {
  inherits = ["base"]
  dockerfile = "Dockerfile"
  tags = ["${REGISTRY}/${IMAGE_NAME}:worker-latest"]
  output = ["type=registry"]
}
