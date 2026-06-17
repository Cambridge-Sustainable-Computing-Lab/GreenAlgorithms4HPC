#!/bin/bash
#SBATCH --job-name=green-alma
#SBATCH --output=GreenAlma/green-alma.out
#SBATCH --error=GreenAlma/green-alma.err
#SBATCH --partition=compute
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --time=01:00:00
#SBATCH --mem-per-cpu=4000

app_path="$1"
env_path="$2"
username="$3"
start_date="$4"
end_date="$5"

userCWD="$(pwd)/GreenAlma"

# echo "userCWD=$userCWD"
# echo "app_path=$app_path"
# echo "env_path=$env_path"
# echo "start_date=$start_date"
# echo "end_date=$end_date"

source /data/rds/DIT/SCICOM/SCRSE/shared/source/.mamba

cd "$app_path"

mamba run --no-capture-output -p "$env_path" \
    python3 "$app_path/__init__.py" --userCWD "$userCWD" --user "$username" --startDay "$start_date" --endDay "$end_date"