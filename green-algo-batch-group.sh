#!/bin/bash
#SBATCH --job-name=green-alma-group
#SBATCH --output=GreenAlma/green-alma-group.out
#SBATCH --error=GreenAlma/green-alma-group.err
#SBATCH --partition=compute
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --time=01:00:00
#SBATCH --mem-per-cpu=4000

app_path="$1"
env_path="$2"
usernames="$3"
start_date="$4"
end_date="$5"

userCWD="$(pwd)/GreenAlma"

source /data/rds/DIT/SCICOM/SCRSE/shared/source/.mamba

cd "$app_path"

IFS=',' read -ra usernames <<< "$usernames"
for user in "${usernames[@]}"; do
    echo "$user"
    mamba run --no-capture-output -p "$env_path" \
        python3 "$app_path/__init__.py" --userCWD "$userCWD" --user "$user" --startDay "$start_date" --endDay "$end_date"
done