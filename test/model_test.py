import unittest

from pycolonies import File, Reference, S3Object


class TestModel(unittest.TestCase):
    def test_file_ensures_single_slash(self) -> None:
        object = S3Object(server="server", port=123, tls=False, accesskey="key", secretkey="secret",
                          region="region", encryptionkey="enckey", encryptionalg="alg", object="object", bucket="bucket")

        reference = Reference(protocol="proto", s3object=object)

        file_with_auto_appended_slash = File(fileid="id", colonyname="testcolony", label="filelabel",
                    name="filename", size=100, sequencenr=1, checksum="cheksum", checksumalg="alg", ref=reference, added=None)
        
        assert "/filelabel" == file_with_auto_appended_slash.label

        file_with_single_leading_slash = file_with_auto_appended_slash = File(fileid="id", colonyname="testcolony", label="///filelabel",
                    name="filename", size=100, sequencenr=1, checksum="cheksum", checksumalg="alg", ref=reference, added=None)

        assert "/filelabel" == file_with_single_leading_slash.label
