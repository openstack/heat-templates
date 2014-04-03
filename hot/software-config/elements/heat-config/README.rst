This is an os-refresh-config script which iterates over deployments configuration
data and invokes the appropriate hook for each deployment item. Any outputs returned
by the hook will be signalled back to heat using the configured signalling method.