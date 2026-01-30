# Wolfi-OS extra packages repository

This repository contains additional packages for [Wolfi-OS](https://wolfi.dev/), a Linux distribution focused on security, simplicity, and reproducibility.
These packages are not part of the core Wolfi-OS distribution, our focus is to provide a community-driven APK repository alternative with focus on PHP at this time.

> Why an alternative repository? See more at [Wolfi OSS commitment](https://github.com/orgs/wolfi-dev/discussions/77550).

> You can see the current list of packages supported by this repository in the root directory.

## Installation of repository

### with Dockerfile

```dockerfile
FROM cgr.dev/chainguard/wolfi-base

RUN sed -i '1i @glimmerlabs https://wolfi.glimmerlabs.dev' /etc/apk/repositories && \
cat <<EOF > /etc/apk/keys/glimmer-labs-signing.rsa.pub
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAujhU1omCi+9hmLm2bL0r
tF0MPTdQ1EDiv+8xspYPQV05ZzVe8O0UBEzc+zEY72AQ7pa/yY1gVCniWKom1rLJ
Z+aJdHvPkOf2aNaA1S7e/WGiYj1sPSKdnCy+qvHDWxhyXcvgIzHvy+7i6Mdab3cO
CIVZPDKSUbLlB/CCD/CX1qoZ25/uDNsH/L8k/pWQg7mShoFu3fJRT2qkXnPN7BJU
lgCm5HH1esBoLr7TdcfgbFrD0XYkr0hZTqrnISZqCpxDzMHMNTL6B+T8PcEMsbQP
r1qWi20hsq561rZQTWdugQ8LWFZ03fhLkESYcmYKNlhWYA81aKMzGXBi6144gHrT
TwIDAQAB
-----END PUBLIC KEY-----
EOF
```

### with apko

```diff
contents:
  keyring:
+   - https://wolfi.glimmerlabs.dev/glimmer-labs-signing.rsa.pub
    - https://packages.wolfi.dev/os/wolfi-signing.rsa.pub
  repositories:
+   - https://wolfi.glimmerlabs.dev
    - https://packages.wolfi.dev/os
  packages:
    - wolfi-base
```
