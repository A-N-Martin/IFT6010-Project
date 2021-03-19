#!/bin/bash

FOLDER="/home/Allmightyme/IFT6010-Project"
config_file=${1}
cfg_path="${FOLDER}/config_files/${config_file}"

# Check if config file is valid
if [ -z "${config_file}" ]; then
      echo "Error: \$config_file argument is empty"
      exit 1
fi
if [ ! -e "${cfg_path}" ]; then
    echo "Error: cfg_path=${cfg_path} does not exist"
    exit 1
fi

# Launch your job, and look for the dataset into $SLURM_TMPDIR
python -m train_transformer \
        --cfg_path "${cfg_path}" \
        --data_path "${FOLDER}" \
        --save_path "${FOLDER}/results"
