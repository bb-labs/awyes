# awyes docker action

This action prints deploys lambdas with ease. Simple aws.json file does the trick! 

## Inputs

### `config`

The directory containing your aws.json. Defaults to `/aws`.

### `src`

The directory containing your source. Defaults to `/src`.


## Example usage

uses: actions/awyes@v1
with:
  config: '/aws'
  src: '/src'