<%
    dependent_stack = "gus-test-deployment"
%>
stack_type: gcp
name: gus-test-deployment-1
description: Gus test stack 1
project: dev-island
imports:
  - path: examples/stacks/gcp/ox.txt
resources:
- type: compute.v1.instance
  name: gus-test-1
  properties:
    zone: us-west1-a
    machineType: https://www.googleapis.com/compute/v1/projects/dev-island/zones/us-west1-a/machineTypes/f1-micro
    disks:
    - deviceName: boot
      type: PERSISTENT
      boot: true
      autoDelete: true
      initializeParams:
        sourceImage: https://www.googleapis.com/compute/v1/projects/debian-cloud/global/images/debian-8-jessie-v20160301
    networkInterfaces:
    - network: https://www.googleapis.com/compute/v1/projects/dev-island/global/networks/default
      # Access Config required to give the instance a public IP address
      accessConfigs:
      - name: External NAT
        type: ONE_TO_ONE_NAT
outputs:
  - name: instance_id
    value: $(ref.gus-test-1.name)
  - name: ox
    value: !GCPDM {deployment: ${dependent_stack}, output: instance_id, project: dev-island}

