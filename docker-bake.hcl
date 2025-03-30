// Common variables
variable "REGISTRY" { default = "kjanat" }
variable "IMAGE_NAME" { default = "pdf-extract-with-ocr" }

// Common build settings
group "default" {
  targets = [
    "asynchronous",
    "synchronous"
  ]
}

// Base target with common settings
target "base" {
  context = "."
  platforms = [
    "linux/amd64",
    // "linux/amd64/v2",
    // "linux/amd64/v3",
    "linux/arm64",
    // "linux/arm/v7",
    // "linux/arm/v6"
  ]
}

target "asynchronous" {
  inherits = ["base"]
  dockerfile = "Dockerfile"
  tags = ["${REGISTRY}/${IMAGE_NAME}:latest"]
  output = ["type=registry"]
}

target "synchronous" {
  inherits = ["base"]
  dockerfile = "Dockerfile-full"
  tags = ["${REGISTRY}/${IMAGE_NAME}:latest-full"]
  output = ["type=registry"]
}
