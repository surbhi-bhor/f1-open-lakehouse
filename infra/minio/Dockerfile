# MinIO Inc. stopped publishing community images and binaries (Docker Hub 404, dl.min.io 410),
# so this builds the last official releases from upstream source, pinned to exact commits.
ARG GO_IMAGE=golang:1.24.9-bookworm
ARG RUNTIME_IMAGE=debian:12.12-slim

FROM ${GO_IMAGE} AS build
ARG MINIO_RELEASE
ARG MINIO_COMMIT
ARG MC_RELEASE
ARG MC_COMMIT
ENV CGO_ENABLED=0
# One package at a time with a capped heap: a full-speed build exhausted Windows memory and crashed WSL.
ENV GOFLAGS=-p=1 GOMEMLIMIT=1500MiB
# Fail the build if a release tag was ever moved to a different commit.
RUN git clone --depth 1 --branch "${MINIO_RELEASE}" https://github.com/minio/minio /src/minio \
 && test "$(git -C /src/minio rev-parse HEAD)" = "${MINIO_COMMIT}" \
 && cd /src/minio && go build -trimpath -ldflags "-s -w" -o /out/minio .
RUN git clone --depth 1 --branch "${MC_RELEASE}" https://github.com/minio/mc /src/mc \
 && test "$(git -C /src/mc rev-parse HEAD)" = "${MC_COMMIT}" \
 && cd /src/mc && go build -trimpath -ldflags "-s -w" -o /out/mc .

FROM ${RUNTIME_IMAGE}
COPY --from=build /out/minio /out/mc /usr/local/bin/
ENTRYPOINT ["minio"]
