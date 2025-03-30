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
    "linux/arm64",
    "linux/arm/v7"
  ]
  // cache-from = ["type=registry,ref=${REGISTRY}/${IMAGE_NAME}:buildcache"]
  // cache-to = ["type=registry,ref=${REGISTRY}/${IMAGE_NAME}:buildcache,mode=max"]
}

target "asynchronous" {
  inherits = ["base"]
  dockerfile = "Dockerfile"
  tags = ["${REGISTRY}/${IMAGE_NAME}:latest"]
  output = ["type=registry"]
  // build-args = {
  //   "BUILD_VERSION" = "${BUILD_VERSION}"
  //   "BUILD_DATE" = "${BUILD_DATE}"
  //   "GIT_COMMIT" = "${GIT_COMMIT}"
  // }
}

target "synchronous" {
  inherits = ["base"]
  dockerfile = "Dockerfile-full"
  tags = ["${REGISTRY}/${IMAGE_NAME}:latest-full"]
  output = ["type=registry"]
}
