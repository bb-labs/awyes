# awyes action

This action deploys any boto3 resource with ease. A simple awyes.yml does the trick! 

## Inputs

### `root`

The directory containing your awyes.yml. Defaults to `.`.


## Example usage

uses: actions/awyes@v1
with:
  root: '/project'