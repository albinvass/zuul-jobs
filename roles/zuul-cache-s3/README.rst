Zuul Cache backend for S3

**Role Variables**

.. zuul:rolevar:: zuul_cache
   :type: dict

   Complex argument which contains information on how to upload and configure the cache.
   It is expected that this argument comes from a `Secret`.

   .. zuul:rolevar:: bucket

      S3 bucket to store artifacts in.

   .. zuul:rolevar:: url_expiry
      :default: true

      How long in seconds the presigned urls should be valid for.

   .. zuul:rolevar:: access_key

      Access key to use for s3.

   .. zuul:rolevar:: secret_key

      Secret key to use for s3.

   .. zuul:rolevar:: url

      S3 URL endpoint.
      If not given the role defaults to AWS.
