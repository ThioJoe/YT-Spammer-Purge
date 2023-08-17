#!/usr/bin/env sh

reset_color='\e[0m'
green_color='\e[32m'
background_green_color='\e[42m'
yellow_color='\e[33m'
background_yellow_color='\e[43m'
red_color='\e[31m'
background_red_color='\e[41m'

generate_json_schema() {
    gjs_in_config_url="$1"

    gjs_schema='http://json-schema.org/draft-07/schema'
    
    non_infered='{ "key": "use_this_config", "type": ["string", "boolean"] }
{ "key": "max_comments", "type": ["string", "integer"] }
{ "key": "recent_videos_amount", "type": ["string", "integer"], "minimum": 1, "maximum": 5000 }
{ "key": "autoASCII_sensitivity", "type": ["string", "integer"], "minimum": 1, "maximum": 3 }
{ "key": "enable_ban", "type": ["string", "boolean"] }
{ "key": "remove_all_author_comments", "type": ["string", "boolean"] }
{ "key": "whitelist_excluded", "type": ["string", "boolean"] }
{ "key": "enable_logging", "type": ["string", "boolean"] }
{ "key": "json_profile_picture", "type": ["string", "boolean"] }
{ "key": "minimum_duplicates", "minimum": 3 }
{ "key": "minimum_duplicate_length", "minimum": 1 }
{ "key": "levenshtein_distance", "minimum": 0, "maximum": 1 }
{ "key": "stolen_minimum_text_length", "minimum": 1 }
{ "key": "your_channel_id", "example": "UCx123-BlahBlahExampleID" }
{ "key": "videos_to_scan", "example": "xyzVidIDExample" }
{ "key": "channel_to_scan", "example": "UCx123-BlahBlahExampleID" }
{ "key": "channel_ids_to_filter", "example": "UCx123-BlahBlahExampleID" }'

    gjs_temp_script="$(mktemp)"
    echo "#!/usr/bin/env sh

in_restrictions=\"\$1\"

key=\"\$(echo \"\$in_restrictions\" | jq '.key')\"
echo \"\$in_restrictions\" | jq -r \"del(.key) | to_entries[] | . = \\\"--arg \\(\$key)_\\(.key) \\(.value)\\\"\"" > "$gjs_temp_script"

    gjs_additional_jq_args="$(echo "$non_infered" |
        xargs -n 1 -d '\n' sh "$gjs_temp_script" |
        sed -E 's/, /,/g
            s/\[|\]//g
            s/"//g')"
    
    # shellcheck disable=SC2086
    wget -O - "$gjs_in_config_url" 2> /dev/null |
        jc --ini |
        sed -E 's/"([[:digit:]]+(\.[[:digit:]]+)?)"/\1/g
            s/"(True|False)"/\l\1/g' |
        jq 'def to_title: . | gsub("_"; " ") | ascii_downcase;
        def to_description: . | to_title + "\n" + $url;
        
        def to_singular:
            if . | test("^[aeiouy]"; "i") then
                . | sub("^(?<x>.*?)s\n"; "An \(.x)\n")
            else
                . | sub("^(?<x>.*?)s\n"; "A \(.x)\n")
            end;

        def to_type(key; value):
            (key + "_type") as $type |
            if $ARGS.named[$type] != null then
                $ARGS.named[$type] | split(",")
            else
                value | type
            end;

        def to_restrictions:
            (. + "_minimum") as $min |
            (. + "_maximum") as $max |
            if $ARGS.named[$min] != null then
                { minimum: $ARGS.named[$min] | tonumber }
            else
                {}
            end +
            if $ARGS.named[$max] != null then
                { maximum: $ARGS.named[$max] | tonumber }
            else
                {}
            end;

        def to_example:
            (. + "_example") as $example |
            if $ARGS.named[$example] != null then
                { examples: [$ARGS.named[$example]] }
            else
                {}
            end;
        
        def wrap: {
            type: "object",
            properties: with_entries(
                if .value | type != "object" then
                    {
                        key,
                        value: ({
                            title: .key | to_title,
                            description: .key | to_description,
                            type: to_type(.key; .value),
                        } +
                        if .value | tostring | test("^\\d+$") then
                            { type: "integer" }
                        else
                            {}
                        end +
                        (.key | to_restrictions) +
                        {
                            default: .value
                        } +
                        (.key | to_example))
                    }
                else
                    .value = {
                        title: .key | to_title,
                        description: .key | to_description
                    } + (.value | wrap) + {
                        additionalProperties: false
                    }
                end)
            };
        
        {
            "$schema": $schema,
            title: "config",
            description: "A config"
        } + (. | wrap)' --arg url "$gjs_in_config_url" --arg schema "$gjs_schema" $gjs_additional_jq_args
}

note() {
    n_in_message="$1"
    printf "${background_green_color}note:$reset_color$green_color %s$reset_color" "$n_in_message"
}

warn() {
    w_in_message="$1"
    printf "${background_yellow_color}warning:$reset_color$yellow_color %s$reset_color" "$w_in_message"
}

error() {
    e_in_message="$1"
    printf "${background_red_color}error:$reset_color$red_color %s$reset_color" "$e_in_message"
}

warn_when_path_exists() {
    wwpe_in_path="$1"
    [ -e "$wwpe_in_path" ] && {
        warn "'$wwpe_in_path' exists, do you want to overwrite it (y/n)?"
        read -r reply
        [ "$reply" != "y" ] && {
            exit
        }
    }
}

error_when_dependency_does_not_exist() {
    ewddne_in_dependency="$1"
    ewddne_in_command="$2"
    ewddne_in_note="$3"

    ! which "$ewddne_in_dependency" > /dev/null && {
        error "'$ewddne_in_dependency' doesn't exist, to install it use '$ewddne_in_command'."
        [ -n "$note" ] && note "$ewddne_in_note"
    }
}

error_when_dependency_does_not_exist jq 'sudo apt install jq'
error_when_dependency_does_not_exist jc 'pip3 install jc'
error_when_dependency_does_not_exist dv 'gem install --user-install dupervisor' "Don't forget to add ~/.gem/ruby/<version>/bin to your PATH."

setup_vscode=

while [ -n "$1" ]; do
    in_option="$1"
    in_argument="$2"

    case "$in_option" in
        --schema|-s)
            in_schema="$in_argument"
            shift
            ;;
        --ini-config|-i)
            in_ini_config="$in_argument"
            shift
            ;;
        --yaml-config|-y)
            in_yaml_config="$in_argument"
            shift
            ;;
        --setup_vscode|-v)
            setup_vscode=true
            ;;
        *)
            error "'$in_option' is not supported."
            exit
            ;;
    esac

    shift
done

config_url='https://raw.githubusercontent.com/ThioJoe/YT-Spammer-Purge/main/assets/default_config.ini' 2> /dev/null

[ -n "$in_schema" ] && {
    warn_when_path_exists "$in_schema"
    generate_json_schema "$config_url" > "$in_schema"

    [ -n "$setup_vscode" ] && [ -n "$in_yaml_config" ] && {
        vscode_settings='./../.vscode/settings.json'
        [ -e "$vscode_settings" ] && {
            modified_config="$(jq '.["yaml.schemas"][$ARGS.named["schema"]] = $ARGS.named["yaml_config"]' --arg schema "$in_schema" --arg yaml_config "$in_yaml_config" "$vscode_settings")"
            echo "$modified_config" > "$vscode_settings"
        }
    }
    exit
}

[ -n "$in_ini_config" ] && [ -n "$in_yaml_config" ] && {
    [ ! -e "$in_yaml_config" ] && {
        error "'$in_yaml_config' doesn't exist."
        exit
    }

    warn_when_path_exists "$in_ini_config"
    dv --ini "$in_yaml_config" > "$in_ini_config"
}