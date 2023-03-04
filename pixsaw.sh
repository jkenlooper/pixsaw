#!/usr/bin/env sh

set -o errexit

project_dir="$(dirname "$(realpath "$0")")"
script_name="$(basename "$0")"
project_name="$(basename "$project_dir")"

project_name_hash="$(printf "%s" "$project_dir" | md5sum | cut -d' ' -f1)"
test "${#project_name_hash}" -eq "32" || (echo "ERROR $script_name: Failed to create a project name hash from the project dir ($project_dir)" && exit 1)

echo "INFO $script_name: Running update-dep.sh script to update dependencies"
"$project_dir/update-dep.sh"

image_name="$(printf '%s' "$project_name-$project_name_hash" | grep -o -E '^.{0,63}')"
container_name="$(printf '%s' "$project_name-$project_name_hash" | grep -o -E '^.{0,63}')"
docker stop --time 1 "$container_name" > /dev/null 2>&1 || printf ''
docker container rm "$container_name" > /dev/null 2>&1 || printf ''
docker image rm "$image_name" > /dev/null 2>&1 || printf ""

echo "INFO $script_name: Building docker image: $image_name"
DOCKER_BUILDKIT=1 docker build \
    --quiet \
    -t "$image_name" \
    "$project_dir" > /dev/null

echo "INFO $script_name: Creating files in output/ directory from examples/"
docker run -i --tty \
    --name "$container_name" \
    --mount "type=bind,src=$project_dir/examples,dst=/examples" \
    "$image_name" --dir=/home/dev/app/output --lines=/examples/small-puzzle-lines.png /examples/320px-White_Spoon_Osteospermum.jpg
docker cp "$container_name:/home/dev/app/output" "$project_dir"
docker stop --time 1 "$container_name" > /dev/null 2>&1 || printf ''
docker container rm "$container_name" > /dev/null 2>&1 || printf ''
