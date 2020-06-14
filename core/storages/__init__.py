import os

from google.cloud import storage

from utils import Utils


class Storage:

    RESULTS_DIR = "results"

    def __init__(self):
        if Utils.is_gcp():
            self.client = storage.Client(project=os.environ["GCP_PROJECT_ID"])
            self.bucket = self.client.get_bucket(os.environ["BUCKET_NAME"])

    def store(self, uuid, data):
        if Utils.is_gcp():
            blob = self.bucket.blob(self._get_key_from_uuid(uuid))
            blob.upload_from_string(data)
        return

    def load(self, uuid):
        if Utils.is_gcp():
            blob = self.bucket.get_blob(self._get_key_from_uuid(uuid))
            if blob is None:
                return {}
            return blob.download_as_string().decode("utf-8")
        else:
            return "__report__"

    def delete(self, directory):
        if Utils.is_gcp():
            prefix = "{}/{}/".format(self.RESULTS_DIR, directory[0:24])
            self.bucket.delete_blobs(blobs=self.bucket.list_blobs(prefix=prefix))
        return

    def _get_key_from_uuid(self, uuid):
        return "{}/{}/{}".format(self.RESULTS_DIR, uuid[0:24], uuid[24:])
