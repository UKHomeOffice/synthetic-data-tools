#!/bin/bash

source venv/bin/activate
source ~/.bashrc

# Colours
BOLD_BLUE=$'\e[1;34m'
BLACK=$'\e[1;39m'
BOLD_RED=$'\e[1;31m'
LIGHT_GREEN=$'\e[1;92m'
DARK_GREY=$'\e[1;90m'
LIGHT_GREY=$'\e[1;37m'

# Title
TITLE="${LIGHT_GREEN}Please select an option: ${DARK_GREY}"

# Menus
DATASET_MENU="${DARK_GREY}Process Data Menu${DARK_GREY}"
SYNTH_MENU="${DARK_GREY}Train/Generate Data Menu${DARK_GREY}"
ANALYTICS_MENU="${DARK_GREY}Analyse Data Menu${DARK_GREY}"

# Options
CREATE_RAW_DATASET="${BOLD_BLUE}Create a new dataset${DARK_GREY}"
PREPARE_ANON_DATASET="${BOLD_BLUE}Prepare a dataset for anon/synth generation${DARK_GREY}"
GEN_DATA_SYNTH_DATASET="${BOLD_BLUE}Use a dataset to generate data using DataSynthesizer${DARK_GREY}"
TRAIN_GPT2="${BOLD_BLUE}Train GPT2 for case description/text analysis${DARK_GREY}"
GENERATE_GPT2="${BOLD_BLUE}Generate GPT2 text using a pre-trained model${DARK_GREY}"
AUGMENT_DATA="${BOLD_BLUE}Augment data back into synth datasets using pregenerated text${DARK_GREY}"
ANALYSE_DATA="${BOLD_BLUE}Analyse dataset and generate statistics${DARK_GREY}"
ELASTICSEARCH_ANALYSIS="${BOLD_BLUE}Analyse entities of fields using Transcribe/Elasticsearch${DARK_GREY}"
KIBANA_STATS="${BOLD_BLUE}Fetch and save Kibana entity statistics${DARK_GREY}"
QUIT="${BOLD_RED}Quit${DARK_GREY}"
BACK="${BOLD_RED}Back to Main Menu${DARK_GREY}"

echo $'\n'

# Process datasets Sub Menu
process_datasets_submenu () {
    while true; do
        echo "${DARK_GREY}"
        local PS3=$'\n'"${TITLE}"$'\n'
        local options=(
            "$CREATE_RAW_DATASET" 
            "$PREPARE_ANON_DATASET"
            "$AUGMENT_DATA"
            "$BACK"
        )
        local opt
        select opt in "${options[@]}"
        do
            case $opt in
            "$CREATE_RAW_DATASET")
                python3 ./data_processing_tools/create_raw_dataset.py
                break
                ;;
            "$PREPARE_ANON_DATASET")
                python3 ./data_processing_tools/process_input_dataset.py
                break
                ;;
            "$AUGMENT_DATA")
                python3 ./data_processing_tools/augment_datasets.py
                break
                ;;
            "$BACK")
                return
                ;;
            *) echo "${BOLD_RED}invalid option ${LIGHT_GREEN}$REPLY";;
            esac
        done
    done
}

# Train/Generate Synth Data Sub Menu
data_synth_submenu () {
    while true; do
        echo "${DARK_GREY}"
        local PS3=$'\n'"${TITLE}"$'\n'
        local options=(
            "$GEN_DATA_SYNTH_DATASET"
            "$TRAIN_GPT2"
            "$GENERATE_GPT2"
            "$BACK"
        )
        local opt
        select opt in "${options[@]}"
        do
            case $opt in
           "$GEN_DATA_SYNTH_DATASET")
                python3 ./data_synth_trainer/generate_synth_data.py
                break
                ;;
            "$TRAIN_GPT2")
                python3 ./gpt2_trainer/train_model.py
                break
                ;;
            "$GENERATE_GPT2")
                python3 ./gpt2_trainer/generate_text.py
                break
                ;;
            "$BACK")
                return
                ;;
            *) echo "${BOLD_RED}invalid option ${LIGHT_GREEN}$REPLY";;
            esac
        done
    done
}

# Analytics Sub Menu
analytics_submenu () {
    while true; do
        echo "${DARK_GREY}"
        local PS3=$'\n'"${TITLE}"$'\n'
        local options=(
            "$ANALYSE_DATA"
            "$ELASTICSEARCH_ANALYSIS"
            "$KIBANA_STATS"
            "$BACK"
        )
        local opt
        select opt in "${options[@]}"
        do
            case $opt in
            "$ANALYSE_DATA")
                python3 ./analytics_tools/dataframe_stats.py
                break
                ;;
            "$ELASTICSEARCH_ANALYSIS")
                python3 ./analytics_tools/entity_analysis.py
                break
                ;;
            "$KIBANA_STATS")
                python3 ./analytics_tools/kibana_stats.py
                break
                ;;
            "$BACK")
                return
                ;;
            *) echo "${BOLD_RED}invalid option ${LIGHT_GREEN}$REPLY";;
            esac
        done
    done
}

while true; do
    echo "${DARK_GREY}"
    PS3=$'\n'"${TITLE}"$'\n'
    options=(
        "$DATASET_MENU"
        "$SYNTH_MENU"
        "$ANALYTICS_MENU"
        "$QUIT"
    )
    select opt in "${options[@]}"
    do
        case $opt in
            "$DATASET_MENU")
                process_datasets_submenu
                break
                ;;
            "$SYNTH_MENU")
                data_synth_submenu
                break
                ;;
            "$ANALYTICS_MENU")
                analytics_submenu
                break
                ;;
            "$QUIT")
                break 2
                ;;
            *) echo "${BOLD_RED}invalid option ${LIGHT_GREEN}$REPLY";;
        esac
    done
done


deactivate