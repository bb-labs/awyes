#compdef awyes

_arguments \
'--path[root path to all awyes files]:filename:_files' \
'--dry[dry run the actions]' \
'--quiet[only print the actions]' \
'*:action_name:->action'

function validate_path {
    if eval realpath $1 >/dev/null 2>/dev/null; then
        valid_path=$(realpath $1)
    fi
    
    for ((i = 1; i <= $#words - 1; i++)); do
        if [[ $words[$i] == --config && ! -z $words[$((i + 1))] ]]; then
            maybe_valid_path=$words[$((i + 1))]
            if eval realpath $maybe_valid_path >/dev/null 2>/dev/null; then
                valid_path=$(eval realpath $maybe_valid_path)
            fi
        fi
    done
    
    [[ ! -z $valid_path ]]
}

case $state in
    action)
        validate_path "./awyes.yml" && _values 'awyes workflows' \
        $(yq 'select(.) | keys | .[]' $valid_path | grep "[^---]")
    ;;
esac
