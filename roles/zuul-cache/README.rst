Cache artifacts in a configured backend.

This role enables repositories to cache built dependencies between
builds to speed up jobs and makes it easy to pass artifacts between
jobs with a configured backend.

Cached items are separate for each repository but could be made
accessible to other jobs with ``zuul.artifacts``.

To allow pushing and pulling artifacts from an object storage without exposing
credentials to an untrusted context the ``zuul-cache`` uses four separate stages
to prepare and update artifacts:

``prepare``
    prepares artifacts to be accessible by the job.
``pull``
    pulls an artifact from the cache.
``push``
    stages the artifact to be cached.
``update``
    updates cache with staged artifacts.

With ``prepare`` Zuul prepares a list of artifacts so they are accessible in an
untrusted context. This can either happen by putting the artifacts in a local cache
on the node or generating temporary tokens that gives direct access to the artifact
in the backend. ``pull`` is used in the untrusted context to retreive the prepared
artifacts so they can be used in the build. ``push`` stages an artifact to be cached
in a trusted context with ``update``. For security reason it is a good idea to only run
the ``update`` stage in a post-review pipeline.

**Role Variables**

.. zuul:rolevar:: zuul_cache_mode
   :type: string

   Used to control whether to push, pull, prepare or update the artifact.

.. zuul:rolevar:: zuul_cache_dir
   :type: string
   :default: {{ ansible_user_dir }}/zuul-cache

   If the backend needs to prepare artifacts local cache this
   configures where the role should operate.

.. zuul:rolevar:: zuul_cache_name
   :type: string

   Name of the artifact to pull from or push to the prepared cache.

.. zuul:rolevar:: zuul_cache_src
   :type: string

   File or directory to store as an artifact when used with `push`.

.. zuul:rolevar:: zuul_cache_dest
   :type: string

   Path to a directory where to the artifact should be unarchived to
   when used with `pull`.

.. zuul:rolevar:: zuul_cache
   :type: dict

   Complex argument which contains information on how to upload and configure the cache.
   It is expected that this argument comes from a `Secret`. See backend specific documentation
   for further fields that can be set.

   .. zuul:rolevar:: backend
      :type: string

      Backend that should be used to store artifacts.

      Available backends are:

      - s3
