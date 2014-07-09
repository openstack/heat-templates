testsls:
  pkg.installed:
    {% if grains['os_family'] == 'RedHat' %}
    - name: {{ pillar['master']['pkg-redhat'] }}
    {% elif grains['os_family'] == 'Debian' %}
    - name: {{ pillar['master']['pkg-apache'] }}
    {% endif %}