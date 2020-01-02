import os

import boto3


def upload_s3(uploads):

    s3bucket = os.getenv("S3_BUCKET")

    response = {}
    for upload in uploads:
        s3key = "%s" % upload["filename"]
        print("Upload image to: %s/%s" % (s3bucket, s3key))

        s3 = boto3.resource("s3").Object(s3bucket, s3key)
        put = s3.put(Body=upload["image"])
        print("Upload result: %s" % put)

        url = boto3.client("s3").generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": s3bucket, "Key": s3key},
            ExpiresIn=3600,
            HttpMethod="GET",
        )

        result = {
            "bucket": s3bucket,
            "key": s3key,
            "url": url,
        }
        response[upload["type"]] = result

    return response
