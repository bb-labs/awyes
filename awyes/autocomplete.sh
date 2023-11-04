#compdef awyes

local state
local config_path
local awyes_actions

_arguments \
  '--config[path to awyes config]:filename:_files' \
  '--preview[dry run the actions]' \
  '--workflow[run a particular workflow]:workflow_name:->workflow' \
  '--action[name of one-off action to run]:action_name:->action'

function valid_config_path {
  if eval realpath ./awyes.yml >/dev/null 2>/dev/null; then
    config_path=$(realpath ./awyes.yml)
  fi

  for ((i = 1; i <= $#words - 1; i++)); do
    if [[ $words[$i] == --config && ! -z $words[$((i + 1))] ]]; then
      maybe_config_path=$words[$((i + 1))]
      if eval realpath $maybe_config_path >/dev/null 2>/dev/null; then
        config_path=$(eval realpath $maybe_config_path)
      fi
    fi
  done

  [[ ! -z $config_path ]]
}

case $state in
action)
  valid_config_path && _values 'awyes actions' \
    $(yq 'to_entries | .[] | .key + "." + (.value | keys | .[])' $config_path)
  ;;
workflow)
  valid_config_path && _values 'awyes workflows' \
    $(yq '.[][] | select(.workflow) | .workflow' $config_path | sort | uniq | sed "s/[^[:alnum:]]//g")
  ;;
esac
