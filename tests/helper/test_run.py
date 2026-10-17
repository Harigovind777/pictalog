from pictalog_helper.run import run_once


class FakeClient:
    def __init__(self, job=None, file=b""):
        self.job = job
        self.file = file
        self.sent: list[tuple] = []

    def claim(self):
        return self.job

    def download(self, job_id):
        self.sent.append(("download", job_id))
        return self.file

    def send_image(self, job_id, png):
        self.sent.append(("image", job_id, png))

    def send_items(self, job_id, items):
        self.sent.append(("items", job_id, items))

    def fail(self, job_id, error):
        self.sent.append(("fail", job_id, error))


class FakeEngine:
    name = "fake"

    def __init__(self, error=None):
        self.error = error
        self.calls = []

    def generate(self, prompt, seed):
        self.calls.append((prompt, seed))
        if self.error:
            raise self.error
        return b"PNGDATA"


class FakeReader:
    def __init__(self):
        self.calls = []

    def read(self, text, file, filename):
        self.calls.append((text, file, filename))
        return [{"name": "Oak table"}]


def test_run_once_no_job_returns_false():
    assert run_once(FakeClient(None), FakeEngine(), FakeReader()) is False


def test_run_once_image_job():
    client, engine = FakeClient({"id": 1, "kind": "image", "payload": {"prompt": "tee", "seed": 9}}), FakeEngine()
    assert run_once(client, engine, FakeReader()) is True
    assert engine.calls == [("tee", 9)]
    assert client.sent == [("image", 1, b"PNGDATA")]


def test_run_once_extract_job_with_text():
    job = {"id": 2, "kind": "extract", "payload": {"text": "Oak table 25,000", "filename": "a.docx", "import_id": 4}}
    client, reader = FakeClient(job), FakeReader()
    run_once(client, FakeEngine(), reader)
    assert reader.calls == [("Oak table 25,000", None, "a.docx")]
    assert client.sent == [("items", 2, [{"name": "Oak table"}])]


def test_run_once_extract_downloads_file_when_no_text():
    job = {"id": 3, "kind": "extract", "payload": {"text": None, "filename": "list.jpg", "import_id": 4}}
    client, reader = FakeClient(job, file=b"JPEG"), FakeReader()
    run_once(client, FakeEngine(), reader)
    assert reader.calls == [(None, b"JPEG", "list.jpg")]
    assert client.sent[0] == ("download", 3)


def test_run_once_reports_failure():
    client = FakeClient({"id": 4, "kind": "image", "payload": {"prompt": "tee", "seed": 1}})
    assert run_once(client, FakeEngine(error=RuntimeError("out of memory")), FakeReader()) is True
    assert client.sent == [("fail", 4, "out of memory")]
