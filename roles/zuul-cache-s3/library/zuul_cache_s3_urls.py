import argparse
import logging
import sys
import os
import boto3
from botocore.exceptions import ClientError

from ansible.module_utils.basic import AnsibleModule


def get_job_artifacts(s3_client, zuul, bucket):
    artifacts = {}

    global_prefix = "{}/global/".format(zuul['project']['canonical_name'])
    global_artifacts_query = s3_client.list_objects(Bucket=bucket,
                                                    Prefix=global_prefix)
    for artifact in global_artifacts_query.get("Contents", []):
        artifacts[os.path.basename(artifact["Key"])] = artifact["Key"]

    buildset_prefix = "{}/{}/".format(
        zuul['project']['canonical_name'],
        zuul['buildset']
    )
    buildset_artifacts_query = s3_client.list_objects(Bucket=bucket,
                                                      Prefix=buildset_prefix)
    for artifact in buildset_artifacts_query.get("Contents", []):
        artifacts[os.path.basename(artifact["Key"])] = artifact["Key"]

    return artifacts


def create_urls(s3_client, zuul, bucket, artifacts, method, expiry,
                endpoint_url=None, aws_access_key_id=None,
                aws_secret_access_key=None):
    urls = dict()
    failures = dict()
    for artifact, location in artifacts.items():
        try:
            if method == "get":
                urls[artifact] = s3_client.generate_presigned_url(
                    'get_object',
                    Params=dict(Bucket=bucket,
                                Key=location),
                    ExpiresIn=expiry
                )
            elif method == "put":
                store = "global" if zuul["post_review"] else zuul["buildset"]
                cache_location = "{}/{}/{}".format(
                    zuul["project"]["canonical_name"],
                    store,
                    artifact)
                urls[artifact] = s3_client.generate_presigned_post(
                    bucket,
                    cache_location,
                    ExpiresIn=expiry
                )
        except ClientError as e:
            logging.exception(e)
            failures[artifact] = "{}".format(e)

    return urls, failures


def run_module(zuul, bucket, artifacts=[], method="get", expiry=None,
               aws_access_key=None, aws_secret_key=None, s3_url=None):
    s3_client = boto3.client('s3',
                             endpoint_url=s3_url,
                             aws_access_key_id=aws_access_key,
                             aws_secret_access_key=aws_secret_key)

    job_artifacts = {}
    if method == "get":
        job_artifacts = get_job_artifacts(s3_client, zuul, bucket)
    elif method == "put":
        job_artifacts = {os.path.basename(artifact): artifact
                         for artifact in artifacts}

    return create_urls(
        s3_client,
        zuul,
        bucket,
        job_artifacts,
        method,
        expiry
    )


def ansible_main():
    module = AnsibleModule(
        argument_spec=dict(
            zuul=dict(type='dict', required=True),
            bucket=dict(type='str', required=True),
            artifacts=dict(type='list', default=[]),
            method=dict(type='str', default='get'),
            expiry=dict(type='int', default=600),
            aws_access_key=dict(type='str'),
            aws_secret_key=dict(type='str', no_log=True),
            s3_url=dict(type='str')
        )
    )

    p = module.params
    urls, failures = run_module(p.get("zuul"),
                                p.get("bucket"),
                                p.get("artifacts"),
                                p.get("method"),
                                p.get("expiry"),
                                p.get("aws_access_key"),
                                p.get("aws_secret_key"),
                                p.get("s3_url"))

    if failures:
        module.fail_json(changed=True,
                         urls=urls,
                         failures=failures)

    module.exit_json(changed=True,
                     urls=urls,
                     failures=failures)


def cli_main():
    parser = argparse.ArgumentParser(
        description="Prepare urls to download artifacts from s3"
    )
    parser.add_argument(
        'project',
        help="Project name"
    )
    parser.add_argument(
        'buildset',
        help="Buildset Id"
    )
    parser.add_argument(
        'bucket',
        help="Bucket name"
    )
    parser.add_argument(
        '--post-review', action='store_true',
    )
    parser.add_argument(
        '--artifacts', nargs='+',
        help='Artifacts to prepare urls for'
    )
    parser.add_argument(
        '--method', default="get",
        help='Method the urls should be used for. "get" or "put"'
    )
    parser.add_argument(
        '--expiry', default=600,
        help='Time limit in seconds for the URL generated.'
    )
    parser.add_argument(
        '--aws-access-key',
        help='Access key id'
    )
    parser.add_argument(
        '--aws-secret-key',
        help='Secret access key'
    )
    parser.add_argument(
        '--s3-url',
        help='Endpoint url of s3 service'
    )
    args = parser.parse_args()
    zuul = dict(
        project=dict(canonical_name=args.project),
        buildset=args.buildset,
        post_review=args.post_review
    )
    urls, failures = run_module(zuul,
                                args.bucket,
                                args.artifacts,
                                args.method,
                                args.expiry,
                                args.aws_access_key,
                                args.aws_secret_key,
                                args.s3_url)
    print(failures)
    print(urls)


if __name__ == '__main__':
    if sys.stdin.isatty():
        cli_main()
    else:
        ansible_main()
