#!/usr/bin/env sh

# Modified from the original in python-worker directory in https://github.com/jkenlooper/cookiecutters .

set -o errexit


project_dir="$(dirname "$(realpath "$0")")"
script_name="$(basename "$0")"
project_name="$(basename "$project_dir")-dep"

name_hash="$(printf "%s" "$project_dir" | md5sum | cut -d' ' -f1)"
test "${#name_hash}" -eq "32" || (echo "ERROR $script_name: Failed to create a name hash from the directory ($project_dir)" && exit 1)

usage() {
  cat <<HERE
Update the python requirement txt files, check for known vulnerabilities,
download local python packages to dep/.

Usage:
  $script_name -h
  $script_name -i
  $script_name

Options:
  -h                  Show this help message.
  -i                  Switch to interactive mode.

HERE
}

interactive="n"

while getopts "hi" OPTION ; do
  case "$OPTION" in
    h) usage
       exit 0 ;;
    i)
       interactive="y"
       ;;
    ?) usage
       exit 1 ;;
  esac
done
shift $((OPTIND - 1))

mkdir -p "$project_dir/dep"
image_name="$project_name-$name_hash"
docker image rm "$image_name" > /dev/null 2>&1 || printf ""
DOCKER_BUILDKIT=1 docker build \
  --quiet \
  -t "$image_name" \
  -f "$project_dir/update-dep.Dockerfile" \
  "$project_dir" > /dev/null

container_name="$project_name-$name_hash"
if [ "$interactive" = "y" ]; then
  docker run -i --tty \
    --user root \
    --name "$container_name" \
    "$image_name" sh > /dev/null

else
  docker run -d \
    --name "$container_name" \
    "$image_name" > /dev/null
fi

docker cp "$container_name:/home/dev/app/requirements.txt" "$project_dir/requirements.txt"
docker cp "$container_name:/home/dev/app/requirements-dev.txt" "$project_dir/requirements-dev.txt"
docker cp "$container_name:/home/dev/app/requirements-test.txt" "$project_dir/requirements-test.txt"
docker cp "$container_name:/home/dev/app/dep/." "$project_dir/dep/"
# Only copy over the security issues if there are any.
rm -f "$project_dir/security-issues-from-bandit.txt"
docker cp "$container_name:/home/dev/security-issues-from-bandit.txt" "$project_dir/security-issues-from-bandit.txt" > /dev/null 2>&1 || echo "Bandit approves!"
docker stop --time 0 "$container_name" > /dev/null 2>&1 || printf ""
docker rm "$container_name" > /dev/null 2>&1 || printf ""
