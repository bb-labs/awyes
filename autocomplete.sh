#compdef awyes

_arguments \
  '--config[path to awyes config]:filename:_files' \
  '--env[path to env file]:filename:_files' \
  '--preview[dry run the actions]' \
  '--workflow[run a particular workflow]:workflow_name:->workflow' \
  '--action[name of one-off action to run]:action_name:->action' \
  '*--set[override or set and env variable]:env_variable:->set'=

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
  validate_path "./awyes.yml" && _values 'awyes actions' \
    $(yq 'to_entries | .[] | .key + "." + (.value | keys | .[])' $valid_path)
  ;;
workflow)
  validate_path "./awyes.yml" && _values 'awyes workflows' \
    $(yq '.[][] | select(.workflow) | .workflow' $valid_path | sort | uniq | sed "s/[^[:alnum:]]//g")
  ;;
esac
