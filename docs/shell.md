# Shell Stacks

Shell stacks exist to fill the gaps where the *declarative* approach won't suffice:

* Orchestrating deployments in multiple cloud provides
* Managing resources not yet available in the provider's resource manager
* Running non cloud specific commands, for example setting up a dev environment

These shell stacks work by providing commands and environment variables for 
each specific action (Create/Delete/Update)

To use Shell Stacks:

* Set "StackType" to "Shell" (if not defined, it assumes Cloudformation type)
* Set which shell to use (defaults to /bin/bash)
* Define the Environment variables which will be used by all Actions
* Define what "Actions" the stack supports (Create/Update/Delete)
    * Define action-specific Environment variables
    * Specify what commands to execute for each action

## Notes

* At least one *Action* must be specified, but no need to define them all
* The environment variables are merged from least to most specific:
    * "Commands" in a shell stack will inherit any predefined environment 
      variables, which is handy when using variables such as AWS_DEFAULT_PROFILE,
      AWS_ACCESS_KEY, etc.
    * The stack-wide enviroment variables do override the predefined ones from
      the environment.
    * The action-specific environment variables always win.
* If "Commands" is a *list* instead of a *string*, no shell is used (so no fancy shell expansions)
* Multiple commands can be specified by using a multiline string in YAML (see example below)
* The extra YAML tags provided by this tools are also available to shell stacks

## Example - Shell Stacks

```
## This stack creates a KMS alias and associates it with an existing key.
## It also deletes the alias.
<%
    role = "myrole"
%>

StackType: Shell
Shell: /bin/bash
Environment:
  AWS_DEFAULT_REGION: us-west-2
  KMS_KEY: !Cloudformation {stack: my-kms-stack, output: ApplicationKey}
Actions:
  Create:
    Environment:
      KMS_KEY: !Cloudformation {stack: kms-stack, output: key_arn}
    Commands: |
      echo creating KMS Alias
      aws kms list-aliases --query "Aliases[*].[AliasName]" --output text | grep "alias/${role}" || aws kms create-alias --alias-name alias/${role} --target-key-id $KMS_KEY
  Delete:
    Commands: |
      aws kms list-aliases --query "Aliases[*].[AliasName]" --output text | grep "alias/${role}" && aws kms delete-alias --alias-name alias/${role}
```
