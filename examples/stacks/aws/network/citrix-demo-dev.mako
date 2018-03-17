StackType: Shell
Shell: /bin/bash
Environment:
  WEBSITE: jira.dev.demo.com
Actions:
  Create:
    Commands: |
      echo "Configuring $WEBSITE on Citrix load balancer"...
  Delete:
    Commands: |
      echo "De-configuring $WEBSITE on Citrix load balancer"...
