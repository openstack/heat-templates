This hook uses 'docker-py' library to deploy containers for a container-manifest(POD)
embeded inside software-config 'config' property.

Container manifest uses standard google container manifest schema[1].

WARNING: This is an experimental implementation.

Config 'inputs' and 'outputs' are ignored.

All container ports are bound to specific host ports specified in the manifest.
if a 'hostPort' is not specified, 'containerPort' is used as the 'hostPort'.
This may result in port conflict. IP-PER-POD model is a possible enhancement.

Sample Container Manifest
-------------------------
.. line-block::

    version: v1beta2      // Required.
    containers:           // Required.
      - name: string      // Required.
        image: string     // Required.
        command: [string]
        workingDir: string
        volumeMounts:
          - name: string
            mountPath: string
            readOnly: boolean
        ports:
          - name: string
            containerPort: int
            hostPort: int
            protocol: string
        env:
          - name: string
            value: string
    restartPolicy:
      - string: {}
    volumes:
      - name: string
        source: emptyDir | HostDir
          emptyDir: {}
          hostDir:
            path: string

[1]https://cloud.google.com/compute/docs/containers/container_vms.