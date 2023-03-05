#!/usr/bin/env sh

set -o errexit

script_name="$(basename "$0")"
project_name="$(basename "$0" ".sh")"
echo "
Try out '$project_name' by prompting for necessary options and isolating it to a docker container.
"

# Use $PWD to avoid using 'realpath' since it isn't always available.
project_dir="$PWD"
test -e "$project_dir/$script_name" || (echo "ERROR: Should run $script_name from the $project_name project directory." 1>&2 && exit 1)

# Exit early if required commands are not available.
for cmd in \
  "docker" \
  ; do
  has_cmd="$(command -v "$cmd" || echo "no")"
  if [ "$has_cmd" = "no" ]; then
    echo "ERROR: This script requires the '$cmd' command." 1>&2
    exit 1
  fi
done

# Make sure docker daemon is running first before prompting the user.
is_docker_up="$(docker ps -q -l || echo "no")"
if [ "$is_docker_up" = "no" ]; then
  echo "ERROR: Failed check if docker daemon was ready. Start docker daemon first." 1>&2
  exit 1
fi

echo "INFO $script_name: Running update-dep.sh script to update dependencies..."
"$project_dir/update-dep.sh"

image_name="$project_name"
container_name="$project_name"
docker stop --time 1 "$container_name" > /dev/null 2>&1 || printf ''
docker container rm "$container_name" > /dev/null 2>&1 || printf ''
docker image rm "$image_name" > /dev/null 2>&1 || printf ""

echo "INFO $script_name: Building docker image: $image_name"
DOCKER_BUILDKIT=1 docker build \
    --quiet \
    -t "$image_name" \
    "$project_dir" > /dev/null

# Use prompts instead of passing options since this is only for demonstration purposes.
echo "
---
"

default_lines_file="examples/small-puzzle-lines.png"
echo "Enter the relative file path for the lines image.
Default: $default_lines_file"
read -r lines_file
lines_file="${lines_file:-$default_lines_file}"
lines_file="$project_dir/$lines_file"
test -e "$lines_file" || (echo "ERROR: File doesn't exist: $lines_file" 1>&2 && exit 1)

default_image_file="examples/320px-White_Spoon_Osteospermum.jpg"
echo "Enter the relative file path for the image to cut into pieces.
Default: $default_image_file"
read -r image_file
image_file="${image_file:-$default_image_file}"
image_file="$project_dir/$image_file"
test -e "$image_file" || (echo "ERROR: File doesn't exist: $image_file" 1>&2 && exit 1)

default_output_dir="output"
echo "Enter the relative directory path to output the files to.
Default: $default_output_dir"
read -r output_dir
output_dir="${output_dir:-$default_output_dir}"
output_dir="$project_dir/$output_dir"
mkdir -p "$output_dir" || printf ""
test -d "$output_dir" || (echo "ERROR: Directory doesn't exist: $output_dir" 1>&2 && exit 1)

echo "
---
"

echo "INFO $script_name: Creating files in $output_dir directory."
bn_lines_file="$(basename "$lines_file")"
bn_image_file="$(basename "$image_file")"
docker run -i --tty \
    --name "$container_name" \
    --mount "type=bind,src=$lines_file,dst=/data/$bn_lines_file,readonly=true" \
    --mount "type=bind,src=$image_file,dst=/data/$bn_image_file,readonly=true" \
    "$image_name" --dir=/home/dev/app/output --lines="/data/$bn_lines_file" "/data/$bn_image_file"
docker cp "$container_name:/home/dev/app/output/" "$output_dir"
docker stop --time 1 "$container_name" > /dev/null 2>&1 || printf ''
docker container rm "$container_name" > /dev/null 2>&1 || printf ''
