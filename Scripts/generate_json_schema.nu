def generate-key-arguments [restrictions: record] {
    let key = $restrictions.key
    $restrictions |
        reject key |
        transpose |
        rename key value |
        each {|$it| $'--arg ($key)_($it.key) ($it.value)'}
}

# Generates JSON schema.
def generate-schema [config_url: string] {
    let schema = 'http://json-schema.org/draft-07/schema'

    let non_inferred = [
        { key: use_this_config, type: [string, boolean] },
        { key: max_comments, type: [string, integer] },
        { key: recent_videos_amount, type: [string, integer], minimum: 1, maximum: 5000 },
        { key: autoASCII_sensitivity, type: [string, integer], minimum: 1, maximum: 3 },
        { key: enable_ban, type: [string, boolean] },
        { key: remove_all_author_comments, type: [string, boolean] },
        { key: whitelist_excluded, type: [string, boolean] },
        { key: enable_logging, type: [string, boolean] },
        { key: json_profile_picture, type: [string, boolean] },
        { key: minimum_duplicates, minimum: 3 },
        { key: minimum_duplicate_length, minimum: 1 },
        { key: levenshtein_distance, minimum: 0, maximum: 1 },
        { key: stolen_minimum_text_length, minimum: 1 },
        { key: your_channel_id, example: UCx123-BlahBlahExampleID },
        { key: videos_to_scan, example: xyzVidIDExample },
        { key: channel_to_scan, example: UCx123-BlahBlahExampleID },
        { key: channel_ids_to_filter, example: UCx123-BlahBlahExampleID }
    ]

    let additional_jq_args = ($non_inferred |
        each {|$it| generate-key-arguments $it} |
        flatten |
        str replace --all ', '  ',' |
        str replace --all '\[|\]' '' |
        str join " " |
        split row " ")

    http get --raw $config_url |
        jc --ini |
        str replace --all '"(\d+(\.\d+)?)"' '$1' |
        str replace --all '"(True)"' 'true' |
        str replace --all '"(False)"' 'false' |
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
        } + (. | wrap)' --arg url $config_url --arg schema $schema $additional_jq_args
}

def note [message: string] {
    print $'(ansi bg_green)note:(ansi reset)(ansi green) ($message)(ansi reset)'
}

def warn [message: string] {
    print $'(ansi bg_yellow)warning:(ansi reset)(ansi yellow) ($message)(ansi reset)'
}

def error [message: string] {
    print $'(ansi bg_red)error:(ansi reset)(ansi red) ($message)(ansi reset)'
}

def warn-when-path-exists [path: string] {
    if ($path | path exists) {
        warn $"'($path)' exists, do you want to overwrite it \(y/n)?"
        if (input) != "y" {
            exit
        }
    }
}

def error-when-dependency-does-not-exist [dependency: string, command: string, note?: string] {
    if (which $dependency) == [] {
        error $"'($dependency)' doesn't exist, to install it use '($command)'."
        if note != null {
            note $note
        }
        exit
    }
}

def main [
    --schema (-s): string # Path to result JSON schema from INI file for YAML config file.
    --ini-config (-i): string # Path to result INI config from YAML config file.
    --yaml-config (-y): string # Path to input YAML config.
    --setup-vscode (-v) # Whether to add yaml.schemas entry to settings.json for Visual Studio Code while generating JSON schema.
] {
    error-when-dependency-does-not-exist jq 'sudo apt install jq'
    error-when-dependency-does-not-exist jc 'pip3 install jc'
    error-when-dependency-does-not-exist dv 'gem install --user-install dupervisor' "Don't forget to add ~/.gem/ruby/<version>/bin to your PATH."

    let config_url = 'https://raw.githubusercontent.com/ThioJoe/YT-Spammer-Purge/main/assets/default_config.ini'

    if $schema != null {
        warn-when-path-exists $schema
        generate-schema $config_url | save --force $schema

        if $setup_vscode != null and $yaml_config != null {
            let vscode_settings = './.vscode/settings.json'
            if ($vscode_settings | path exists) {
                let modified_config = (jq $".[\"yaml.schemas\"][\"($schema)\"] = \"($yaml_config)\"" $vscode_settings)
                $modified_config | save --force $vscode_settings
            }
        }
        return
    }

    if $ini_config != null and $yaml_config != null {
        if not ($yaml_config | path exists) {
            error $"'($yaml_config)' doesn't exist."
            exit
        }

        warn-when-path-exists $ini_config
        dv --ini $yaml_config | save --force $ini_config
    }
}

