# Hammer Lifecycle Environment Information
What follows is the output of various `hammer lifecycle-environment --help` commands (as of nightly branch 2025-11-07),
demonstrating the flags each `hammer lifecycle-environment` action takes as parameters. Instructions are provided on
how to call each action through ForemanMCP.

## `hammer lifecycle-environment`
This subcommand can be executed with any actions and parameters using the `execute_hammer` tool.
Example `hammer lifecycle-environment --help`
```
$ hammer lifecycle-environment --help
Usage:
    hammer lifecycle-environment [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
 SUBCOMMAND                    Subcommand
 [ARG] ...                     Subcommand arguments

Subcommands:
 create                        Create an environment
 delete                        Destroy an environment
 info                          Show an environment
 list                          List environments in an organization
 paths                         List environment paths
 update                        Update an environment

Options:
 -h, --help                    Print help
```

## `hammer lifecycle-environment create`
This subcommand can be generated with using the `generate_hammer_lifecycle_environment_create` resource and can be executed using the `execute_hammer_lifecycle_environment_create` tool. More in-depth operations require the use of the `execute_hammer` tool.
```
$ hammer lifecycle-environment create --help
Usage:
    hammer lifecycle-environment create [OPTIONS]

Options:
 --description VALUE                            Description of the environment
 --label VALUE                                  Label of the environment
 --name VALUE                                   Name of the environment
 --organization[-id|-title|-label] VALUE/NUMBER Name of organization
 --path-id NUMBER                               If you are adding an environment to an existing path after Library, pass the id
                                                of the environment that is the current successor of Library in the path. It has
                                                to be the id of the old environment following library in this path.
 --prior VALUE                                  Name of the prior environment
 --prior-id NUMBER                              Id of an environment that is prior to the new environment in the chain. It has
                                                to be either the id of Library or the id of an environment at the end of a
                                                chain.
 --registry-name-pattern VALUE                  Pattern for container image names
 --registry-unauthenticated-pull BOOLEAN        Allow unauthenticed pull of container images
 -h, --help                                     Print help

Option details:
  Here you can find option types and the value an option can accept:

  BOOLEAN             One of true/false, yes/no, 1/0
  DATETIME            Date and time in YYYY-MM-DD HH:MM:SS or ISO 8601 format
  ENUM                Possible values are described in the option's description
  FILE                Path to a file
  KEY_VALUE_LIST      Comma-separated list of key=value.
                      JSON is acceptable and preferred way for such parameters
  LIST                Comma separated list of values. Values containing comma should be quoted or escaped with backslash.
                      JSON is acceptable and preferred way for such parameters
  MULTIENUM           Any combination of possible values described in the option's description
  NUMBER              Numeric value. Integer
  SCHEMA              Comma separated list of values defined by a schema.
                      JSON is acceptable and preferred way for such parameters
  VALUE               Value described in the option's description. Mostly simple string
```

## `hammer lifecycle-environment delete`
This subcommand can be generated using the `generate_hammer_lifecycle_environment_delete` resource and can be executed using the `execute_hammer_lifecycle_environment_delete` tool. Deletion by id requires the use of the `execute_hammer` tool.
```
$ hammer lifecycle-environment delete --help
Usage:
    hammer lifecycle-environment <delete|destroy> [OPTIONS]

Options:
 --id NUMBER                                    Id of the environment
 --name VALUE                                   Lifecycle environment name to search by
 --organization[-id|-title|-label] VALUE/NUMBER Organization identifier
 -h, --help                                     Print help

Option details:
  Here you can find option types and the value an option can accept:

  BOOLEAN             One of true/false, yes/no, 1/0
  DATETIME            Date and time in YYYY-MM-DD HH:MM:SS or ISO 8601 format
  ENUM                Possible values are described in the option's description
  FILE                Path to a file
  KEY_VALUE_LIST      Comma-separated list of key=value.
                      JSON is acceptable and preferred way for such parameters
  LIST                Comma separated list of values. Values containing comma should be quoted or escaped with backslash.
                      JSON is acceptable and preferred way for such parameters
  MULTIENUM           Any combination of possible values described in the option's description
  NUMBER              Numeric value. Integer
  SCHEMA              Comma separated list of values defined by a schema.
                      JSON is acceptable and preferred way for such parameters
  VALUE               Value described in the option's description. Mostly simple string
```

## `hammer lifecycle-environment info`
This subcommand can be generated using the `generate_hammer_lifecycle_environment_info` resource and can be executed using the `execute_hammer_lifecycle_environment_info` resource. Info by ID or info containing non-default fields requires the use of the `execute_hammer` tool.
```
$ hammer lifecycle-environment info --help
Usage:
    hammer lifecycle-environment <info|show> [OPTIONS]

Options:
 --fields LIST                                  Show specified fields or predefined field sets only. (See below)
 --id NUMBER                                    Id of the environment
 --name VALUE                                   Lifecycle environment name to search by
 --organization[-id|-title|-label] VALUE/NUMBER Name/title/label/id of the organization
 -h, --help                                     Print help

Predefined field sets:
  ----------------------------|-----|---------|-----
  FIELDS                      | ALL | DEFAULT | THIN
  ----------------------------|-----|---------|-----
  Id                          | x   | x       | x
  Name                        | x   | x       | x
  Label                       | x   | x       |
  Description                 | x   | x       |
  Organization                | x   | x       |
  Library                     | x   | x       |
  Prior lifecycle environment | x   | x       |
  Unauthenticated pull        | x   | x       |
  Registry name pattern       | x   | x       |
  ----------------------------|-----|---------|-----

Option details:
  Here you can find option types and the value an option can accept:

  BOOLEAN             One of true/false, yes/no, 1/0
  DATETIME            Date and time in YYYY-MM-DD HH:MM:SS or ISO 8601 format
  ENUM                Possible values are described in the option's description
  FILE                Path to a file
  KEY_VALUE_LIST      Comma-separated list of key=value.
                      JSON is acceptable and preferred way for such parameters
  LIST                Comma separated list of values. Values containing comma should be quoted or escaped with backslash.
                      JSON is acceptable and preferred way for such parameters
  MULTIENUM           Any combination of possible values described in the option's description
  NUMBER              Numeric value. Integer
  SCHEMA              Comma separated list of values defined by a schema.
                      JSON is acceptable and preferred way for such parameters
  VALUE               Value described in the option's description. Mostly simple string
```

## `hammer lifecycle-environment list`
This subcommand can be generated using the `generate_hammer_lifecycle_environment_list` resource and can be executed using the `execute_hammer_lifecycle_environment_list` resource. Passing in parameters requires use of the `execute_hammer` tool.
```
$ hammer lifecycle-environment list --help
Usage:
    hammer lifecycle-environment <list|index> [OPTIONS]

Options:
 --fields LIST                                  Show specified fields or predefined field sets only. (See below)
 --full-result BOOLEAN                          Whether or not to show all results
 --label VALUE                                  Filter only environments containing this label
 --library BOOLEAN                              Set true if you want to see only library environments
 --name VALUE                                   Filter only environments containing this name
 --order VALUE                                  Sort field and order, eg. 'id DESC'
 --organization[-id|-title|-label] VALUE/NUMBER Organization identifier
 --page NUMBER                                  Page number, starting at 1
 --per-page NUMBER                              Number of results per page to return
 --search VALUE                                 Search string
 -h, --help                                     Print help

Predefined field sets:
  -------|-----|---------|-----
  FIELDS | ALL | DEFAULT | THIN
  -------|-----|---------|-----
  Id     | x   | x       | x
  Name   | x   | x       | x
  Prior  | x   | x       |
  -------|-----|---------|-----

Option details:
  Here you can find option types and the value an option can accept:

  BOOLEAN             One of true/false, yes/no, 1/0
  DATETIME            Date and time in YYYY-MM-DD HH:MM:SS or ISO 8601 format
  ENUM                Possible values are described in the option's description
  FILE                Path to a file
  KEY_VALUE_LIST      Comma-separated list of key=value.
                      JSON is acceptable and preferred way for such parameters
  LIST                Comma separated list of values. Values containing comma should be quoted or escaped with backslash.
                      JSON is acceptable and preferred way for such parameters
  MULTIENUM           Any combination of possible values described in the option's description
  NUMBER              Numeric value. Integer
  SCHEMA              Comma separated list of values defined by a schema.
                      JSON is acceptable and preferred way for such parameters
  VALUE               Value described in the option's description. Mostly simple string

Search / Order fields:
  id                  integer
  label               string
  name                string
  organization_id     integer
```

## `hammer lifecycle-environment paths`
This subcommand can be executed using the `execute_hammer` tool.
```
$ hammer lifecycle-environment paths --help
Usage:
    hammer lifecycle-environment paths [OPTIONS]

Options:
 --content-source-id NUMBER                     Show whether each lifecycle environment is associated with the given Smart Proxy
                                                id.
 --fields LIST                                  Show specified fields or predefined field sets only. (See below)
 --organization[-id|-title|-label] VALUE/NUMBER Organization identifier
 --permission-type VALUE                        The associated permission type. One of (readable | promotable) Default: readable
 -h, --help                                     Print help

Predefined field sets:
  ---------------|-----|--------
  FIELDS         | ALL | DEFAULT
  ---------------|-----|--------
  Lifecycle path | x   | x
  ---------------|-----|--------

Option details:
  Here you can find option types and the value an option can accept:

  BOOLEAN             One of true/false, yes/no, 1/0
  DATETIME            Date and time in YYYY-MM-DD HH:MM:SS or ISO 8601 format
  ENUM                Possible values are described in the option's description
  FILE                Path to a file
  KEY_VALUE_LIST      Comma-separated list of key=value.
                      JSON is acceptable and preferred way for such parameters
  LIST                Comma separated list of values. Values containing comma should be quoted or escaped with backslash.
                      JSON is acceptable and preferred way for such parameters
  MULTIENUM           Any combination of possible values described in the option's description
  NUMBER              Numeric value. Integer
  SCHEMA              Comma separated list of values defined by a schema.
                      JSON is acceptable and preferred way for such parameters
  VALUE               Value described in the option's description. Mostly simple string
```

## `hammer lifecycle-environment update`
This subcommand can be executed using the `execute_hammer` tool. 
Example: `hammer lifecycle-environment update --organization "Default Organization" --name "Old name" --new-name "New name"`
```
$ hammer lifecycle-environment update --help
Usage:
    hammer lifecycle-environment update [OPTIONS]

Options:
 --async BOOLEAN                                Do not wait for the update action to finish. Default: true
 --description VALUE                            Description of the environment
 --id NUMBER                                    Id of the environment
 --name VALUE                                   Lifecycle environment name to search by
 --new-name VALUE                               New name to be given to the environment
 --organization[-id|-title|-label] VALUE/NUMBER Name of the organization
 --registry-name-pattern VALUE                  Pattern for container image names
 --registry-unauthenticated-pull BOOLEAN        Allow unauthenticed pull of container images
 -h, --help                                     Print help

Option details:
  Here you can find option types and the value an option can accept:

  BOOLEAN             One of true/false, yes/no, 1/0
  DATETIME            Date and time in YYYY-MM-DD HH:MM:SS or ISO 8601 format
  ENUM                Possible values are described in the option's description
  FILE                Path to a file
  KEY_VALUE_LIST      Comma-separated list of key=value.
                      JSON is acceptable and preferred way for such parameters
  LIST                Comma separated list of values. Values containing comma should be quoted or escaped with backslash.
                      JSON is acceptable and preferred way for such parameters
  MULTIENUM           Any combination of possible values described in the option's description
  NUMBER              Numeric value. Integer
  SCHEMA              Comma separated list of values defined by a schema.
                      JSON is acceptable and preferred way for such parameters
  VALUE               Value described in the option's description. Mostly simple string
```