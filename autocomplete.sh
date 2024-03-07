#compdef awyes

_arguments \
'--path[root path to all awyes files]:filename:_files' \
'--dry[dry run the actions]' \
'--quiet[only print the actions]' \
'*:action_name:->action'


files=$(find . -name "awyes*.yml" -exec echo -n {} \; -exec echo -n ' ' \;)


case $state in
    action)
        _values 'awyes actions' $(echo $files | xargs yq 'select(.) | keys | .[]' | grep "[^---]")
    ;;
esac
