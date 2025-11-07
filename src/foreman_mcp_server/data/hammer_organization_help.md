# Hammer Organization Information
What follows is the output of various `hammer organization --help` commands (as of nightly branch 2025-11-10),
demonstrating the flags each `hammer organization` action takes as parameters. Instructions are provided on
how to call each action through ForemanMCP.

## `hammer organization`
This subcommand can be executed with any actions and parameters using the `execute_hammer` tool.
Example `hammer organization --help`
```
$ hammer organization --help
Usage:
    hammer organization [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
 SUBCOMMAND                    Subcommand
 [ARG] ...                     Subcommand arguments

Subcommands:
 add-compute-resource          Associate a compute resource
 add-domain                    Associate a domain
 add-hostgroup                 Associate a hostgroup
 add-location                  Associate a location
 add-medium                    Associate a medium
 add-provisioning-template     Associate provisioning templates
 add-smart-proxy               Associate a smart proxy
 add-subnet                    Associate a subnet
 add-user                      Associate an user
 configure-cdn                 Update the CDN configuration
 create                        Create organization
 delete                        Delete an organization
 delete-parameter              Delete parameter for an organization
 info                          Show organization
 list                          List all organizations
 remove-compute-resource       Disassociate a compute resource
 remove-domain                 Disassociate a domain
 remove-hostgroup              Disassociate a hostgroup
 remove-location               Disassociate a location
 remove-medium                 Disassociate a medium
 remove-provisioning-template  Disassociate provisioning templates
 remove-smart-proxy            Disassociate a smart proxy
 remove-subnet                 Disassociate a subnet
 remove-user                   Disassociate an user
 set-parameter                 Create or update parameter for an organization
 update                        Update organization

Options:
 -h, --help                    Print help
```

## `hammer organization create`
This subcommand can be executed using the `execute_hammer` tool.
```
$ hammer organization create --help
Usage:
    hammer organization create [OPTIONS]

Options:
 --compute-resource[s|-ids] LIST                Compute resource names/ids
 --description VALUE
 --domain[s|-ids] LIST                          Domain names/ids
 --environment-ids LIST                         Environment ids
 --hostgroup[s|-ids|-titles] LIST               Host group names/titles/ids
 --ignore-types LIST                            List of resources types that will be automatically associated
 --label VALUE
 --location[-id|-title] VALUE/NUMBER            Set the current location context for the request
 --location[s|-ids|-titles] LIST                Associated location names/titles/ids
 --medi[a|um-ids] LIST                          Medium names/ids
 --name VALUE
 --organization[-id|-title|-label] VALUE/NUMBER Set the current organization context for the request
 --partition-table[s|-ids] LIST                 Partition template names/ids
 --provisioning-template[s|-ids] LIST           Provisioning template names/ids
 --realm[s|-ids] LIST                           Realm names/ids
 --smart-prox[ies|y-ids] LIST                   Smart proxy names/ids
 --subnet[s|-ids] LIST                          Subnet names/ids
 --user[s|-ids] LIST                            User logins/ids
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

## `hammer organization delete`
This subcommand can be executed using the `execute_hammer` tool.
```
$ hammer organization delete --help
Usage:
    hammer organization <delete|destroy> [OPTIONS]

Options:
 --async                                        Do not wait for the task
 --id VALUE
 --label VALUE                                  Organization label to search by
 --location[-id|-title] VALUE/NUMBER            Set the current location context for the request
 --name VALUE                                   Set the current organization context for the request
 --organization[-id|-title|-label] VALUE/NUMBER Set the current organization context for the request
 --title VALUE                                  Set the current organization context for the request
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

## `hammer organization info`
This subcommand can be generated using the `generate_hammer_organization_info` resource and can be executed using the `execute_hammer_organization_info` resource. Info by ID or info containing non-default fields requires the use of the `execute_hammer` tool.
```
$ hammer organization info --help
Usage:
    hammer organization <info|show> [OPTIONS]

Options:
 --fields LIST                                  Show specified fields or predefined field sets only. (See below)
 --id VALUE
 --label VALUE                                  Organization label to search by
 --location[-id|-title] VALUE/NUMBER            Set the current location context for the request
 --name VALUE                                   Set the current organization context for the request
 --organization[-id|-title|-label] VALUE/NUMBER Set the current organization context for the request
 --title VALUE                                  Set the current organization context for the request
 -h, --help                                     Print help

Predefined field sets:
  -------------------------------------------------|-----|---------|-----
  FIELDS                                           | ALL | DEFAULT | THIN
  -------------------------------------------------|-----|---------|-----
  Id                                               | x   | x       | x
  Title                                            | x   | x       | x
  Name                                             | x   | x       | x
  Description                                      | x   | x       |
  Parent                                           | x   | x       |
  Users/                                           | x   | x       |
  Smart proxies/                                   | x   | x       |
  Subnets/                                         | x   | x       |
  Compute resources/                               | x   | x       |
  Installation media/                              | x   | x       |
  Templates/                                       | x   | x       |
  Partition tables/                                | x   | x       |
  Domains/                                         | x   | x       |
  Realms/                                          | x   | x       |
  Hostgroups/                                      | x   | x       |
  Parameters/                                      | x   | x       |
  Locations/                                       | x   | x       |
  Created at                                       | x   | x       |
  Updated at                                       | x   | x       |
  Label                                            | x   | x       | x
  Description                                      | x   | x       |
  Service levels                                   | x   | x       |
  Cdn configuration/type                           | x   | x       |
  Cdn configuration/url                            | x   | x       |
  Cdn configuration/upstream organization          | x   | x       |
  Cdn configuration/upstream lifecycle environment | x   | x       |
  Cdn configuration/upstream content view          | x   | x       |
  Cdn configuration/username                       | x   | x       |
  Cdn configuration/ssl ca credential id           | x   | x       |
  -------------------------------------------------|-----|---------|-----

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

## `hammer organization list`
This subcommand can be generated using the `generate_hammer_organization_list` resource and can be executed using the `execute_hammer_organization_list` resource. Passing in parameters requires use of the `execute_hammer` tool.
```
$ hammer organization list --help
Usage:
    hammer organization <list|index> [OPTIONS]

Options:
 --fields LIST                                  Show specified fields or predefined field sets only. (See below)
 --full-result BOOLEAN                          Whether or not to show all results
 --location[-id|-title] VALUE/NUMBER            Set the current location context for the request
 --order VALUE                                  Sort field and order, eg. 'id DESC'
 --organization[-id|-title|-label] VALUE/NUMBER Set the current organization context for the request
 --page NUMBER                                  Page number, starting at 1
 --per-page NUMBER                              Number of results per page to return
 --search VALUE                                 Search string
 --sort-by VALUE                                Field to sort the results on
 --sort-order VALUE                             How to order the sorted results (e.g. ASC for ascending)
 -h, --help                                     Print help

Predefined field sets:
  ------------|-----|---------|-----
  FIELDS      | ALL | DEFAULT | THIN
  ------------|-----|---------|-----
  Id          | x   | x       | x
  Title       | x   | x       | x
  Name        | x   | x       | x
  Description | x   | x       |
  Label       | x   | x       | x
  ------------|-----|---------|-----

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
  description         text
  id                  integer
  label               string
  name                string
  organization_id     integer
  title               string
```

## `hammer organization update`
This subcommand can be executed using the `execute_hammer` tool.
Example: `hammer organization update --name "Old Name" --new-name "New Name"`
```
$ hammer organization update --help
Usage:
    hammer organization update [OPTIONS]

Options:
 --compute-resource[s|-ids] LIST                Compute resource names/ids
 --description VALUE
 --domain[s|-ids] LIST                          Domain names/ids
 --environment-ids LIST                         Environment ids
 --hostgroup[s|-ids|-titles] LIST               Host group names/titles/ids
 --id VALUE
 --ignore-types LIST                            List of resources types that will be automatically associated
 --label VALUE                                  Organization label to search by
 --location[-id|-title] VALUE/NUMBER            Set the current location context for the request
 --location[s|-ids|-titles] LIST                Associated location names/titles/ids
 --medi[a|um-ids] LIST                          Medium names/ids
 --name VALUE
 --new-name VALUE
 --new-title VALUE
 --organization[-id|-title|-label] VALUE/NUMBER Set the current organization context for the request
 --partition-table[s|-ids] LIST                 Partition template names/ids
 --provisioning-template[s|-ids] LIST           Provisioning template names/ids
 --realm[s|-ids] LIST                           Realm names/ids
 --redhat-repository-url VALUE                  Red Hat CDN URL
 --smart-prox[ies|y-ids] LIST                   Smart proxy names/ids
 --subnet[s|-ids] LIST                          Subnet names/ids
 --title VALUE                                  Set the current organization context for the request
 --user[s|-ids] LIST                            User logins/ids
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

## Other Actions
For other organization actions (add-*, remove-*, set-parameter, delete-parameter, configure-cdn, etc.), use the `execute_hammer` tool with the appropriate parameters. You can get help for any specific action by running:
```
hammer organization <action> --help
```
