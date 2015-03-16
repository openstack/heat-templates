Adds the fedora and selinux-permissive elements.

selinux-permissive is added to avoid a relabel during boot, which is very
slow in a gate environment.