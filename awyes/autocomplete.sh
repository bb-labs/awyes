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

# parser.add_argument(
#     '-v', '--verbose', action=argparse.BooleanOptionalAction, default=True,
#     help="Enable logging")
# parser.add_argument(
#     '-d', '--include-deps', action=argparse.BooleanOptionalAction, default=True,
#     help="When specifying an action, whether to include dependent actions")
# parser.add_argument(
#     '--include-docker', action=argparse.BooleanOptionalAction,
#     default=True,
#     help="Include a docker client")

# parser.add_argument('-w', '--workflow', type=str, required=False, default="",
#                     help='The awyes workflow type')
# parser.add_argument('--config', type=str, required=False,
#                     default="awyes.yml", help='Path to awyes config')
# parser.add_argument('--clients', type=str, required=False,
#                     default="awyes.py",
#                     help='Path to user specified awyes clients')
# parser.add_argument('-r', '--raw', type=str, required=False, default="",
#                     help='Raw config to use in place of path')
# parser.add_argument('-a', '--action', type=str, required=False, default="",
#                     help="The action name to run")
